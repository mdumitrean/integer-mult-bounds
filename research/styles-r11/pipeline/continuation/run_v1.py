"""Registered independent admission of the first confirmed latest-source fill."""
from datetime import datetime, timezone
from fractions import Fraction as Q
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
import admission as A
import outer_transfer as O
import outer_balance as B

ROUND = R.RESULTS / 'CONTINUATION-01'
EXPERIMENT = 'V1-FILL-ADMISSION'
PREG = ROUND / 'V1/PREREGISTRATION.json'
SEEDS = (11031, 29063)
RECORD = None


def need(value, message):
    if not value:
        raise ValueError(message)


def cpu():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+child.ru_utime+child.ru_stime


def snapshot():
    sources = set((R.PKG/'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(R.ROOT/'research') and path.suffix == '.py':
                sources.add(path)
    result = {}
    for path in sorted(sources):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        result[str(path.relative_to(R.ROOT))] = digest
        archive = ROUND/'SOURCES'/(digest+'.py.gz')
        archive.parent.mkdir(parents=True, exist_ok=True)
        if not archive.exists():
            archive.write_bytes(gzip.compress(raw, mtime=0))
    return result


def select_candidate(registry):
    for row in registry['experiments']:
        if row['lane'] != 'constructive-fill' or row['status'] != 'PASS' or not row.get('confirmed'):
            continue
        results = [A.read_data(R.PKG/path) for path in row['result_files']]
        if any(str(r['statistics'].get('baseline_pr')) != '2917' for r in results):
            continue
        need(len(results) == 2 and {r['seed'] for r in results} == set(SEEDS), 'confirmed two-seed input')
        candidates = [r['statistics']['candidate']['fill_artifact'] for r in results]
        need(len({c['sha256'] for c in candidates}) == 1, 'same candidate in both search seeds')
        return dict(search_experiment=row['id'], candidate=candidates[0],
            search_results=[dict(path=path, sha256=R.sha256(R.PKG/path)) for path in row['result_files']])
    raise ValueError('No confirmed positive latest-source fill candidate is eligible')


def task(seed, candidate):
    controls = A.admission_controls(seed)
    need(controls['status'] == 'PASS', 'independent owner/admission controls')
    admission = A.audit_fill_candidate(dict(seed=seed, candidate_path=candidate['path'],
                                            candidate_sha256=candidate['sha256']))
    need(admission['status'] == 'PASS', 'complete finite root separation')
    transfer = admission['source_bound_transfer']
    need(transfer['status'] == 'PASS_SOURCE_BOUND_FILL_TRANSFER', 'affected supplier transfer')
    C = admission['endpoint_admission']['complex_lower']
    claim = RECORD['data']['CLAIM.json']
    prior_release = RECORD['data']['evidence/RELEASE-RECEIPT.json']
    outer = O.certify(C, claim, prior_release, seed)
    balance = B.certify(C, claim, outer)
    # Independent checker result uses exact rational headline, never a display decimal.
    need(Q(balance['kappa']) == Q(outer['ledger']['kappa']), 'independent outer headline agreement')
    need(balance['status'].startswith('PASS'), 'independent outer balance check')
    admission['obligations']['outer'] = dict(status='PASS_TWO_EXACT_ARITHMETIC_CHECKERS',
        kappa=outer['ledger']['kappa'], fresh_functional_checks=50,
        historical_comparisons_transferred=13, rejecting_controls=17)
    admission['obligations']['strict_global_supplier']['new_release_binding'] = 'BOUND_BY_RUN_RECEIPT'
    return dict(status='PASS', seed=seed, candidate=candidate, controls=controls,
        admission=admission, outer=outer, independent_balance=balance,
        headline=dict(kappa=outer['ledger']['kappa'], kappa_decimal=outer['kappa_decimal'],
            improvement=outer['improvement'], improvement_decimal=outer['improvement_decimal'],
            complex_lower=C, baseline_pr=2917, conditional=True),
        fresh_native_replay=False, inherited_obligations=admission['obligations']['inherited_theorem'],
        solver_calls=0, n_permutations=0,
        scope='Conditional finite improvement with all changed fill/supplier/arithmetic obligations checked. Unchanged native and outer mechanism evidence is source-bound reuse; all-size theorem hypotheses remain.')


def main():
    global RECORD
    protocol = A.read_data(PREG)
    need(protocol['state'] == 'FROZEN' and tuple(protocol['seeds']) == SEEDS, 'frozen V1 protocol')
    need(datetime.now(timezone.utc) < datetime.fromisoformat(protocol['hard_stop_utc']), 'hard stop')
    registry_path = ROUND/'EXPERIMENTS.json'
    registry = A.read_data(registry_path)
    selected = select_candidate(registry)
    row = next(x for x in registry['experiments'] if x['id'] == EXPERIMENT)
    need(row['status'] == 'planned', 'new validation attempt only')
    run = ROUND/EXPERIMENT/'v1'
    run.mkdir(parents=True, exist_ok=False)
    row.update(status='running', started_utc=R.utcnow())
    R.write_json(registry_path, registry)
    start_cpu, start_wall = cpu(), time.monotonic()
    observed, failure, manifest = {}, None, {}
    attribution = R.provenance()+F.provenance()['source_attribution']
    try:
        F.prepare(2917)
        RECORD = F.get_record()
        prepared = A.prepare(RECORD, dict(pr=2917, commit=F.HEAD, manifest_sha256=F.MANIFEST_SHA,
            manifest_path='data/continuation-01/pr2917/MANIFEST.json'))
        manifest = snapshot()
        R.write_json(run/'IMPLEMENTATION.json', dict(script_sha256=manifest,
            preregistration_sha256=R.sha256(PREG), selected=selected, parent_prepared=prepared,
            source_attribution=attribution, frozen_utc=R.utcnow()), immutable=True)
        def checkpoint(index, item):
            observed[index] = item
            R.write_json(run/('seed-'+str(SEEDS[index]))/'POOL-CHECKPOINT.json', item, immutable=True)
            print(json.dumps(dict(seed=SEEDS[index], pool_status=item['status'],
                result_status=item.get('result', {}).get('status'), cpu_seconds=item.get('cpu_seconds'))), flush=True)
        pool.run_pool(task, [(s, selected['candidate']) for s in SEEDS], workers=pool.worker_count(),
            timeout=600, rss_gib=6, working_set_gib=1, projection_path=run/'MEMORY-PROJECTION.json',
            on_result=checkpoint, cpu_budget_seconds=7200-(cpu()-start_cpu))
    except BaseException:
        failure = traceback.format_exc()[-8000:]
    total_cpu, total_wall = cpu()-start_cpu, time.monotonic()-start_wall
    overhead = max(0, total_cpu-sum(x.get('cpu_seconds') or 0 for x in observed.values()))
    records = []
    for i, seed in enumerate(SEEDS):
        item = observed.get(i, dict(status='ERROR', error=failure or 'task uncollected'))
        statistics = item.get('result', {})
        status = statistics.get('status', 'ERROR') if item['status'] == 'OK' else item['status']
        if status not in ('PASS', 'TIMEOUT', 'ERROR', 'EXPLORATORY'):
            status = 'EXPLORATORY'
        result = dict(schema_version=1, experiment=EXPERIMENT, milestone='CONTINUATION-01',
            seed=seed, n_permutations=0, status=status, recorded_utc=R.utcnow(),
            word_blob_ids={p['path']: p['git_blob'] for p in attribution}, source_attribution=attribution,
            script_sha256=manifest,
            script_manifest_sha256=hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest(),
            preregistration_sha256=R.sha256(PREG), statistics=statistics,
            wall_seconds=item.get('seconds', total_wall),
            cpu_seconds=(item.get('cpu_seconds') or 0)+(overhead if i == 0 else 0),
            peak_rss_bytes=item.get('peak_rss_bytes'),
            null_summary=dict(model='none: exact conditional candidate admission', mean=None, sd=None, empirical_p=None),
            decision=dict(pass_bar=protocol['experiments'][EXPERIMENT]['pass_bar'], verdict=status),
            confirmation_required=True, launch_failure=failure, task_error=item.get('error'),
            scope='Validation does not reset a scientific lane NULL streak. Source-bound reused evidence is distinct from fresh checks.')
        R.write_json(run/('seed-'+str(seed))/'RESULT.json', result, immutable=True)
        records.append(result)
    passed = all(r['status'] == 'PASS' for r in records)
    if passed:
        identity = [json.dumps(dict(headline=r['statistics']['headline'],
            profile=r['statistics']['admission']['candidate_profile'],
            candidate_sha=r['statistics']['candidate']['sha256']), sort_keys=True) for r in records]
        passed = identity[0] == identity[1]
    status = 'PASS' if passed else ('ERROR' if failure or any(r['status'] == 'ERROR' for r in records) else 'EXPLORATORY')
    files = [str((run/('seed-'+str(s))/'RESULT.json').relative_to(R.PKG)) for s in SEEDS]
    row.update(status=status, confirmed=passed, candidate_identity_agreement=passed,
        result_files=files, updated_utc=R.utcnow(), cpu_seconds=total_cpu)
    R.write_json(registry_path, registry)
    receipt = dict(status=status, selected=selected, total_cpu_seconds=total_cpu,
        total_wall_seconds=total_wall, failure=failure,
        result_files=[dict(path=p, sha256=R.sha256(R.PKG/p)) for p in files],
        source_implementation_sha256=R.sha256(run/'IMPLEMENTATION.json'),
        preregistration_sha256=R.sha256(PREG), fresh_native_replay=False,
        scope='No public posting, selected-frontier update or all-size theorem claim. Coordinator review remains required.')
    if passed:
        receipt['headline'] = records[0]['statistics']['headline']
        receipt['source_bound_prior_evidence'] = records[0]['statistics']['admission']['source_bound_transfer']['prior_evidence']
    R.write_json(run/'RELEASE-RECEIPT.json', receipt, immutable=True)
    print(json.dumps(dict(experiment=EXPERIMENT, status=status, cpu_seconds=total_cpu,
        wall_seconds=total_wall, failure=failure)), flush=True)
    if status != 'PASS':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
