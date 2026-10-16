"""Frozen fixed-work infrastructure benchmark; coordinator execution only.

No word, solver, statistical hypothesis or scientific outcome is evaluated.
The same numerical tasks are compared at both registered worker allocations.
"""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
THREAD_KEYS = ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
               'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'BLIS_NUM_THREADS')
for _key in THREAD_KEYS:
    os.environ[_key] = '1'
HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/RESOURCE-SCALING-13'
DATA = PKG / 'data/resources13'
NP = POOL = X = Y = None
INPUT_SHA = None
CONFIG = None

# Root can copy this literal mapping into the preregistration before import.
PROTOCOL = {
    'seeds': [73001, 146003],
    'workers': [61, 120],
    'worker_orders': {'73001': [61, 120], '146003': [120, 61]},
    'tasks': 480,
    'iterations': 10000,
    'rows': 32768,
    'cols': 32,
    'data_seed': 130073,
    'estimate_rss': 1.5,
    'rss_gib': 4,
    'timeout': 180,
    'maxtasksperchild': 50,
    'cpu_budget_per_run': 12000,
    'step_size': 0.04,
    'ridge': 0.01,
    'tiny_rows': 16,
    'tiny_cols': 4,
    'tiny_iterations': 7,
    'tiny_tolerance': 1e-12,
    'minimum_speedup_each_seed': 1.15,
}


