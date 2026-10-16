"""Registered continuation04 fixed-exterior expansion screen; all scientific tasks use pool.py.

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
import random
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
import source2966 as S
import admission as A

ROUND = R.RESULTS/'CONTINUATION-04'
SEEDS = (31081, 62039)
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
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--attempt', default='v1')
    args = parser.parse_args()
    need(args.attempt.startswith('v') and args.attempt[1:].isdigit(), 'canonical attempt')
    preg = ROUND/'E2'/'PREREGISTRATION.json'
    protocol = json.loads(preg.read_text())
    preg_sha = R.sha256(preg)
    need(preg_sha == args.registration_sha256 and protocol['state'] == 'FROZEN', 'frozen registration')
    need(tuple(protocol['seeds']) == SEEDS, 'registered distinct seeds')
    need(sys.flags.isolated and not sys.flags.optimize, 'isolated Python; assertions enabled')
    need(sys.pycache_prefix is not None and not Path(sys.pycache_prefix).exists(), 'unused bytecode namespace')
    implementation_path = ROUND/'E2'/('IMPLEMENTATION-PINS-'+args.attempt+'.json')
    implementation = json.loads(implementation_path.read_text())
    for path, sha in implementation['sha256'].items():
        need(R.sha256(R.ROOT/path) == sha, 'pre-execution implementation pin: '+path)
    registry_path = ROUND/'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(x for x in registry['experiments'] if x['id'] == protocol['experiment'])
    need(registry['no_active_experiments'], 'one scientific pool at a time')
    need(row['status'] == 'planned' or row.get('execution') == 'INCOMPLETE', 'new or repaired attempt only')
    run = ROUND/protocol['experiment']/args.attempt
    run.mkdir(parents=True, exist_ok=False)
    row.update(status='running', execution='RUNNING', started_utc=R.utcnow())
    registry['no_active_experiments'] = False
    R.write_json(registry_path, registry)
    start_cpu, start_wall = cpu(), time.monotonic()
    prior_cpu = sum(float(x.get('cpu_seconds', 0)) for x in registry['experiments'])
    observed, manifest, prepared, statistics, provenance = {}, {}, {}, {}, {}
    attribution = R.provenance()
    failure, phase, agreement, status, artifact_bytes = None, None, False, 'EXPLORATORY', 0

    def deadline():
        if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered scientific launch cutoff')
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
            need(artifact_bytes <= protocol['resources']['new_artifact_bytes_cap'], 'new artifact cap')
            R.write_json(run/'BUDGET-CHECKPOINT.json', dict(recorded_utc=R.utcnow(), phase=name,
                         parent_and_reaped_cpu_seconds=cpu()-start_cpu,
                         completed={p:len(v) for p,v in observed.items()},
                         scope='pool.py also accounts for live worker CPU'))
            if len(specs) < 16 or len(observed[name]) % 64 == 0 or len(observed[name]) == len(specs):
                print(json.dumps(dict(phase=name, completed=len(observed[name]), total=len(specs),
                    pool_status=item['status'], status=item.get('result', {}).get('status'))), flush=True)
        pool.run_pool(worker, [(s,) for s in specs], workers=pool.worker_count(), timeout=300,
                      rss_gib=4, working_set_gib=1,
                      projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
                      on_result=checkpoint, cpu_budget_seconds=remaining)
        need(len(observed[name]) == len(specs), 'complete pool receipt coverage')
        rows = [observed[name][i] for i in range(len(specs))]
        bad = [r['item'] for r in rows if r['item']['status'] != 'OK']
        if any(x['status'] == 'TIMEOUT' for x in bad):
            raise TimeoutError(name+' execution timeout')
        need(not bad, name+' task errors: '+repr(bad)[:6000])
        need(sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file()) <
             protocol['resources']['result_bytes_cap'], 'total results storage cap')
        return [x['item']['result'] for x in rows]

    try:
        deadline()
        artifact(run/'PREPARATION-MEMORY-PROJECTION.json',
                 pool.project_memory(pool.worker_count(), rss_gib=4, working_set_gib=1))
        for ref in protocol['inputs'].values():
            path = (R.ROOT if ref['path_base'] == 'repository' else R.PKG)/ref['path']
            need(R.sha256(path) == ref['sha256'], 'registered source data pin: '+ref['path'])
        RECORDS = S.prepare()
        provenance = S.provenance()
        attribution = provenance['source_attribution']
        import expansions_other as MODULE
        prepared = MODULE.prepare(RECORDS, Q(protocol['cost']['endpoint']),
            {int(k):v for k,v in protocol['source_profile'].items()},
            {int(k):v for k,v in protocol['source_inventory'].items()})
        manifest = snapshot()
        artifact(run/'IMPLEMENTATION.json', dict(script_sha256=manifest, prepared=prepared,
            preregistration_sha256=preg_sha, implementation_pins_sha256=R.sha256(implementation_path),
            source_attribution=attribution, source_provenance=provenance, parent_load_once=True,
            workers=pool.worker_count(), private_bytecode_namespace=sys.pycache_prefix, frozen_utc=R.utcnow()))
        controls = launch('controls', [dict(kind='algebra_control', seed=seed) for seed in SEEDS] +
            [dict(kind='baseline', provider=p, seed=seed) for seed in SEEDS for p in ('base','extra')])
        need(all(x['status'] == 'PASS' for x in controls), 'all algebra and baseline controls pass')
        need(scientific(controls[0]) == scientific(controls[1]), 'two-seed algebra control agreement')
        for provider in ('base', 'extra'):
            baseline = [x for x in controls if x.get('provider') == provider]
            need(len(baseline) == 2 and scientific(baseline[0]) == scientific(baseline[1]),
                 'two-seed complete source baseline agreement: '+provider)
        census = launch('census', [dict(kind='census', provider=p, seed=s)
            for s in SEEDS for p in ('base','extra')])
        by_census = {(x['provider'],x['seed']):x for x in census}
        selected, coverage = {}, {}
        for provider in ('base','extra'):
            one,two = (by_census[provider,s] for s in SEEDS)
            need(one['complete'] and two['complete'], 'complete registered finite census')
            need(one['candidates'] == two['candidates'] and one['counts'] == two['counts'], 'census agreement')
            selected[provider] = one['candidates']
            need(len({x['candidate_id'] for x in selected[provider]}) == len(selected[provider]), 'unique candidate IDs')
            coverage[provider] = dict(counts=one['counts'], candidates=len(one['candidates']),
                                      selected=len(one['candidates']), unpriced=0)
        artifact(run/'COVERAGE.json', coverage)
        price_specs = []
        for seed in SEEDS:
            specs = [dict(kind='price', provider=p, seed=seed, candidate=c,
                output_dir=str(run/('seed-'+str(seed))/'words'/p/c['candidate_id']))
                for p in ('base','extra') for c in selected[p]]
            random.Random(seed).shuffle(specs)
            price_specs.extend(specs)
        prices = launch('price', price_specs)
        by_price = {(x['provider'],x['candidate_id'],x['seed']):x for x in prices}
        favorable, unresolved = [], []
        outcomes = Counter()
        for provider in ('base','extra'):
            for candidate in selected[provider]:
                cid = candidate['candidate_id']
                one,two = (by_price[provider,cid,s] for s in SEEDS)
                # Ignore execution timing only; compare all returned scientific facts.
                need(scientific({k:v for k,v in one.items() if k not in {'word','word_artifact'}}) ==
                     scientific({k:v for k,v in two.items() if k not in {'word','word_artifact'}}), 'exact seeded price agreement')
                need(one['status'] in {'PASS_CANDIDATE','REJECTED_GUARD','NO_GAIN','EXPLORATORY'}, 'known price status')
                outcomes[one['status']] += 1
                if one['status'] == 'EXPLORATORY':
                    unresolved.append(dict(provider=provider,candidate_id=cid))
                if one['status'] == 'PASS_CANDIDATE':
                    need(Q(one['moment_delta']['upper']) < 0, 'strict favorable exact moment interval')
                    need(one['word']['sha256'] == two['word']['sha256'], 'identical seeded favorable word bytes')
                    favorable.append((Q(one['moment_delta']['upper']),provider,cid))
        order = {(p,c['candidate_id']):i for p in ('base','extra') for i,c in enumerate(selected[p])}
        favorable.sort(key=lambda x:(x[0],x[1],order[x[1],x[2]]))
        retained = [x for p in ('base','extra') for x in [v for v in favorable if v[1]==p][:4]]
        validations = launch('validation', [dict(kind='validation',seed=s,provider=p,candidate_id=cid,
            word=by_price[p,cid,s]['word']) for _,p,cid in retained for s in SEEDS])
        need(all(x['status'] == 'PASS' for x in validations), 'retained local audits and mutants pass')
        for _,p,cid in retained:
            pair=[x for x in validations if x['provider']==p and x['candidate_id']==cid]
            need(len(pair)==2 and pair[0]['audit']['word_semantic_sha256']==pair[1]['audit']['word_semantic_sha256'],
                 'retained semantic word agreement')
        agreement=True
        status='EXPLORATORY' if favorable or unresolved else 'NULL'
        statistics=dict(coverage=coverage,controls=controls,priced_candidates=len(prices)//2,
            outcomes=dict(outcomes),favorable=len(favorable),
            retained=[dict(provider=p,candidate_id=cid,moment_delta_upper=str(d)) for d,p,cid in retained],
            unresolved=unresolved,local_validation_receipts=len(validations),
            fresh_native='UNRUN_REQUIRED_FOR_CHANGED_WORD',full_supplier_outer='UNRUN_REQUIRED',
            scope=protocol['null_scope'])
        phase=None
        need(datetime.now(timezone.utc)<datetime.fromisoformat(protocol['hard_stop_utc']), 'round checkpoint')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()[-12000:])
        status='TIMEOUT' if isinstance(error,(TimeoutError,pool.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsed_cpu,elapsed_wall=cpu()-start_cpu,time.monotonic()-start_wall
    saved=[x for rows in observed.values() for x in rows.values()]
    overhead=max(0,elapsed_cpu-sum(x['item'].get('cpu_seconds') or 0 for x in saved))
    confirmed=failure is None and agreement and status in {'PASS','NULL'}
    refs=[]
    for index,seed in enumerate(SEEDS):
        mine=[x for x in saved if x['spec']['seed']==seed]
        result=dict(schema_version=1,experiment=protocol['experiment'],milestone=protocol['milestone'],
            seed=seed,status=status,confirmed=confirmed,scientific_decision_agreement=agreement,recorded_utc=R.utcnow(),
            preregistration_sha256=preg_sha,implementation_pins_sha256=R.sha256(implementation_path),
            script_sha256=manifest,script_manifest_sha256=digest(manifest),source_attribution=attribution,
            source_provenance=provenance,word_blob_ids={p['path']:p.get('git_blob') for p in attribution},
            inputs=protocol['inputs'],cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine)+(overhead if index==0 else 0),
            wall_seconds=elapsed_wall,peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine),default=0),
            statistics=statistics,task_receipts=[x['artifact'] for x in mine],n_permutations=0,
            null_summary=dict(model='exact finite fixed-exterior registered construction',mean=None,sd=None,empirical_p=None),
            decision=dict(verdict=status,pass_bar=protocol['pass_bar'],null_bar=protocol['null_bar']),
            failure=failure,incomplete_phase=phase,confirmation_required=True,no_kappa_claim=True,
            prior_stopped_protocols_unchanged=True)
        refs.append(artifact(run/('seed-'+str(seed))/'RESULT.json',result))
    attempts=row.get('attempts',[])
    attempts.append(dict(attempt=args.attempt,status=status,cpu_seconds=elapsed_cpu,wall_seconds=elapsed_wall,
                         result_files=[x['path'] for x in refs]))
    row.update(status=status,execution='COMPLETED' if failure is None else 'INCOMPLETE',confirmed=confirmed,
        scientific_decision_agreement=agreement,cpu_seconds=sum(x['cpu_seconds'] for x in attempts),
        wall_seconds=sum(x['wall_seconds'] for x in attempts),attempts=attempts,
        result_files=[x['path'] for x in refs],updated_utc=R.utcnow())
    registry['no_active_experiments']=True
    registry['status']='ROUND_CHECKS_PENDING'
    previous = next(x for x in registry['experiments'] if x['id'] == 'E1-ADJACENT-EXPANSIONS')
    nulls = (int(previous.get('confirmed') and previous['status']=='NULL') + 1) if confirmed and status=='NULL' else 0
    registry['lane_status']={'fixed_exterior_expansions':dict(consecutive_confirmed_nulls=nulls,
        stopped=nulls>=2,scope='Two consecutive confirmed NULLs stop this lane for the round; all earlier stops remain in force.')}
    R.write_json(registry_path,registry)
    artifact(run/'RUN.json',dict(status=status,confirmed=confirmed,scientific_decision_agreement=agreement,
        total_cpu_seconds=elapsed_cpu,total_wall_seconds=elapsed_wall,failure=failure,incomplete_phase=phase,
        statistics=statistics,results=refs,completed_by_phase={p:len(v) for p,v in observed.items()},
        workers=pool.worker_count(),prior_round_cpu_seconds=prior_cpu,
        source_implementation_sha256=R.sha256(run/'IMPLEMENTATION.json') if (run/'IMPLEMENTATION.json').exists() else None))
    print(json.dumps(dict(experiment=protocol['experiment'],status=status,confirmed=confirmed,
                         cpu_seconds=elapsed_cpu,wall_seconds=elapsed_wall,failure=failure)),flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()


