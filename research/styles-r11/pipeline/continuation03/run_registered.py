"""Frozen continuation03 controls/census; all scientific tasks use pool.py.

Source packages are inert JSON. This runner never imports acquired PR code.
Attempts, source snapshots, task receipts and per-seed decisions are immutable.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as Q
from pathlib import Path
import argparse
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
sys.path[:0] = [str(HERE), str(HERE.parent/'continuation'), str(HERE.parent)]
import records as R
import pool
import source2957 as S
import admission as A

ROUND = R.RESULTS/'CONTINUATION-03'
PINS = {'T1': '2a4cc6608f4d25ff7eb31150de3e604ac4a3e4d2437df38d08db4dc79cb9864e',
        'G3': '752227cd9874ada104a967e02c0574d0a280902a7f264a9a3ee0fb2392648906',
        'G4': '486b75d92edc4f47c595f83c75af1c48dcbb7d6182e0ad86253b8184c5006175'}
SEEDS = (14051, 33073)
RECORDS = {}
MODULE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+children.ru_utime+children.ru_stime


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def artifact(path, value):
    raw = canonical(value)
    data = gzip.compress(raw, mtime=0) if path.name.endswith('.gz') else raw
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)
    return dict(path=str(path.relative_to(R.PKG)), sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data), payload_sha256=hashlib.sha256(raw).hexdigest())


def snapshot():
    paths = set((R.PKG/'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(R.ROOT/'research') and path.suffix == '.py':
                need(not path.is_relative_to(R.PKG/'data'), 'never import acquired code')
                paths.add(path)
    directory = ROUND/'SOURCES'
    directory.mkdir(exist_ok=True)
    result = {}
    for path in sorted(paths):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        result[str(path.relative_to(R.ROOT))] = sha
        target = directory/(sha+'.py.gz')
        if target.exists():
            need(gzip.decompress(target.read_bytes()) == raw, 'immutable source preimage')
        else:
            with target.open('xb') as handle:
                handle.write(gzip.compress(raw, mtime=0))
    return result


def scientific(value):
    """Remove only execution metadata, retaining literal scientific content."""
    if isinstance(value, list):
        return [scientific(v) for v in value]
    if isinstance(value, dict):
        return {k: scientific(v) for k, v in value.items()
                if k not in {'seed', 'cpu_seconds', 'wall_seconds', 'elapsed_seconds',
                             'seconds', 'recorded_utc', 'output_dir', 'schedule',
                             'delivered_payloads'}}
    return value


def worker(spec):
    kind = spec['kind']
    if kind == 'closure':
        return MODULE.controls_task(spec['seed'])
    if kind == 'algebra_control':
        return MODULE.controls_task(spec['seed'])
    if kind == 'baseline':
        return S.baseline_task(spec)
    if kind == 'census':
        return MODULE.census_task(spec)
    if kind == 'price':
        return MODULE.price_task(spec)
    if kind == 'validation':
        ref = spec['word']
        path = R.PKG/ref['path']
        need(path.resolve().is_relative_to(ROUND), 'candidate artifact confinement')
        need(R.sha256(path) == ref['sha256'], 'candidate artifact binding')
        raw = json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())
        audit = A.local_admission(raw, RECORDS[spec['provider']]['attribution'])
        need(audit['audit']['checked_columns'] == 632, 'all632 live input columns')
        bad_profile = deepcopy(raw)
        profile = bad_profile['report']['local_profile']
        rank = min(profile, key=int)
        profile[rank] -= 1
        rejected_profile = False
        try:
            A.local_admission(bad_profile, RECORDS[spec['provider']]['attribution'])
        except (AssertionError, ValueError):
            rejected_profile = True
        need(rejected_profile, 'omitted paid child control must reject')
        bad_cleanup = deepcopy(raw)
        need(bool(bad_cleanup['cleanup']), 'nonempty candidate cleanup')
        del bad_cleanup['cleanup'][0]
        rejected_cleanup = False
        try:
            A.local_admission(bad_cleanup, RECORDS[spec['provider']]['attribution'])
        except (AssertionError, ValueError):
            rejected_cleanup = True
        need(rejected_cleanup, 'omitted cleanup control must reject')
        return dict(status='PASS', seed=spec['seed'], provider=spec['provider'],
                    candidate_id=spec['candidate_id'], audit=audit,
                    negative_controls=dict(omitted_paid_child=rejected_profile,
                                           omitted_cleanup=rejected_cleanup),
                    fresh_native='UNRUN_REQUIRED', full_supplier_outer='UNRUN_REQUIRED')
    raise ValueError('unregistered worker kind: '+kind)


def main():
    global RECORDS, MODULE
    parser = argparse.ArgumentParser()
    parser.add_argument('--family', choices=sorted(PINS), required=True)
    parser.add_argument('--attempt', default='v1')
    args = parser.parse_args()
    need(args.attempt.startswith('v') and args.attempt[1:].isdigit(), 'canonical attempt')
    family = args.family
    preg = ROUND/family/'PREREGISTRATION.json'
    protocol = json.loads(preg.read_text())
    need(R.sha256(preg) == PINS[family] and protocol['state'] == 'FROZEN', 'frozen preregistration')
    need(tuple(protocol['seeds']) == SEEDS, 'registered seeds')
    need(not sys.flags.optimize and sys.flags.isolated, 'isolated Python and enabled assertions')
    need(sys.pycache_prefix is not None and not Path(sys.pycache_prefix).exists(), 'unused private bytecode namespace')
    implementation_path = ROUND/family/('IMPLEMENTATION-PINS-'+args.attempt+'.json')
    implementation = json.loads(implementation_path.read_text())
    for path, sha in implementation['sha256'].items():
        need(R.sha256(R.ROOT/path) == sha, 'pre-execution source pin: '+path)
    registry_path = ROUND/'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(row for row in registry['experiments'] if row['id'] == protocol['experiment'])
    need(registry['no_active_experiments'], 'only one scientific pool at a time')
    need(row['status'] == 'planned' or row.get('execution') == 'INCOMPLETE', 'new or documented repaired attempt only')
    run = ROUND/protocol['experiment']/args.attempt
    run.mkdir(parents=True, exist_ok=False)
    row.update(status='running', execution='RUNNING', started_utc=R.utcnow())
    registry['no_active_experiments'] = False
    R.write_json(registry_path, registry)
    start_cpu, start_wall = cpu(), time.monotonic()
    prior_cpu = sum(float(x.get('cpu_seconds', 0)) for x in registry['experiments'])
    observed = {}
    manifest, prepared, statistics = {}, {}, {}
    attribution = R.provenance()
    provenance = {}
    failure = None
    phase = None
    status = 'EXPLORATORY'
    agreement = False
    artifact_bytes = 0

    def deadline():
        now = datetime.now(timezone.utc)
        if now >= datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('science launch cutoff reached')
        remaining = min(protocol['resources']['cpu_budget_seconds_family']-(cpu()-start_cpu),
                        protocol['resources']['round_cpu_budget_seconds']-prior_cpu-(cpu()-start_cpu))
        if remaining <= 0:
            raise pool.PoolCpuBudgetExceeded('registered CPU budget exhausted')
        return remaining

    def launch(name, specs):
        nonlocal phase, artifact_bytes
        if not specs:
            return []
        phase = name
        remaining = deadline()
        observed[name] = {}
        artifact(run/(name.upper()+'-TASKS.json.gz'), specs)
        def checkpoint(index, item):
            nonlocal artifact_bytes
            ref = artifact(run/name/('task-%05d.json.gz' % index), item)
            artifact_bytes += ref['bytes']
            observed[name][index] = dict(spec=specs[index], item=item, artifact=ref)
            need(artifact_bytes <= protocol['resources']['new_artifact_bytes_cap'], 'new artifact byte cap')
            R.write_json(run/'BUDGET-CHECKPOINT.json', dict(recorded_utc=R.utcnow(), phase=name,
                         parent_and_reaped_cpu_seconds=cpu()-start_cpu,
                         completed={p: len(v) for p, v in observed.items()},
                         scope='pool.py also accounts for live worker CPU'))
            if len(specs) < 16 or len(observed[name]) % 8 == 0 or len(observed[name]) == len(specs):
                print(json.dumps(dict(phase=name, completed=len(observed[name]), total=len(specs),
                                      pool_status=item['status'], status=item.get('result', {}).get('status'))), flush=True)
        pool.run_pool(worker, [(spec,) for spec in specs], workers=pool.worker_count(),
                      timeout=300, rss_gib=4, working_set_gib=1,
                      projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
                      on_result=checkpoint, cpu_budget_seconds=remaining)
        need(len(observed[name]) == len(specs), 'complete pool receipt coverage')
        rows = [observed[name][i] for i in range(len(specs))]
        bad = [r['item'] for r in rows if r['item']['status'] != 'OK']
        if any(r['status'] == 'TIMEOUT' for r in bad):
            raise TimeoutError(name+' execution timeout')
        need(not bad, name+' task errors: '+repr(bad)[:6000])
        need(sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file()) <
             protocol['resources']['result_bytes_cap'], 'total results storage cap')
        return [row['item']['result'] for row in rows]

    try:
        deadline()
        artifact(run/'PREPARATION-MEMORY-PROJECTION.json',
                 pool.project_memory(pool.worker_count(), rss_gib=4, working_set_gib=1))
        for ref in protocol['inputs'].values():
            path = (R.ROOT if ref['path_base'] == 'repository' else R.PKG)/ref['path']
            need(R.sha256(path) == ref['sha256'], 'registered data pin: '+ref['path'])
        RECORDS = S.prepare()
        provenance = S.provenance()
        attribution = provenance['source_attribution']
        if family == 'T1':
            import frame_closure as MODULE
            prepared['closure'] = MODULE.prepare(RECORDS)
        elif family == 'G3':
            import triangles as MODULE
            prepared['triangles'] = MODULE.prepare({k: RECORDS[k] for k in ('base', 'extra')})
        else:
            import interactions as MODULE
            prepared['interactions'] = MODULE.prepare({k: RECORDS[k] for k in ('base', 'extra')})
        manifest = snapshot()
        artifact(run/'IMPLEMENTATION.json', dict(script_sha256=manifest, prepared=prepared,
                 preregistration_sha256=PINS[family], implementation_pins_sha256=R.sha256(implementation_path),
                 source_attribution=attribution, source_provenance=provenance,
                 parent_load_once=True, workers=pool.worker_count(),
                 private_bytecode_namespace=sys.pycache_prefix, frozen_utc=R.utcnow()))
        if family == 'T1':
            controls = launch('closure', [dict(kind='closure', seed=seed) for seed in SEEDS])
            need(all(r['status'] in {'PASS', 'EXPLORATORY'} for r in controls), 'known closure control statuses')
            agreement = scientific(controls[0]) == scientific(controls[1])
            need(agreement, 'second seed complete closure scientific equality')
            statistics = dict(controls=controls, fixed_graph_only=True, cost_optimality_claim=False,
                              intrinsic_rank_laplacian_claim=False)
            status = 'PASS' if all(r['status'] == 'PASS' for r in controls) else 'EXPLORATORY'
        else:
            controls = launch('controls', [dict(kind='algebra_control', seed=seed) for seed in SEEDS]+
                              [dict(kind='baseline', provider=p, seed=seed) for seed in SEEDS for p in ('base', 'extra')])
            need(all(r['status'] == 'PASS' for r in controls), 'all algebra and baseline controls must pass')
            census = launch('census', [dict(kind='census', provider=p, seed=seed)
                                      for seed in SEEDS for p in ('base', 'extra')])
            by_census = {(r['provider'], r['seed']): r for r in census}
            selected = {}
            coverage = {}
            for provider in ('base', 'extra'):
                one, two = (by_census[provider, seed] for seed in SEEDS)
                need(one['complete'] and two['complete'], 'complete registered scalar census')
                need(one['candidates'] == two['candidates'] and one['counts'] == two['counts'],
                     'two-seed exact candidate and rejection census')
                selected[provider] = one['candidates'][:128]
                coverage[provider] = dict(counts=one['counts'], candidates=len(one['candidates']),
                                          selected=len(selected[provider]), unpriced=max(0, len(one['candidates'])-128))
            artifact(run/'COVERAGE.json', coverage)
            price_specs = [dict(kind='price', provider=p, seed=seed, candidate=c,
                                output_dir=str(run/('seed-'+str(seed))/'words'/p/c['candidate_id']),
                                solver_timeout=300)
                           for p in ('base', 'extra') for c in selected[p] for seed in SEEDS]
            prices = launch('price', price_specs)
            by_price = {(r['provider'], r['candidate_id'], r['seed']): r for r in prices}
            favorable, unresolved = [], []
            for provider in ('base', 'extra'):
                for candidate in selected[provider]:
                    cid = candidate['candidate_id']
                    one, two = (by_price[provider, cid, seed] for seed in SEEDS)
                    for key in ('status', 'local_profile', 'width_inventory', 'moment_delta'):
                        need(one.get(key) == two.get(key), 'two-seed price agreement: '+key)
                    need(one['status'] in {'PASS_CANDIDATE', 'REJECTED_GUARD', 'NO_GAIN', 'EXPLORATORY'}, 'known price status')
                    if one['status'] == 'EXPLORATORY':
                        unresolved.append(dict(provider=provider, candidate_id=cid))
                    if one['status'] == 'PASS_CANDIDATE':
                        need(Q(one['moment_delta']['upper']) < 0, 'strict exact favorable upper delta')
                        favorable.append((Q(one['moment_delta']['upper']), provider, cid))
            canonical_order = {(p, candidate['candidate_id']): index
                               for p in ('base', 'extra')
                               for index, candidate in enumerate(selected[p])}
            favorable.sort(key=lambda value: (value[0], value[1],
                                              canonical_order[value[1], value[2]]))
            retained = []
            for provider in ('base', 'extra'):
                retained += [x for x in favorable if x[1] == provider][:4]
            validations = launch('validation', [dict(kind='validation', seed=seed, provider=p, candidate_id=cid,
                word=by_price[p, cid, seed]['word']) for _, p, cid in retained for seed in SEEDS])
            need(all(r['status'] == 'PASS' for r in validations), 'all retained local audits and negative controls pass')
            for _, provider, cid in retained:
                pair = [r for r in validations if r['provider'] == provider and r['candidate_id'] == cid]
                need(len(pair) == 2 and pair[0]['audit']['word_semantic_sha256'] == pair[1]['audit']['word_semantic_sha256'],
                     'identical retained words both seeds')
            agreement = True
            status = 'EXPLORATORY' if favorable or unresolved or any(c['unpriced'] for c in coverage.values()) else 'NULL'
            statistics = dict(coverage=coverage, controls=controls,
                              priced_candidates=len(prices)//2, favorable=len(favorable),
                              retained=[dict(provider=p, candidate_id=cid, moment_delta_upper=str(delta)) for delta, p, cid in retained],
                              unresolved=unresolved, local_validation_receipts=len(validations),
                              fresh_native='UNRUN_REQUIRED_FOR_CHANGED_WORD', full_supplier_outer='UNRUN_REQUIRED',
                              scope=('Single <=16-event contractions with registered certified-surrogate frame assignment; not an all-frame optimum or global word obstruction.'
                                     if family == 'G3' else
                                     'Compatible G3 pairs and one canonical maximal batch, each with one joint certified-surrogate refit; superseded2957 source diagnostic only, not a current frontier claim or all-frame optimum.'))
        phase = None
        need(datetime.now(timezone.utc) < datetime.fromisoformat(protocol['hard_stop_utc']), 'round checkpoint')
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()[-12000:])
        status = 'TIMEOUT' if isinstance(error, (TimeoutError, pool.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsed_cpu, elapsed_wall = cpu()-start_cpu, time.monotonic()-start_wall
    saved = [x for phase_rows in observed.values() for x in phase_rows.values()]
    overhead = max(0, elapsed_cpu-sum(x['item'].get('cpu_seconds') or 0 for x in saved))
    confirmed = failure is None and agreement and status in {'PASS', 'NULL'}
    result_refs = []
    for index, seed in enumerate(SEEDS):
        mine = [x for x in saved if x['spec']['seed'] == seed]
        result = dict(schema_version=1, experiment=protocol['experiment'], milestone=protocol['milestone'],
            seed=seed, status=status, confirmed=confirmed, scientific_decision_agreement=agreement,
            recorded_utc=R.utcnow(), preregistration_sha256=PINS[family],
            implementation_pins_sha256=R.sha256(implementation_path), script_sha256=manifest,
            script_manifest_sha256=digest(manifest), source_attribution=attribution,
            source_provenance=provenance,
            word_blob_ids={p['path']: p.get('git_blob') for p in attribution}, inputs=protocol['inputs'],
            cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine)+(overhead if index == 0 else 0),
            wall_seconds=elapsed_wall, peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine), default=0),
            statistics=statistics, task_receipts=[x['artifact'] for x in mine],
            n_permutations=0, null_summary=dict(model='exact finite registered protocol', mean=None, sd=None, empirical_p=None),
            decision=dict(verdict=status, pass_bar=protocol['pass_bar'], null_bar=protocol['null_bar']),
            failure=failure, incomplete_phase=phase, confirmation_required=True,
            no_kappa_claim=True, prior_stopped_protocols_unchanged=True)
        result_refs.append(artifact(run/('seed-'+str(seed))/'RESULT.json', result))
    attempts = row.get('attempts', [])
    attempts.append(dict(attempt=args.attempt, status=status, cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall,
                         result_files=[r['path'] for r in result_refs]))
    row.update(status=status, execution='COMPLETED' if failure is None else 'INCOMPLETE', confirmed=confirmed,
               scientific_decision_agreement=agreement, cpu_seconds=sum(a['cpu_seconds'] for a in attempts),
               wall_seconds=sum(a['wall_seconds'] for a in attempts), attempts=attempts,
               result_files=[r['path'] for r in result_refs], updated_utc=R.utcnow())
    registry['no_active_experiments'] = True
    registry['status'] = 'ROUND_CHECKS_PENDING'
    if family == 'G4':
        lane = registry['lane_status']['constructive-word']
        lane.update(latest_experiment=protocol['experiment'],
                    consecutive_confirmed_nulls=2 if confirmed and status == 'NULL' else 0,
                    stopped=confirmed and status == 'NULL',
                    scope='No additional scientific family this round; two confirmed nulls stop the word lane.')
    R.write_json(registry_path, registry)
    artifact(run/'RUN.json', dict(status=status, confirmed=confirmed, scientific_decision_agreement=agreement,
             total_cpu_seconds=elapsed_cpu, total_wall_seconds=elapsed_wall, failure=failure,
             incomplete_phase=phase, statistics=statistics, results=result_refs,
             completed_by_phase={p: len(v) for p, v in observed.items()},
             workers=pool.worker_count(), prior_round_cpu_seconds=prior_cpu,
             source_implementation_sha256=R.sha256(run/'IMPLEMENTATION.json') if (run/'IMPLEMENTATION.json').exists() else None))
    print(json.dumps(dict(experiment=protocol['experiment'], status=status, confirmed=confirmed,
                          cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall, failure=failure)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