def need(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def numerical_result(value):
    return {k: v for k, v in value.items() if k != 'worker_pid'}


def percentiles(values):
    values = sorted(values)
    if not values:
        return None
    def at(p):
        position = p * (len(values) - 1)
        low = math.floor(position)
        high = math.ceil(position)
        return values[low] + (values[high] - values[low]) * (position - low)
    return dict(count=len(values), minimum=values[0], p25=at(.25), median=at(.5),
                p90=at(.9), p95=at(.95), p99=at(.99), maximum=values[-1])


def reference(path):
    path = Path(path)
    return dict(path=str(path.relative_to(PKG)), sha256=sha(path), bytes=path.stat().st_size)


def telemetry_summary(path):
    if not path.exists():
        return None
    samples = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return dict(samples=len(samples),
                maximum_live_workers=max((v['live_workers'] for v in samples), default=0),
                maximum_running_workers=max((v['running_workers'] for v in samples), default=0),
                maximum_worker_rss_bytes=max((v['maximum_worker_rss_bytes'] for v in samples), default=0),
                minimum_available_memory_bytes=min((v['memory']['available_bytes'] for v in samples), default=None),
                scope='Sequential half-second samples, not an instantaneous CPU-utilization measurement; shared RSS counted in every worker.')


def write(path, value):
    path = Path(path)
    need(not path.exists(), 'immutable artifact already exists: ' + str(path))
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    if path.suffix == '.gz':
        raw = gzip.compress(raw, compresslevel=5, mtime=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(raw)
    return reference(path)


def iterate(features, target, weights, iterations):
    """Exactly the registered iteration count; no convergence or time stopping."""
    for _ in range(iterations):
        residual = features @ weights - target
        gradient = (features.T @ residual) / features.shape[0] + CONFIG['ridge'] * weights
        weights = weights - CONFIG['step_size'] * gradient
    return weights


def tiny_reference():
    """Independent scalar-loop arithmetic reference, run once in the parent."""
    rows, cols = CONFIG['tiny_rows'], CONFIG['tiny_cols']
    features = [[((i * 5 + j * 3) % 17 - 8) / 8.0 for j in range(cols)] for i in range(rows)]
    target = [((i * 7) % 11 - 5) / 8.0 for i in range(rows)]
    initial = [(j - 2) / 16.0 for j in range(cols)]
    serial = list(initial)
    for _ in range(CONFIG['tiny_iterations']):
        residual = [sum(features[i][j] * serial[j] for j in range(cols)) - target[i]
                    for i in range(rows)]
        gradient = [sum(features[i][j] * residual[i] for i in range(rows)) / rows
                    + CONFIG['ridge'] * serial[j] for j in range(cols)]
        serial = [serial[j] - CONFIG['step_size'] * gradient[j] for j in range(cols)]
    vectorized = iterate(NP.asarray(features, dtype=NP.float64), NP.asarray(target, dtype=NP.float64),
                         NP.asarray(initial, dtype=NP.float64), CONFIG['tiny_iterations'])
    error = max(abs(float(vectorized[j]) - serial[j]) for j in range(cols))
    need(error <= CONFIG['tiny_tolerance'] and all(math.isfinite(v) for v in serial),
         'tiny independent scalar reference agrees')
    return dict(status='PASS', rows=rows, cols=cols, iterations=CONFIG['tiny_iterations'],
                scalar_weights=serial, vectorized_weights=vectorized.tolist(),
                max_absolute_error=error, tolerance=CONFIG['tiny_tolerance'])


def task(spec):
    need(X is not None and Y is not None, 'once-parent cached synthetic features')
    need(all(os.environ.get(k) == '1' for k in THREAD_KEYS), 'single-thread numerical libraries')
    initial = NP.asarray([((j * 11 + spec['task_id'] * 7 + spec['seed']) % 31 - 15) / 128.0
                          for j in range(CONFIG['cols'])], dtype=NP.float64)
    weights = iterate(X, Y, initial, CONFIG['iterations'])
    residual = X @ weights - Y
    loss = float((residual @ residual) / CONFIG['rows'] + CONFIG['ridge'] * (weights @ weights))
    need(bool(NP.isfinite(weights).all()) and math.isfinite(loss), 'finite numerical benchmark output')
    return dict(status='PASS', seed=spec['seed'], task_id=spec['task_id'],
                worker_pid=os.getpid(),
                iterations=CONFIG['iterations'], input_sha256=INPUT_SHA,
                weights_sha256=hashlib.sha256(weights.astype('<f8', copy=False).tobytes()).hexdigest(),
                weights_sum=float(weights.sum()), weights_squared_norm=float(weights @ weights), loss=loss)


def main():
    global NP, POOL, X, Y, INPUT_SHA, CONFIG
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--implementation-sha256', required=True)
    parser.add_argument('--attempt', default='v1')
    args = parser.parse_args()
    need(sys.flags.isolated and not sys.flags.optimize, 'Python -I with assertions enabled')
    need(args.attempt.replace('-', '').replace('_', '').isalnum(), 'simple new attempt name')
    registration_path = ROUND / 'PREREGISTRATION.json'
    implementation_path = ROUND / 'IMPLEMENTATION-PINS.json'
    need(sha(registration_path) == args.registration_sha256, 'frozen registration SHA256')
    need(sha(implementation_path) == args.implementation_sha256, 'frozen implementation SHA256')
    registration = json.loads(registration_path.read_text())
    implementation = json.loads(implementation_path.read_text())
    need(registration.get('state') == 'FROZEN', 'registration state is FROZEN')
    CONFIG = registration.get('protocol', registration)
    need(all(CONFIG.get(k) == value for k, value in PROTOCOL.items()), 'exact fixed workload and resource protocol')
    required = [Path(__file__), HERE / 'measured_pool.py', HERE.parent / 'pool.py']
    need(all(str(p.relative_to(ROOT)) in implementation['sha256'] for p in required),
         'runner, wrapper and immutable pool source pins')
    for relative, expected in implementation['sha256'].items():
        path = (ROOT / relative).resolve()
        need(path.is_relative_to(ROOT) and sha(path) == expected, 'source pin before import: ' + relative)
        if 'archives' in implementation:
            archived = implementation['archives'][expected]
            archive_path = (PKG / archived['path']).resolve()
            need(archive_path.is_relative_to(PKG), 'source archive confined to package')
            need(hashlib.sha256(gzip.decompress(archive_path.read_bytes())).hexdigest() == expected,
                 'source archive bytes: ' + relative)
    original_pins = PKG / 'data/words/PINS.json'
    attribution = dict(original_pins=reference(original_pins), original_entries=len(json.loads(original_pins.read_text())['files']),
                       scope='Infrastructure-only synthetic benchmark; no source word is processed. All original credits remain bound.')
    need(attribution['original_entries'] == 21, 'all original attribution entries retained')
    if 'source_attribution' in registration:
        need(registration['source_attribution']['original_pins']['sha256'] == attribution['original_pins']['sha256'],
             'registered original attribution pin')
    # Own modules and NumPy are imported only after every source pin above.
    sys.path[:0] = [str(HERE), str(HERE.parent)]
    import measured_pool as POOL
    import numpy as NP
    output = ROUND / args.attempt
    data = DATA / args.attempt
    output.mkdir(parents=True, exist_ok=False)
    data.mkdir(parents=True, exist_ok=False)
    overall_cpu, overall_wall = cpu(), time.monotonic()
    completed, summaries, cells, failure = [], {}, [], None
    control_ref = input_ref = None
    status = 'ERROR'
    try:
        control_ref = write(data / 'SERIAL-REFERENCE.json', tiny_reference())
        generator = NP.random.Generator(NP.random.PCG64(CONFIG['data_seed']))
        X = generator.standard_normal((CONFIG['rows'], CONFIG['cols']), dtype=NP.float64)
        truth = NP.linspace(-0.2, 0.2, CONFIG['cols'], dtype=NP.float64)
        Y = X @ truth + (NP.arange(CONFIG['rows'], dtype=NP.float64) % 13 - 6) / 512.0
        X.flags.writeable = False
        Y.flags.writeable = False
        hasher = hashlib.sha256()
        hasher.update(X.astype('<f8', copy=False).tobytes())
        hasher.update(Y.astype('<f8', copy=False).tobytes())
        INPUT_SHA = hasher.hexdigest()
        try:
            import threadpoolctl
        except ImportError:
            native_threads = dict(available=False, enforcement='single-thread environment set before NumPy import')
        else:
            libraries = threadpoolctl.threadpool_info()
            need(all(library.get('num_threads') == 1 for library in libraries),
                 'all loaded native numerical libraries use one thread')
            native_threads = dict(available=True, libraries=libraries,
                                  version=importlib.metadata.version('threadpoolctl'))
        input_ref = write(data / 'INPUT.json', dict(shape=list(X.shape), dtype=str(X.dtype),
            data_seed=CONFIG['data_seed'], input_sha256=INPUT_SHA, bytes=int(X.nbytes + Y.nbytes),
            loaded_once_in_parent=True, read_only_arrays=True, synthetic=True,
            python=sys.version, numpy=importlib.metadata.version('numpy'), platform=platform.platform(),
            thread_environment={k: os.environ[k] for k in THREAD_KEYS},
            native_threadpools=native_threads,
            affinity_cores=len(os.sched_getaffinity(0)), allocated_cores=128, reserved_cores=8))
        for seed in CONFIG['seeds']:
            specs = [dict(seed=seed, task_id=i) for i in range(CONFIG['tasks'])]
            spec_ref = write(data / ('TASKS-SEED-' + str(seed) + '.json.gz'), specs)
            for order_index, workers in enumerate(CONFIG['worker_orders'][str(seed)]):
                name = 'seed-%d-workers-%d' % (seed, workers)
                directory = data / name
                directory.mkdir(parents=True, exist_ok=False)
                projection_path = directory / 'MEMORY-PROJECTION.json'
                telemetry_path = directory / 'TELEMETRY.jsonl'
                records = {}
                started_cpu, started_wall = cpu(), time.monotonic()
                started_parent_cpu = time.process_time()
                started_children = resource.getrusage(resource.RUSAGE_CHILDREN)
                callback_cpu = callback_wall = 0.0
                cell_failure = None
                cell_status = 'ERROR'
                def checkpoint(index, item):
                    nonlocal callback_cpu, callback_wall
                    callback_start_cpu, callback_start_wall = time.process_time(), time.monotonic()
                    artifact = write(directory / ('task-%04d.json.gz' % index), item)
                    records[index] = dict(index=index, spec=specs[index], artifact=artifact,
                                          status=item['status'], cpu_seconds=item.get('cpu_seconds'),
                                          wall_seconds=item.get('seconds'), peak_rss_bytes=item.get('peak_rss_bytes'),
                                          result=item.get('result'), error=item.get('error'))
                    if len(records) % 60 == 0 or len(records) == len(specs):
                        print(json.dumps(dict(event='progress', seed=seed, workers=workers,
                            completed=len(records), tasks=len(specs), elapsed_seconds=time.monotonic()-started_wall)), flush=True)
                    callback_cpu += time.process_time() - callback_start_cpu
                    callback_wall += time.monotonic() - callback_start_wall
                print(json.dumps(dict(event='launch', seed=seed, workers=workers, tasks=len(specs),
                                      iterations=CONFIG['iterations'], utc=now())), flush=True)
                try:
                    returned = POOL.run_pool(task, [(s,) for s in specs],
                        estimated_worker_rss_gib=CONFIG['estimate_rss'], workers=workers,
                        timeout=CONFIG['timeout'], rss_gib=CONFIG['rss_gib'],
                        maxtasksperchild=CONFIG['maxtasksperchild'], projection_path=projection_path,
                        on_result=checkpoint, cpu_budget_seconds=CONFIG['cpu_budget_per_run'],
                        telemetry_path=telemetry_path)
                    need(len(returned) == len(records) == len(specs), 'all fixed tasks accounted')
                    need(all(item['status'] == 'OK' and item['result']['status'] == 'PASS' for item in returned),
                         'all fixed numerical tasks completed')
                    checksums = [numerical_result(item['result']) for item in returned]
                    if seed in summaries:
                        need(checksums == summaries[seed], 'exact task checksums and numerical summaries across schedules')
                    else:
                        summaries[seed] = checksums
                    cell_status = 'PASS'
                except BaseException as error:
                    cell_failure = dict(type=type(error).__name__, message=str(error),
                                        traceback=traceback.format_exc()[-12000:])
                    cell_status = 'TIMEOUT' if isinstance(error, TimeoutError) else 'ERROR'
                elapsed_cpu, elapsed_wall = cpu() - started_cpu, time.monotonic() - started_wall
                children = resource.getrusage(resource.RUSAGE_CHILDREN)
                worker_cpu = (children.ru_utime + children.ru_stime
                              - started_children.ru_utime - started_children.ru_stime)
                parent_cpu = time.process_time() - started_parent_cpu
                ordered = [records[k] for k in sorted(records)]
                by_worker = {}
                for item in ordered:
                    if isinstance(item['result'], dict) and 'worker_pid' in item['result']:
                        totals = by_worker.setdefault(item['result']['worker_pid'], dict(cpu=0.0, task_wall=0.0, tasks=0))
                        totals['cpu'] += item['cpu_seconds'] or 0
                        totals['task_wall'] += item['wall_seconds'] or 0
                        totals['tasks'] += 1
                manifest = write(directory / 'TASK-RECEIPTS.json.gz', ordered)
                row = dict(schema_version=1, experiment='RESOURCE-SCALING-13', seed=seed,
                    workers=workers, schedule_order_index=order_index, status=cell_status, recorded_utc=now(),
                    preregistration_sha256=args.registration_sha256,
                    implementation_sha256=args.implementation_sha256, script_sha256=sha(Path(__file__)),
                    source_attribution=attribution, workload=dict(specs=spec_ref, protocol=PROTOCOL,
                        input=input_ref, serial_reference=control_ref, duration_adaptation=False),
                    task_receipts=manifest, tasks_completed=len(ordered), tasks_planned=len(specs),
                    task_cpu_seconds=sum(x['cpu_seconds'] or 0 for x in ordered),
                    worker_cpu_seconds=worker_cpu, parent_cpu_seconds=parent_cpu,
                    callback_cpu_seconds=callback_cpu, callback_wall_seconds=callback_wall,
                    cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall,
                    average_core_equivalents=elapsed_cpu / elapsed_wall,
                    tasks_per_second=len(ordered) / elapsed_wall,
                    peak_rss_bytes=max((x['peak_rss_bytes'] or 0 for x in ordered), default=0),
                    largest_worker_rss_bytes=max((x['peak_rss_bytes'] or 0 for x in ordered), default=0),
                    task_cpu_duration_seconds=percentiles([x['cpu_seconds'] for x in ordered if x['cpu_seconds'] is not None]),
                    task_wall_duration_seconds=percentiles([x['wall_seconds'] for x in ordered if x['wall_seconds'] is not None]),
                    worker_task_cpu_total_seconds=percentiles([v['cpu'] for v in by_worker.values()]),
                    worker_task_wall_sum_seconds=percentiles([v['task_wall'] for v in by_worker.values()]),
                    tasks_per_worker=percentiles([v['tasks'] for v in by_worker.values()]),
                    timing_scope='Cell timing includes pool startup, tasks, callbacks, termination/join and numerical validation; final receipt serialization is included in overall timing.',
                    checksum_set_sha256=digest([numerical_result(x['result']) for x in ordered]) if cell_status == 'PASS' else None,
                    memory_projection=reference(projection_path) if projection_path.exists() else None,
                    telemetry=reference(telemetry_path) if telemetry_path.exists() else None,
                    telemetry_summary=telemetry_summary(telemetry_path),
                    word_blob_ids=[], n_permutations=0,
                    null_summary=dict(applicable=False, mean=None, sd=None, empirical_p=None),
                    failure=cell_failure, scientific_outcomes=False, kappa_claim=False,
                    scope='Fixed-work numerical process-pool throughput and resource accounting only.')
                row['statistics'] = dict(tasks_planned=len(specs), tasks_completed=len(ordered),
                    cpu_seconds=elapsed_cpu, worker_cpu_seconds=worker_cpu, parent_cpu_seconds=parent_cpu,
                    wall_seconds=elapsed_wall, tasks_per_second=row['tasks_per_second'],
                    average_core_equivalents=row['average_core_equivalents'],
                    largest_worker_rss_bytes=row['largest_worker_rss_bytes'],
                    task_cpu_duration_seconds=row['task_cpu_duration_seconds'],
                    task_wall_duration_seconds=row['task_wall_duration_seconds'],
                    checksum_set_sha256=row['checksum_set_sha256'])
                row['decision'] = dict(numerical_resource_admission=cell_status,
                    serial_reference_passed=True, all_task_outputs_finite=cell_status == 'PASS',
                    paired_schedule_outputs_equal=True if cell_status == 'PASS' and order_index == 1 else None,
                    paired_validation_location='RUN.json comparisons and the second schedule RESULT for this seed',
                    performance='Separate two-seed throughput decision in RUN.json; no numerical status promotion',
                    scientific_outcome=False, kappa_claim=False)
                cells.append(row)
                completed.append(write(output / name / 'RESULT.json', row))
                print(json.dumps(dict(event='complete', seed=seed, workers=workers, status=cell_status,
                                      cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall)), flush=True)
                if cell_failure:
                    raise RuntimeError('preserved failed benchmark cell: ' + name + ': ' + cell_failure['message'])
        status = 'PASS'
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()[-12000:])
    comparisons = []
    for seed in CONFIG['seeds']:
        pair = {v['workers']: v for v in cells if v['seed'] == seed and v['status'] == 'PASS'}
        if set(pair) == set(CONFIG['workers']):
            comparisons.append(dict(seed=seed, checksums_equal=pair[61]['checksum_set_sha256'] == pair[120]['checksum_set_sha256'],
                elapsed_speedup_120_vs_61=pair[61]['wall_seconds'] / pair[120]['wall_seconds'],
                throughput_ratio_120_vs_61=pair[120]['tasks_per_second'] / pair[61]['tasks_per_second'],
                worker_order=CONFIG['worker_orders'][str(seed)]))
    report = dict(schema_version=1, experiment='RESOURCE-SCALING-13', status=status, recorded_utc=now(),
        preregistration_sha256=args.registration_sha256, implementation_sha256=args.implementation_sha256,
        source_attribution=attribution, result_files=completed, comparisons=comparisons,
        confirmed=status == 'PASS' and len(comparisons) == 2 and all(v['checksums_equal'] for v in comparisons),
        total_cpu_seconds=cpu() - overall_cpu, total_wall_seconds=time.monotonic() - overall_wall,
        failure=failure, scientific_outcomes=False, kappa_claim=False,
        scope='Infrastructure-only fixed-work benchmark. Counterbalanced order; no duration calibration or hardware-independent performance claim.')
    speed_confirmed = (report['confirmed'] and all(v['elapsed_speedup_120_vs_61'] >= CONFIG['minimum_speedup_each_seed']
                                                   for v in comparisons))
    report['numerical_resource_admission_status'] = status
    report['performance_status'] = 'PASS' if speed_confirmed else 'EXPLORATORY'
    report['choose_120_for_this_workload'] = speed_confirmed
    report['speedup_threshold_each_seed'] = CONFIG['minimum_speedup_each_seed']
    report['performance_scope'] = 'The120-worker recommendation applies only to this fixed coarse synthetic workload; numerical/resource admission and throughput confirmation are separate.'
    receipt = write(output / 'RUN.json', report)
    print(json.dumps(dict(status=status, run=receipt, cpu_seconds=report['total_cpu_seconds'],
                          wall_seconds=report['total_wall_seconds'], comparisons=comparisons)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
