"""Registered T370 packing circuit: immutable receipts, exact audits, one pool.

No acquired program is imported. Implementation bytes are checked before any
scientific module import or parent preparation. All scientific workers run via
pipeline/pool.py; no unverified profile proposal is admitted as a kappa result.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as Q
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import random
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
PKG = HERE.parent.parent
ROOT = PKG.parents[1]
ROUND = PKG/'results/CONTINUATION-06'
SEEDS = (28099,63073)
R = pool = S = T = M = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def cpu():
    child = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+child.ru_utime+child.ru_stime


def artifact(path, value):
    raw = canonical(value)
    data = gzip.compress(raw,mtime=0) if path.name.endswith('.gz') else raw
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)
    return dict(path=str(path.relative_to(PKG)),sha256=hashlib.sha256(data).hexdigest(),
                bytes=len(data),payload_sha256=hashlib.sha256(raw).hexdigest())


def scientific(value):
    if isinstance(value,list):
        return [scientific(v) for v in value]
    if isinstance(value,tuple):
        return [scientific(v) for v in value]
    if isinstance(value,dict):
        return {k:scientific(v) for k,v in value.items() if k not in
            {'seed','cpu_seconds','wall_seconds','elapsed_seconds','seconds','recorded_utc','output_dir','schedule'}}
    return value


def profile(value):
    return {int(r):int(n) for r,n in value.items() if n}


def snapshot():
    paths = set((PKG/'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        name = getattr(module,'__file__',None)
        if name:
            path = Path(name).resolve()
            if path.is_relative_to(ROOT/'research') and path.suffix == '.py':
                need(not path.is_relative_to(PKG/'data'),'acquired code must never be imported')
                paths.add(path)
    directory = ROUND/'SOURCES'
    directory.mkdir(exist_ok=True)
    result = {}
    for path in sorted(paths):
        raw = path.read_bytes()
        h = hashlib.sha256(raw).hexdigest()
        result[str(path.relative_to(ROOT))] = h
        target = directory/(h+'.py.gz')
        if target.exists():
            need(gzip.decompress(target.read_bytes()) == raw,'immutable source preimage')
        else:
            with target.open('xb') as handle:
                handle.write(gzip.compress(raw,mtime=0))
    return result


def worker(spec):
    kind = spec['kind']
    if kind == 'transport_controls':
        return T.controls_task(spec['seed'])
    if kind == 'moment_controls':
        return M.controls_task(spec['seed'])
    if kind == 'baseline':
        return S.baseline_task(spec)
    if kind == 'moment':
        return M.assess_task(spec['seed'])
    if kind == 'census':
        return T.census_task(spec['seed'])
    if kind == 'search':
        return T.task(spec)
    if kind == 'materialize':
        return T.materialize_task(spec)
    raise ValueError('unregistered worker kind: '+kind)


def main():
    global R,pool,S,T,M
    parser=argparse.ArgumentParser()
    parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--attempt',default='v1')
    args=parser.parse_args()
    need(args.attempt.startswith('v') and args.attempt[1:].isdigit(),'canonical attempt')
    need(sys.flags.isolated and not sys.flags.optimize,'isolated Python, assertions enabled')
    need(sys.pycache_prefix is not None and not Path(sys.pycache_prefix).exists(),'unused private bytecode namespace')
    preg=ROUND/'P1/PREREGISTRATION.json'
    protocol=json.loads(preg.read_text())
    need(sha(preg)==args.registration_sha256 and protocol['state']=='FROZEN','frozen preregistration')
    need(tuple(protocol['seeds'])==SEEDS,'registered confirmation seeds')
    pins_path=ROUND/'P1'/('IMPLEMENTATION-PINS-'+args.attempt+'.json')
    implementation=json.loads(pins_path.read_text())
    for relative,h in implementation['sha256'].items():
        need(sha(ROOT/relative)==h,'pre-import implementation pin: '+relative)
    need(str(Path(__file__).resolve().relative_to(ROOT)) in implementation['sha256'],'runner is pinned')
    sys.path[:0]=[str(HERE),str(HERE.parent/'continuation'),str(HERE.parent)]
    import records as R
    import pool
    import source_fill as S
    import topple as T
    import moment as M
    registry_path=ROUND/'EXPERIMENTS.json'
    registry=json.loads(registry_path.read_text())
    row=next(x for x in registry['experiments'] if x['id']==protocol['experiment'])
    need(registry['no_active_experiments'],'one scientific pool at a time')
    need(row['status']=='planned' or row.get('execution')=='INCOMPLETE','new or mechanically repaired attempt')
    run=ROUND/protocol['experiment']/args.attempt
    run.mkdir(parents=True,exist_ok=False)
    row.update(status='running',execution='RUNNING',started_utc=R.utcnow())
    registry['no_active_experiments']=False
    R.write_json(registry_path,registry)
    started_cpu,started_wall=cpu(),time.monotonic()
    prior_cpu=sum(float(x.get('cpu_seconds',0)) for x in registry['experiments'])
    observed,manifest,statistics,provenance,prepared={},{},{},{},{}
    attribution=R.provenance()
    failure,phase,agreement,status=None,None,False,'EXPLORATORY'

    def deadline():
        if datetime.now(timezone.utc)>=datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered science launch cutoff')
        remaining=min(protocol['resources']['cpu_budget_seconds_family']-(cpu()-started_cpu),
            protocol['resources']['round_cpu_budget_seconds']-prior_cpu-(cpu()-started_cpu))
        if remaining<=0:
            raise pool.PoolCpuBudgetExceeded('registered CPU budget exhausted')
        return remaining

    def storage():
        used=sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file())
        need(used<=protocol['resources']['new_artifact_bytes_cap'],'round artifact cap')
        total=sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file())
        need(total<protocol['resources']['result_bytes_cap'],'global result artifact cap')

    def launch(name,specs):
        nonlocal phase
        if not specs:
            return []
        phase=name
        remaining=deadline()
        observed[name]={}
        artifact(run/(name.upper()+'-TASKS.json.gz'),specs)
        def checkpoint(index,item):
            ref=artifact(run/name/('task-%05d.json.gz'%index),item)
            observed[name][index]=dict(spec=specs[index],item=item,artifact=ref)
            R.write_json(run/'BUDGET-CHECKPOINT.json',dict(recorded_utc=R.utcnow(),phase=name,
                parent_and_reaped_cpu_seconds=cpu()-started_cpu,
                completed={p:len(v) for p,v in observed.items()},
                scope='pool.py also accounts for live worker CPU'))
            if len(specs)<16 or len(observed[name])%20==0 or len(observed[name])==len(specs):
                print(json.dumps(dict(phase=name,completed=len(observed[name]),total=len(specs),
                    pool_status=item['status'],status=item.get('result',{}).get('status'))),flush=True)
        pool.run_pool(worker,[(s,) for s in specs],workers=pool.worker_count(),timeout=300,
            rss_gib=6,working_set_gib=protocol['resources']['working_set_gib'],
            projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
            on_result=checkpoint,cpu_budget_seconds=remaining)
        need(len(observed[name])==len(specs),'complete pool receipt coverage')
        entries=[observed[name][i] for i in range(len(specs))]
        bad=[x['item'] for x in entries if x['item']['status']!='OK']
        if any(x['status']=='TIMEOUT' for x in bad):
            raise TimeoutError(name+' worker deadline')
        need(not bad,name+' task errors: '+repr(bad)[:6000])
        storage()
        return [x['item']['result'] for x in entries]

    try:
        deadline()
        artifact(run/'PREPARATION-MEMORY-PROJECTION.json',pool.project_memory(pool.worker_count(),
            rss_gib=6,working_set_gib=protocol['resources']['working_set_gib']))
        for ref in protocol['inputs'].values():
            base=ROOT if ref['path_base']=='repository' else PKG
            need(sha(base/ref['path'])==ref['sha256'],'registered input pin: '+ref['path'])
        prepared['source']=S.prepare()
        state=S.get_state()
        provenance=state['source']
        attribution=provenance['source_attribution']
        prepared['transport']=T.prepare(state)
        prepared['moment']=M.prepare(dict(live=331520,calls=3330,copies=5,dimension=73,
            source_attribution=attribution,allocation_evidence=dict(
                source_preparation=prepared['source']['rows_sha256'],scope='unmodified five-copy baseline only; candidate not yet constructed')))
        manifest=snapshot()
        for path,h in manifest.items():
            need(implementation['sha256'].get(path)==h,'all imported/archived scientific source was frozen: '+path)
        artifact(run/'IMPLEMENTATION.json',dict(script_sha256=manifest,prepared=prepared,
            preregistration_sha256=sha(preg),implementation_pins_sha256=sha(pins_path),
            source_attribution=attribution,source_provenance=provenance,parent_load_once=True,
            workers=pool.worker_count(),private_bytecode_namespace=sys.pycache_prefix,frozen_utc=R.utcnow()))
        for name,kind in [('controls','transport_controls'),('moment_controls','moment_controls'),('baseline','baseline')]:
            values=launch(name,[dict(kind=kind,seed=s) for s in SEEDS])
            need(all(x['status']=='PASS' for x in values),name+' controls pass')
            need(scientific(values[0])==scientific(values[1]),name+' exact two-seed agreement')
            statistics[name]=values
        moments=launch('moment',[dict(kind='moment',seed=s) for s in SEEDS])
        need(all(x['status']=='PASS_CONDITIONAL_PROFILE_MOMENT' for x in moments),'conditional exact moment checks')
        need(scientific(moments[0])==scientific(moments[1]),'two-seed moment agreement')
        statistics['conditional_moment']=moments[0]
        census=launch('census',[dict(kind='census',seed=s) for s in SEEDS])
        ordered=[sorted(x['cases'],key=lambda c:c['case_id']) for x in census]
        need(all(x['status']=='PASS' and x['count']==60 for x in census),'complete finite census')
        need(ordered[0]==ordered[1] and census[0]['cases_sha256']==census[1]['cases_sha256'],'census seed agreement')
        selected=ordered[0]
        specs=[]
        for seed in SEEDS:
            mine=[dict(kind='search',seed=seed,case=case,max_seconds=240) for case in selected]
            random.Random(seed).shuffle(mine)
            specs+=mine
        search=launch('search',specs)
        by={(x['case']['case_id'],x['seed']):x for x in search}
        successes,outcomes=[],Counter()
        for case in selected:
            one,two=(by[case['case_id'],s] for s in SEEDS)
            if any(x['status']=='TIMEOUT' or not x['complete'] for x in (one,two)):
                raise TimeoutError('registered constructor case incomplete: '+case['case_id'])
            need(scientific(one)==scientific(two),'exact two-seed transport agreement: '+case['case_id'])
            need(one['status'] in {'PASS','NULL'},'resolved constructor status')
            outcomes[one['outcome']]+=1
            if one['status']=='PASS':
                need(Q(one['witness']['cost']['upper'])<0,'strict exact witness profile gain')
                successes.append(case['case_id'])
        statistics.update(cases=60,search_tasks=len(search),outcomes=dict(outcomes),
            successful_cases=successes,retained_case=successes[0] if successes else None,
            coverage_scope=protocol['null_scope'],all_cases_complete=True)
        validations=[]
        if successes:
            cid=successes[0]
            validations=launch('materialize',[dict(kind='materialize',seed=s,
                witness=by[cid,s]['witness'],output_dir=str(run/('seed-'+str(s))/'candidate')) for s in SEEDS])
            for value in validations:
                need(value['status']=='PASS','complete candidate owner audit')
                need(profile(value['profile'])==profile(moments[0]['complete_profile']),
                    'literal full-profile binding to exact moment certificate')
                need(profile(value['idle'])==profile(moments[0]['aggregate_idle_profile']),
                    'literal aggregate idle binding')
                need(value['audit']['rank_mass']==24082560,'candidate complete rank mass')
                for name in ('fill_artifact','profile_artifact'):
                    ref=value[name]
                    need(sha(PKG/ref['path'])==ref['sha256'],'candidate artifact hash')
            need(validations[0]['fill_artifact']['sha256']==validations[1]['fill_artifact']['sha256'],
                'independently materialized seed fills are byte-identical')
            stripped=[{k:v for k,v in x.items() if k not in {'fill_artifact','profile_artifact'}} for x in validations]
            need(scientific(stripped[0])==scientific(stripped[1]),'complete candidate audit agreement')
        statistics['candidate_validations']=validations
        statistics['full_scaled_admission']='UNRUN_REQUIRED; no nativecache replay or admitted kappa claim'
        status='EXPLORATORY' if successes else 'NULL'
        agreement=True
        phase=None
        need(datetime.now(timezone.utc)<datetime.fromisoformat(protocol['hard_stop_utc']),'round checkpoint')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()[-14000:])
        status='TIMEOUT' if isinstance(error,(TimeoutError,pool.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsed_cpu,elapsed_wall=cpu()-started_cpu,time.monotonic()-started_wall
    saved=[x for phase_rows in observed.values() for x in phase_rows.values()]
    overhead=max(0,elapsed_cpu-sum(x['item'].get('cpu_seconds') or 0 for x in saved))
    confirmed=failure is None and agreement
    refs=[]
    for index,seed in enumerate(SEEDS):
        mine=[x for x in saved if x['spec']['seed']==seed]
        result=dict(schema_version=1,experiment=protocol['experiment'],milestone=protocol['milestone'],
            seed=seed,status=status,confirmed=confirmed,scientific_decision_agreement=agreement,
            recorded_utc=R.utcnow(),preregistration_sha256=sha(preg),implementation_pins_sha256=sha(pins_path),
            script_sha256=manifest,script_manifest_sha256=digest(manifest),source_attribution=attribution,
            source_provenance=provenance,word_blob_ids={p['path']:p.get('git_blob') for p in attribution},
            inputs=protocol['inputs'],cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine)+(overhead if index==0 else 0),
            wall_seconds=elapsed_wall,peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine),default=0),
            statistics=statistics,task_receipts=[x['artifact'] for x in mine],n_permutations=0,
            null_summary=dict(model='exact finite registered55-bin packing constructor',mean=None,sd=None,empirical_p=None),
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
    registry['lane_status']={'packing_topple':dict(consecutive_confirmed_nulls=int(confirmed and status=='NULL'),
        stopped=False,scope=protocol['null_scope'])}
    R.write_json(registry_path,registry)
    artifact(run/'RUN.json',dict(status=status,confirmed=confirmed,scientific_decision_agreement=agreement,
        total_cpu_seconds=elapsed_cpu,total_wall_seconds=elapsed_wall,failure=failure,incomplete_phase=phase,
        statistics=statistics,results=refs,completed_by_phase={p:len(v) for p,v in observed.items()},
        workers=pool.worker_count(),prior_round_cpu_seconds=prior_cpu,
        source_implementation_sha256=sha(run/'IMPLEMENTATION.json') if (run/'IMPLEMENTATION.json').exists() else None))
    storage()
    print(json.dumps(dict(experiment=protocol['experiment'],status=status,confirmed=confirmed,
        cpu_seconds=elapsed_cpu,wall_seconds=elapsed_wall,failure=failure)),flush=True)
    if failure:
        raise SystemExit(1)


if __name__=='__main__':
    main()
