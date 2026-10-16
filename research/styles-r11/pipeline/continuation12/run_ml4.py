"""Registered queued historical-exchange generation and predictive analysis."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gc
import gzip
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-12'
EXPERIMENT = 'ML4-HISTORICAL-EXCHANGE'
H = M = P = T = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value, replace=False):
    path = Path(path)
    need(replace or not path.exists(), 'immutable artifact: ' + str(path))
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, compresslevel=5, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    if replace:
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_bytes(raw)
        os.replace(temporary, path)
    else:
        path.write_bytes(raw)
    return dict(path=str(path.relative_to(PKG)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def worker(spec):
    if spec['phase_kind'] == 'data_controls':
        return H.controls(spec['seed'])
    if spec['phase_kind'] == 'generation':
        return H.generate(spec)
    if spec['phase_kind'] == 'model_controls':
        return M.controls(spec['seed'])
    if spec['phase_kind'] == 'model':
        return M.task(spec)
    raise ValueError('unknown phase kind: ' + repr(spec))


def main():
    global H, M, P, T
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--implementation-pins-sha256', required=True)
    parser.add_argument('--attempt', default='v1')
    args = parser.parse_args()
    need(sys.flags.isolated and not sys.flags.optimize, 'Python -I with assertions enabled')
    need(sys.pycache_prefix and not Path(sys.pycache_prefix).exists(), 'fresh unused bytecode namespace')
    preg = ROUND / 'ML4/PREREGISTRATION.json'
    protocol = json.loads(preg.read_text())
    need(sha(preg) == args.registration_sha256 and protocol['state'] == 'FROZEN', 'frozen preregistration')
    pin_path = ROUND / 'ML4' / ('IMPLEMENTATION-PINS-' + args.attempt + '.json')
    need(sha(pin_path) == args.implementation_pins_sha256, 'frozen implementation manifest')
    pins = json.loads(pin_path.read_text())
    required = [HERE / name for name in ('run_ml4.py', 'historical_exchange.py', 'exchange_ml.py', 'telemetry.py')]
    required += [HERE.parent / 'pool.py']
    need(all(str(path.relative_to(ROOT)) in pins['sha256'] for path in required),
         'runner, data, model, telemetry, and common pool sources all frozen')
    for relative, digest in pins['sha256'].items():
        need(sha(ROOT / relative) == digest, 'implementation pin before import: ' + relative)
        archive = PKG / pins['archives'][digest]['path']
        need(hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest,
             'source archive before import: ' + relative)
    need(str(Path(__file__).relative_to(ROOT)) in pins['sha256'], 'runner frozen')
    for reference in protocol['inputs'].values():
        need(sha(PKG / reference['path']) == reference['sha256'], 'registered input: ' + reference['path'])
    sys.path[:0] = [str(HERE), str(HERE.parent)]
    import historical_exchange as H
    import exchange_ml as M
    import pool as P
    import telemetry as T
    need(H.PROTOCOL == protocol['data_protocol'], 'implementation matches exact dataset registration')
    need(M.PROTOCOL == protocol['model_protocol'], 'implementation matches exact model registration')
    seeds = protocol['seeds']
    resources = protocol['resources']
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(item for item in registry['experiments'] if item['id'] == EXPERIMENT)
    need(registry['no_active_experiments'], 'no concurrent scientific pool')
    need(row['status'] == 'planned' or row.get('execution') == 'INCOMPLETE', 'new or explicitly repaired attempt')
    run = ROUND / EXPERIMENT / args.attempt
    data = PKG / 'data/continuation-12' / ('ml4-' + args.attempt)
    run.mkdir(parents=True, exist_ok=False)
    data.mkdir(parents=True, exist_ok=False)
    # Attempt-specific output location only; scientific settings remain those
    # authenticated in the preregistration above.
    protocol['_runtime_data_path'] = str(data.relative_to(PKG))
    row.update(status='running', execution='RUNNING', started_utc=now())
    registry['no_active_experiments'] = False
    write(registry_path, registry, replace=True)
    c0, w0 = cpu(), time.monotonic()
    previous_cpu = sum(item.get('cpu_seconds', 0) for item in registry['experiments'])
    observed, prepared, phase_metrics = {}, {}, {}
    failure, phase = None, 'preparation'
    confirmed = False
    status = 'EXPLORATORY'
    analysis = {}
    historical_attribution = None
    telemetry_errors = []
    monitor = T.Monitor(data / 'RESOURCE-TRACE.jsonl', P.worker_count())

    def monitor_call(method, *values):
        try:
            return getattr(monitor, method)(*values)
        except Exception as error:
            telemetry_errors.append(dict(utc=now(), method=method, error=repr(error)))
            return None

    monitor_call('start')
    original = json.loads((PKG / 'data/words/PINS.json').read_text())['files']
    attribution = [dict(path=path, **value) for path, value in original.items()]

    def deadline():
        if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered science launch cutoff reached')
        remaining = min(resources['cpu_budget_seconds_family'] - (cpu() - c0),
                        resources['round_cpu_budget_seconds'] - previous_cpu - (cpu() - c0))
        if remaining <= 0:
            raise TimeoutError('registered CPU budget reached')
        return remaining

    def storage():
        checks = [(ROUND, resources['new_result_bytes_cap']),
                  (PKG / 'data/continuation-12', resources['new_data_bytes_cap']),
                  (PKG / 'results', resources['result_bytes_cap'])]
        for directory, cap in checks:
            total = sum(path.stat().st_size for path in directory.rglob('*') if path.is_file())
            need(total < cap, 'storage cap: %s uses %d of %d' % (directory, total, cap))

    def launch(name, specs, rss_gib=4, working_set_gib=0.8):
        nonlocal phase
        phase = name
        specs = list(specs)
        remaining = deadline()
        storage()
        write(data / (name.upper() + '-TASKS.json.gz'), specs)
        observed[name] = []
        monitor_call('set_phase', name, len(specs))
        pc, pw = cpu(), time.monotonic()
        print(json.dumps(dict(event='launch', phase=name, tasks=len(specs), workers=P.worker_count(),
                              remaining_cpu_seconds=remaining, utc=now())), flush=True)

        def checkpoint(index, item):
            reference = write(data / name / ('task-%05d.json.gz' % index), item)
            result = item.get('result')
            if name == 'generation' and isinstance(result, dict):
                # Save the complete result first. The common pool retains each
                # returned object, so compact it in place after checkpointing.
                result = {key: value for key, value in result.items()
                          if key not in ('rows', 'records', 'features', 'pairs')}
                item['result'] = result
            record = dict(index=index, spec=specs[index], **reference,
                          status=item['status'], cpu_seconds=item.get('cpu_seconds'),
                          wall_seconds=item.get('seconds'), peak_rss_bytes=item.get('peak_rss_bytes'),
                          summary=result, error=item.get('error'))
            observed[name].append(record)
            monitor_call('progress', len(observed[name]))
            if len(observed[name]) % 61 == 0 or len(observed[name]) == len(specs) or len(specs) < 10:
                write(data / 'QUEUE-CHECKPOINT.json', dict(utc=now(), phase=name,
                      completed=len(observed[name]), total=len(specs),
                      completed_by_phase={key: len(value) for key, value in observed.items()},
                      parent_and_reaped_cpu_seconds=cpu() - c0), replace=True)
                print(json.dumps(dict(phase=name, completed=len(observed[name]), total=len(specs),
                                      status=item['status'], utc=now())), flush=True)
            # Stop the common pool before it submits replacement work after
            # the registered launch cutoff. Completed evidence is saved first.
            if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
                raise TimeoutError('registered science launch cutoff reached during queue')

        P.run_pool(worker, [(spec,) for spec in specs], workers=P.worker_count(), timeout=300,
                   rss_gib=rss_gib, working_set_gib=working_set_gib,
                   projection_path=data / (name.upper() + '-MEMORY-PROJECTION.json'),
                   on_result=checkpoint, cpu_budget_seconds=remaining)
        observed[name].sort(key=lambda item: item['index'])
        phase_metrics[name] = dict(tasks=len(specs), cpu_seconds=cpu() - pc,
                                  wall_seconds=time.monotonic() - pw)
        phase_metrics[name]['average_core_equivalents'] = (
            phase_metrics[name]['cpu_seconds'] / phase_metrics[name]['wall_seconds'])
        write(data / (name.upper() + '-MANIFEST.json.gz'), observed[name])
        bad = [item for item in observed[name] if item['status'] != 'OK']
        if any(item['status'] == 'TIMEOUT' for item in bad):
            raise TimeoutError(name + ': task deadline exceeded')
        need(not bad, name + ': failed tasks ' + repr(bad[:3])[:10000])
        storage()
        return observed[name]

    try:
        deadline()
        write(data / 'ENVIRONMENT.json', dict(utc=now(), argv=sys.argv, python=sys.version,
              python_executable=sys.executable, platform=platform.platform(),
              dependencies={name: importlib.metadata.version(name) for name in ('numpy', 'scipy', 'mpmath', 'networkx')},
              affinity_cores=len(os.sched_getaffinity(0)), allocated_cores=128,
              configured_workers=P.worker_count(), ram_gib=P.memory_gib(),
              threads={key: os.environ[key] for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS',
                      'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS')}))
        write(data / 'PREPARATION-MEMORY-PROJECTION.json',
              P.project_memory(P.worker_count(), 6, resources['generation_working_set_gib']))
        monitor_call('set_phase', 'data_preparation', 0)
        prepared['data'] = H.prepare(protocol)
        historical_attribution = write(data / 'SOURCE-ATTRIBUTION.json', prepared['data']['provenance'])
        write(data / 'DATA-PREPARATION.json', prepared['data'])
        checks = launch('data_controls', [dict(phase_kind='data_controls', seed=seed) for seed in seeds],
                        rss_gib=6, working_set_gib=resources['generation_working_set_gib'])
        need(all(item['summary']['status'] == 'PASS' for item in checks), 'data controls must pass')
        specs = [dict(spec, phase_kind='generation') for seed in seeds
                 for spec in H.generation_specs(seed, 0)]
        generated = launch('generation', specs, rss_gib=6,
                           working_set_gib=resources['generation_working_set_gib'])
        prepared['generation'] = H.summarize_generation(generated)
        need(prepared['generation']['confirmed'], 'two-seed exact corpus agreement')
        write(data / 'GENERATION-SUMMARY.json', prepared['generation'])
        H.release_generation_state()
        gc.collect()
        deadline()
        monitor_call('set_phase', 'model_preparation', 0)
        first_seed = [item for item in generated if item['spec']['seed'] == seeds[0]]
        model_estimate = M.estimate_preparation(first_seed)
        parent = T._process(os.getpid())
        memory = T.memory()
        need(parent is not None, 'parent RSS available for model preparation projection')
        model_estimate.update(parent_current_rss_bytes=parent['rss_bytes'],
                              available_memory_bytes=memory['MemAvailable_bytes'],
                              projected_parent_peak_bytes=parent['rss_bytes'] +
                              model_estimate['predicted_transient_upper_bound_bytes'])
        write(data / 'MODEL-ARRAY-MEMORY-PROJECTION.json', model_estimate)
        need(model_estimate['predicted_transient_upper_bound_bytes'] < memory['MemAvailable_bytes'],
             'projected model preparation fits currently available memory')
        write(data / 'MODEL-PREPARATION-MEMORY-PROJECTION.json',
              P.project_memory(P.worker_count(), 4, resources['model_working_set_gib']))
        prepared['model'] = M.prepare(first_seed, protocol)
        write(data / 'MODEL-PREPARATION.json', prepared['model'])
        checks = launch('model_controls', [dict(phase_kind='model_controls', seed=seed) for seed in seeds],
                        working_set_gib=resources['model_working_set_gib'])
        need(all(item['summary']['status'] == 'PASS' for item in checks), 'model controls must pass')
        for name, method in [('observed', M.observed_specs), ('learning_curves', M.learning_curve_specs),
                             ('benchmark', M.benchmark_specs)]:
            launch(name, [dict(spec, phase_kind='model') for seed in seeds for spec in method(seed)],
                   working_set_gib=resources['model_working_set_gib'])
        launch('permutations', [dict(spec, phase_kind='model') for seed in seeds
               for spec in M.permutation_specs(seed, protocol['n_permutations'])],
               working_set_gib=resources['model_working_set_gib'])
        analysis = M.summarize(observed, protocol)
        confirmed = analysis['confirmed']
        need(confirmed, 'registered two-seed decision must agree')
        write(data / 'ANALYSIS.json', analysis)
        phase = None
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error),
                       traceback=traceback.format_exc()[-18000:])
        status = 'TIMEOUT' if isinstance(error, (TimeoutError, P.PoolCpuBudgetExceeded)) else 'ERROR'
    telemetry = monitor_call('stop') or {}
    telemetry['errors'] = telemetry_errors
    elapsedc, elapsedw = cpu() - c0, time.monotonic() - w0
    saved = [item for items in observed.values() for item in items]
    manifest_ref = write(data / 'ALL-TASKS.json.gz', saved)
    overhead = max(0, elapsedc - sum(item.get('cpu_seconds') or 0 for item in saved))
    stats = dict(status=status, confirmed=confirmed and failure is None,
                 total_cpu_seconds=elapsedc, total_wall_seconds=elapsedw,
                 average_core_equivalents=elapsedc / elapsedw,
                 configured_workers=P.worker_count(), telemetry=telemetry,
                 phases=phase_metrics, completed_by_phase={key: len(value) for key, value in observed.items()},
                 preparation=prepared, analysis=analysis, failure=failure, incomplete_phase=phase)
    complete_ref = write(data / 'RUN.json', stats)
    result_refs = []
    for position, seed in enumerate(seeds):
        mine = [item for item in saved if item['spec']['seed'] == seed]
        result_refs.append(write(run / ('seed-' + str(seed)) / 'RESULT.json', dict(
            schema_version=1, experiment=EXPERIMENT, milestone='CONTINUATION-12/ML4', seed=seed,
            status=status, confirmed=confirmed and failure is None, recorded_utc=now(),
            preregistration_sha256=sha(preg), implementation_pins=dict(path=str(pin_path.relative_to(PKG)), sha256=sha(pin_path)),
            script_sha256=sha(Path(__file__)), inputs=protocol['inputs'], source_attribution=attribution,
            release_source_attribution=dict(complete_provenance=historical_attribution,
                authors_and_lineage=protocol['attribution']),
            word_blob_ids={item['path']: item.get('git_blob') for item in attribution},
            n_permutations=sum(item['spec'].get('kind') == 'permutation' for item in mine),
            cpu_seconds=sum(item.get('cpu_seconds') or 0 for item in mine) + (overhead if position == 0 else 0),
            wall_seconds=elapsedw, peak_rss_bytes=max((item.get('peak_rss_bytes') or 0 for item in mine), default=0),
            task_manifest=manifest_ref, complete_run=complete_ref, failure=failure, incomplete_phase=phase,
            decision=analysis.get('seeds', {}).get(str(seed)), scope=protocol['scope'],
            pattern_claim=False, kappa_claim=False)))
    attempts = row.get('attempts', []) + [dict(attempt=args.attempt, status=status,
        cpu_seconds=elapsedc, wall_seconds=elapsedw, result_files=[item['path'] for item in result_refs])]
    row.update(status=status, execution='COMPLETED' if failure is None else 'INCOMPLETE',
               confirmed=confirmed and failure is None, attempts=attempts,
               cpu_seconds=sum(item['cpu_seconds'] for item in attempts),
               wall_seconds=sum(item['wall_seconds'] for item in attempts),
               result_files=[item['path'] for item in result_refs], updated_utc=now())
    registry['no_active_experiments'] = True
    write(registry_path, registry, replace=True)
    write(run / 'RUN.json', dict(status=status, confirmed=confirmed and failure is None,
          total_cpu_seconds=elapsedc, total_wall_seconds=elapsedw,
          average_core_equivalents=elapsedc / elapsedw, telemetry=telemetry,
          phases=phase_metrics, failure=failure, complete_run=complete_ref, results=result_refs))
    storage()
    print(json.dumps(dict(event='complete', status=status, confirmed=confirmed,
                          cpu_seconds=elapsedc, wall_seconds=elapsedw,
                          average_core_equivalents=elapsedc / elapsedw, failure=failure)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
