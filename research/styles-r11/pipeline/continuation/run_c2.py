"""Run the independently registered same-call exchange census on pinned PR2917."""
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
import latest_fill as F

ROUND = R.RESULTS / 'CONTINUATION-01'
EXPERIMENT = 'C2-LATEST-SAME-CALL'
PREG = ROUND / 'C2/PREREGISTRATION.json'
SEEDS = (11031, 29063)


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


def task(seed, directory):
    return F.c2_task(seed, directory, max_seconds=180)


def main():
    protocol = json.loads(PREG.read_text())
    if protocol['state'] != 'FROZEN' or tuple(protocol['seeds']) != SEEDS:
        raise ValueError('frozen family and seed binding')
    if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['hard_stop_utc']):
        raise RuntimeError('hard stop reached')
    run = ROUND / EXPERIMENT / 'v1'
    if run.exists():
        raise FileExistsError('immutable attempt already exists: ' + str(run))
    run.mkdir(parents=True)
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(row for row in registry['experiments'] if row['id'] == EXPERIMENT)
    if row['status'] != 'planned':
        raise ValueError('unplanned repeated launch')
    row.update(status='running', started_utc=R.utcnow())
    R.write_json(registry_path, registry)
    c0, w0 = cpu(), time.monotonic()
    observed, failure, prepared, manifest = {}, None, None, {}
    try:
        prepared = F.prepare(pr=2917)
        attribution = R.provenance() + F.provenance()['source_attribution']
        manifest = source_snapshot(ROUND / 'SOURCES')
        R.write_json(run / 'IMPLEMENTATION.json', dict(script_sha256=manifest,
            preregistration_sha256=R.sha256(PREG), source_attribution=attribution,
            prepared=prepared, frozen_utc=R.utcnow()), immutable=True)
        args = []
        for seed in SEEDS:
            directory = run / ('seed-' + str(seed))
            directory.mkdir()
            args.append((seed, str(directory)))
        def checkpoint(index, item):
            observed[index] = item
            R.write_json(run / ('seed-' + str(SEEDS[index])) / 'POOL-CHECKPOINT.json', item, immutable=True)
            print(json.dumps({'seed': SEEDS[index], 'pool_status': item['status'],
                              'result_status': item.get('result', {}).get('status'),
                              'cpu_seconds': item.get('cpu_seconds')}), flush=True)
        pool.run_pool(task, args, workers=pool.worker_count(), timeout=600, rss_gib=6,
                      working_set_gib=1, projection_path=run / 'MEMORY-PROJECTION.json',
                      on_result=checkpoint, cpu_budget_seconds=7200-(cpu()-c0))
    except BaseException:
        failure = traceback.format_exc()[-8000:]
    total_cpu, total_wall = cpu()-c0, time.monotonic()-w0
    attributable = sum(item.get('cpu_seconds') or 0 for item in observed.values())
    overhead = max(0, total_cpu-attributable)
    attribution = R.provenance() + F.provenance()['source_attribution']
    records = []
    for index, seed in enumerate(SEEDS):
        item = observed.get(index, {'status': 'ERROR', 'error': failure or 'task not collected'})
        statistics = item.get('result', {})
        status = statistics.get('status') if item['status'] == 'OK' else item['status']
        if status not in R.STATUSES:
            status = 'ERROR'
        record = dict(schema_version=1, experiment=EXPERIMENT, milestone='CONTINUATION-01',
            recorded_utc=R.utcnow(), seed=seed, n_permutations=0, status=status,
            word_blob_ids={p['path']: p['git_blob'] for p in attribution},
            source_attribution=attribution, script_sha256=manifest,
            script_manifest_sha256=hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            preregistration_sha256=R.sha256(PREG), statistics=statistics,
            wall_seconds=item.get('seconds', total_wall),
            cpu_seconds=(item.get('cpu_seconds') or 0) + (overhead if index==0 else 0),
            peak_rss_bytes=item.get('peak_rss_bytes'),
            null_summary={'model': 'none: exhaustive constructive pair census', 'mean': None, 'sd': None, 'empirical_p': None},
            decision={'pass_bar': protocol['experiments'][EXPERIMENT]['pass_bar'], 'verdict': status},
            confirmation_required=True, launch_failure=failure, task_error=item.get('error'),
            scope='Constructive literal-fill gain only. Complete supplier and outer admission are separate mandatory gates; not yet an integer-kappa claim.')
        path = run / ('seed-' + str(seed)) / 'RESULT.json'
        R.write_json(path, record, immutable=True)
        records.append(record)
    statuses = {r['status'] for r in records}
    same = len(statuses) == 1
    candidates = [r['statistics'].get('candidate') for r in records]
    candidate_agreement = all(candidates) and len({c['fill_artifact']['sha256'] for c in candidates}) == 1
    agreed = same and (records[0]['status'] != 'PASS' or candidate_agreement)
    row.update(status=records[0]['status'] if agreed else 'EXPLORATORY',
               confirmed=agreed and records[0]['status'] in ('PASS', 'NULL'),
               candidate_identity_agreement=bool(candidate_agreement),
               result_files=[str((run/('seed-'+str(s))/'RESULT.json').relative_to(R.PKG)) for s in SEEDS],
               updated_utc=R.utcnow(), cpu_seconds=total_cpu,
               confirmation_note='Different traversal seeds; selected candidate identity must also agree before a positive decision stands.')
    R.write_json(registry_path, registry)
    R.write_json(run / 'RUN.json', dict(status=row['status'], total_cpu_seconds=total_cpu,
                 total_wall_seconds=total_wall, failure=failure, completed=len(observed)), immutable=True)
    print(json.dumps({'experiment': EXPERIMENT, 'status': row['status'], 'cpu_seconds': total_cpu,
                      'wall_seconds': total_wall, 'failure': failure}), flush=True)
    if failure or row['status'] in ('ERROR', 'TIMEOUT'):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
