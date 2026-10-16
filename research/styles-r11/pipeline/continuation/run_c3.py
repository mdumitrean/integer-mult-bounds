"""C3 controls, 168 exhaustive shards, then canonical reducers via pool.py."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import os
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent)]
import records as R
import pool
import cross_call as F

ROUND = R.RESULTS / 'CONTINUATION-01'
EXPERIMENT = 'C3-CROSS-CALL-EXCHANGE'
PREG = ROUND / 'C3/PREREGISTRATION.json'
PREG_SHA = 'a1cd103e2eb2dd1043238533bd4fb8eb2b4e4b7dfac26acaa81ede11eca1d38c'
SEEDS = (11031, 29063)
BUDGET = 7200


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def source_snapshot(directory):
    paths = set((R.PKG / 'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        path = getattr(module, '__file__', None)
        if path:
            path = Path(path).resolve()
            if path.is_relative_to(R.ROOT / 'research') and path.suffix == '.py':
                paths.add(path)
    result = {}
    for path in sorted(paths):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        result[str(path.relative_to(R.ROOT))] = digest
        archive = directory / (digest + '.py.gz')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            archive.write_bytes(gzip.compress(raw, mtime=0))
    return result


def immutable_gzip(path, value):
    raw = gzip.compress((json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode(), mtime=0)
    if path.exists():
        raise FileExistsError('immutable shard receipt already exists: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def control(seed):
    return F.controls_task(seed)


def block(seed, block_id):
    return F.c3_block_task(seed, block_id, max_seconds=240)


def finish(seed, block_results, directory, controls_result):
    return F.finish_task(seed, block_results, directory, controls_result)


def main():
    protocol = json.loads(PREG.read_text())
    if R.sha256(PREG) != PREG_SHA or protocol['state'] != 'FROZEN' or tuple(protocol['seeds']) != SEEDS:
        raise ValueError('frozen family and seed binding')
    if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['hard_stop_utc']):
        raise RuntimeError('hard stop reached')
    run = ROUND / EXPERIMENT / 'v1'
    if run.exists():
        raise FileExistsError('immutable attempt already exists: ' + str(run))
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(row for row in registry['experiments'] if row['id'] == EXPERIMENT)
    previous = next(row for row in registry['experiments'] if row['id'] == 'C2-LATEST-SAME-CALL')
    if row['status'] != 'planned' or previous['status'] != 'NULL' or not previous['confirmed']:
        raise ValueError('planned C3 after confirmed C2 NULL required')
    run.mkdir(parents=True)
    for seed in SEEDS:
        (run / ('seed-' + str(seed))).mkdir()
    row.update(status='running', started_utc=R.utcnow())
    R.write_json(registry_path, registry)
    c0, w0 = cpu(), time.monotonic()
    observed = {'controls': {}, 'blocks': {}, 'finish': {}}
    failure, prepared, manifest, failed_phase = None, None, {}, None
    phase_specs = {}

    def remaining():
        value = BUDGET - (cpu() - c0)
        if value <= 0:
            raise pool.PoolCpuBudgetExceeded('cumulative C3 family CPU budget exhausted')
        if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['hard_stop_utc']):
            raise TimeoutError('registered wall-clock hard stop reached')
        return value

    def launch(phase, fn, args):
        nonlocal failed_phase
        failed_phase = phase
        phase_specs[phase] = args
        def checkpoint(index, item):
            observed[phase][index] = item
            seed = args[index][0]
            directory = run / ('seed-' + str(seed))
            if phase == 'blocks':
                path = directory / 'blocks' / ('block-%03d.json.gz' % args[index][1])
                immutable_gzip(path, item)
            else:
                path = directory / (phase.upper() + '-POOL.json')
                R.write_json(path, item, immutable=True)
            completed_cpu = sum(v.get('cpu_seconds') or 0 for values in observed.values() for v in values.values())
            R.write_json(run / 'BUDGET-CHECKPOINT.json', dict(phase=phase, updated_utc=R.utcnow(),
                family_budget_seconds=BUDGET, completed_task_cpu_seconds=completed_cpu,
                parent_and_reaped_cpu_seconds=cpu()-c0,
                note='pool.py separately enforces the budget including live worker CPU; this checkpoint records completed work.',
                completed_by_phase={key: len(value) for key, value in observed.items()}))
            if phase != 'blocks' or (len(observed[phase]) % 8 == 0) or len(observed[phase]) == len(args):
                print(json.dumps(dict(phase=phase, completed=len(observed[phase]), expected=len(args),
                                      pool_status=item['status'], result_status=item.get('result', {}).get('status'),
                                      completed_task_cpu_seconds=completed_cpu)), flush=True)
        values = pool.run_pool(fn, args, workers=pool.worker_count(), timeout=300, rss_gib=6,
            working_set_gib=0.5 if phase == 'blocks' else 1,
            projection_path=run / ('MEMORY-PROJECTION-' + phase.upper() + '.json'),
            on_result=checkpoint, cpu_budget_seconds=remaining())
        return values

    try:
        prepared = F.prepare(pr=2917)
        attribution = R.provenance() + F.provenance()['source_attribution']
        manifest = source_snapshot(ROUND / 'SOURCES')
        R.write_json(run / 'IMPLEMENTATION.json', dict(script_sha256=manifest,
            preregistration_sha256=PREG_SHA, source_attribution=attribution, prepared=prepared,
            frozen_utc=R.utcnow(), parent_load_once=True, workers=pool.worker_count(),
            sequential_phases=['controls', '168 indexed shards', 'canonical reducers']), immutable=True)
        controls = launch('controls', control, [(seed,) for seed in SEEDS])
        if any(item['status'] != 'OK' or item['result']['status'] != 'PASS' for item in controls):
            raise RuntimeError('C3 controls failed; no census launched')
        control_by_seed = {seed: item['result'] for seed, item in zip(SEEDS, controls)}
        block_args = [(seed, spec['block']) for spec in F.block_specs() for seed in SEEDS]
        shards = launch('blocks', block, block_args)
        if any(item['status'] != 'OK' or not item['result'].get('complete') for item in shards):
            raise RuntimeError('C3 census incomplete; no scientific reducer launched')
        byseed = {seed: [] for seed in SEEDS}
        for (seed, block_id), item in zip(block_args, shards):
            byseed[seed].append(item['result'])
        finish_args = [(seed, byseed[seed], str(run / ('seed-' + str(seed))), control_by_seed[seed]) for seed in SEEDS]
        launch('finish', finish, finish_args)
        failed_phase = None
    except BaseException:
        failure = traceback.format_exc()[-8000:]
    total_cpu, total_wall = cpu()-c0, time.monotonic()-w0
    all_items = [item for values in observed.values() for item in values.values()]
    attributable = sum(item.get('cpu_seconds') or 0 for item in all_items)
    overhead = max(0, total_cpu-attributable)
    attribution = R.provenance() + F.provenance()['source_attribution']
    result_records = []
    for index, seed in enumerate(SEEDS):
        items = [item for phase, values in observed.items() for i, item in values.items()
                 if phase_specs[phase][i][0] == seed]
        completed = observed['finish'].get(index)
        if completed is not None:
            statistics = completed.get('result', {})
            status = statistics.get('status') if completed['status'] == 'OK' else completed['status']
        else:
            status = 'EXPLORATORY'
            if any(item['status'] == 'ERROR' for item in items) or not prepared:
                status = 'ERROR'
            elif any(item['status'] == 'TIMEOUT' for item in items) or (failure and 'Budget' in failure):
                status = 'TIMEOUT'
            statistics = dict(complete=False, candidate=None, incomplete_phase=failed_phase,
                              completed_shards=sum(1 for i in observed['blocks'] if phase_specs['blocks'][i][0] == seed),
                              expected_shards=len(F.block_specs()), conceptual_domain=F.DOMAIN,
                              scope='No scientific PASS/NULL without complete shard coverage and all controls.')
        if status not in R.STATUSES:
            status = 'ERROR'
        record = dict(schema_version=1, experiment=EXPERIMENT, milestone='CONTINUATION-01',
            recorded_utc=R.utcnow(), seed=seed, n_permutations=0, status=status,
            word_blob_ids={p['path']: p['git_blob'] for p in attribution}, source_attribution=attribution,
            script_sha256=manifest,
            script_manifest_sha256=hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            preregistration_sha256=PREG_SHA, statistics=statistics, wall_seconds=total_wall,
            cpu_seconds=sum(item.get('cpu_seconds') or 0 for item in items) + (overhead if index == 0 else 0),
            peak_rss_bytes=max((item.get('peak_rss_bytes') or 0 for item in items), default=None),
            null_summary={'model': 'none: exhaustive constructive exchange census', 'mean': None, 'sd': None, 'empirical_p': None},
            decision={'pass_bar': protocol['experiments'][EXPERIMENT]['pass_bar'], 'verdict': status},
            confirmation_required=True, launch_failure=failure,
            task_errors=[item.get('error') for item in items if item.get('error')],
            scope='Constructive literal-fill/profile gain only; complete changed-obligation admission is a separate mandatory gate.')
        R.write_json(run / ('seed-' + str(seed)) / 'RESULT.json', record, immutable=True)
        result_records.append(record)
    statuses = {r['status'] for r in result_records}
    candidates = [r['statistics'].get('candidate') for r in result_records]
    candidate_agreement = all(candidates) and len({c['fill_artifact']['sha256'] for c in candidates}) == 1
    count_agreement = result_records[0]['statistics'].get('counts') == result_records[1]['statistics'].get('counts')
    agreed = len(statuses) == 1 and count_agreement and (result_records[0]['status'] != 'PASS' or candidate_agreement)
    verdict = result_records[0]['status'] if agreed else 'EXPLORATORY'
    confirmed = agreed and verdict in ('PASS', 'NULL')
    streak = 2 if confirmed and verdict == 'NULL' else (0 if confirmed and verdict == 'PASS' else 1)
    row.update(status=verdict, confirmed=confirmed, candidate_identity_agreement=bool(candidate_agreement),
               count_agreement=count_agreement, cpu_seconds=total_cpu, updated_utc=R.utcnow(),
               result_files=[str((run / ('seed-' + str(s)) / 'RESULT.json').relative_to(R.PKG)) for s in SEEDS],
               consecutive_confirmed_nulls=streak, lane_stopped=streak >= 2)
    registry.setdefault('lane_status', {})['constructive-fill'] = dict(consecutive_confirmed_nulls=streak,
        stopped=streak >= 2, latest_experiment=EXPERIMENT,
        rule='C2 is the prior confirmed NULL; a confirmed C3 NULL is the second and stops this lane. Incomplete work does not reset the streak.')
    R.write_json(registry_path, registry)
    if streak >= 2:
        R.write_json(run / 'LANE-STOP.json', dict(status='STOP', lane='constructive-fill',
            experiments=['C2-LATEST-SAME-CALL', EXPERIMENT], consecutive_confirmed_nulls=2,
            scope='Two registered literal-fill pair-exchange families only; no global packing impossibility claim.',
            rule=protocol['experiments'][EXPERIMENT]['stop_rule'], preregistration_sha256=PREG_SHA), immutable=True)
    R.write_json(run / 'RUN.json', dict(status=verdict, confirmed=confirmed, total_cpu_seconds=total_cpu,
        total_wall_seconds=total_wall, failure=failure, incomplete_phase=failed_phase,
        completed_by_phase={key: len(value) for key, value in observed.items()},
        family_budget_seconds=BUDGET, lane_stopped=streak >= 2, candidate_identity_agreement=bool(candidate_agreement)), immutable=True)
    print(json.dumps(dict(experiment=EXPERIMENT, status=verdict, cpu_seconds=total_cpu,
                         wall_seconds=total_wall, lane_stopped=streak >= 2, failure=failure)), flush=True)
    if failure or verdict in ('ERROR', 'TIMEOUT'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
