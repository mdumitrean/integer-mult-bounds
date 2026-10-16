"""Unblinded out-of-cohort source check with a fixed training cohort and frozen ridge."""
from datetime import datetime,timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import math
import os
import statistics
import sys
import time
import traceback

sys.dont_write_bytecode=True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
HERE=Path(__file__).resolve().parent
PKG=HERE.parents[1];ROOT=PKG.parents[1];ROUND=PKG/'results/CONTINUATION-07'
SEEDS=(37003,74017)
F=M=P=U=H=None

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def clean(value):
    if isinstance(value,list):return [clean(v) for v in value]
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if k not in
        {'seed','cpu_seconds','wall_seconds','elapsed_seconds','seconds','recorded_utc'}}
    return value

def worker(spec):
    if spec['kind']=='feature_controls':return F.controls_task(spec['seed'])
    if spec['kind']=='feature':return F.task(spec)
    if spec['kind']=='model_controls':return M.controls_task(spec['seed'])
    if spec['kind']=='prediction':return prediction_task(spec)
    raise ValueError(spec['kind'])


def prediction_task(spec):
    started=time.process_time()
    state=M._state();np=M._numpy()
    need(H is not None,'parent-installed heldout feature row')
    model=M._fit(state['X'],state['y'])
    value=float(M._predict(model,np.asarray([H['features']],dtype=float))[0])
    target=H['target'];comparison=None
    if target is not None:
        truth=target['log10_gain'];baseline=model['intercept']
        def ratio(log_value):
            try:return 10.0**(log_value-truth)
            except OverflowError:return None
        comparison=dict(observed_log10_gain=truth,predicted_log10_gain=value,
            training_mean_log10_gain=baseline,squared_log_error=(truth-value)**2,
            baseline_squared_log_error=(truth-baseline)**2,
            predicted_to_actual_gain_ratio=ratio(value),
            predicted_log10_gain_ratio=value-truth,
            within_factor_two=abs(value-truth)<=math.log10(2),
            baseline_to_actual_gain_ratio=ratio(baseline),
            baseline_log10_gain_ratio=baseline-truth,
            baseline_within_factor_two=abs(baseline-truth)<=math.log10(2),
            factor_two_scope='Fixed unblinded diagnostic only; no pattern, lane or promotion decision.',
            exact_parent_gain=target['gain'],exact_kappa_before=target['before'],
            exact_kappa_after=target['after'])
    return dict(status='PASS_UNBLINDED_FROZEN_PREDICTION' if target is not None else 'EXPLORATORY_CENSORED_TARGET',
        seed=int(spec['seed']),release_id=H['release_id'],parent_pr=H['parent_pr'],
        training_release_ids=[r['release_id'] for r in state['eligible']],
        training_rows_sha256=state['summary']['rows_sha256'],
        training_source_attribution=[r['source_attribution'] for r in state['rows']],
        feature_names=list(state['names']),alpha=M.ALPHA,
        train_mean=model['mean'].tolist(),train_scale=model['scale'].tolist(),
        standardized_coefficients=model['beta'].tolist(),intercept=model['intercept'],
        heldout=H,predicted_log10_gain=value,comparison=comparison,
        outcome_known_before_registration=True,blinded_prospective_validation=False,
        related_ancestry=True,model_refitted_on_training_only=True,model_updated_with_heldout=False,
        tuning=False,pattern_claim=False,kappa_claim=False,
        cpu_seconds=time.process_time()-started,
        scope='Unblinded source-bound out-of-cohort diagnostic. This is not PLAN6 heldout pattern validation, independent-lineage evidence, fresh admission or a new construction.')

def main():
    global F,M,P,U,H
    parser=argparse.ArgumentParser();parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--attempt',default='v1');args=parser.parse_args()
    need(sys.flags.isolated and not sys.flags.optimize,'isolated Python, assertions enabled')
    need(sys.pycache_prefix and not Path(sys.pycache_prefix).exists(),'fresh unused bytecode namespace')
    preg=ROUND/'ML3/PREREGISTRATION.json';protocol=json.loads(preg.read_text())
    need(sha(preg)==args.registration_sha256 and protocol['state']=='FROZEN','frozen preregistration')
    pins_path=ROUND/'ML3'/('IMPLEMENTATION-PINS-'+args.attempt+'.json')
    pins=json.loads(pins_path.read_text())['sha256']
    for p,h in pins.items():need(sha(ROOT/p)==h,'implementation pin before imports: '+p)
    need(str(Path(__file__).relative_to(ROOT)) in pins,'runner frozen')
    sys.path[:0]=[str(HERE),str(HERE.parent)]
    import run_ml1 as U
    import release_features_v2 as F
    import release_ml as M
    import pool as P
    write=U.write
    registry_path=ROUND/'EXPERIMENTS.json';registry=json.loads(registry_path.read_text())
    row=next(r for r in registry['experiments'] if r['id']==protocol['experiment'])
    need(registry['no_active_experiments'],'one active scientific pool')
    need(row['status']=='planned' or row.get('execution')=='INCOMPLETE','new or mechanical repair attempt')
    run=ROUND/protocol['experiment']/args.attempt;run.mkdir(parents=True,exist_ok=False)
    row.update(status='running',execution='RUNNING',started_utc=U.now());registry['no_active_experiments']=False
    write(registry_path,registry,False)
    startc,startw=U.cpu(),time.monotonic();prior=sum(r.get('cpu_seconds',0) for r in registry['experiments'])
    observed={};prepared={};stats={};failure=None;status='EXPLORATORY';phase=None;agreement=False
    original=json.loads((PKG/'data/words/PINS.json').read_text())['files']
    attribution=[dict(path=k,**v) for k,v in original.items()]
    cohort={};feature_refs=[]
    def deadline():
        if datetime.now(timezone.utc)>=datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered science launch cutoff')
        remaining=min(protocol['resources']['cpu_budget_seconds_family']-(U.cpu()-startc),
            protocol['resources']['round_cpu_budget_seconds']-prior-(U.cpu()-startc))
        if remaining<=0:raise TimeoutError('registered CPU budget')
        return remaining
    def storage():
        need(sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file())<18000000,'round result cap')
        need(sum(p.stat().st_size for p in (PKG/'results').rglob('*') if p.is_file())<200000000,'global result cap')
    def launch(name,specs):
        nonlocal phase
        phase=name;remaining=deadline();observed[name]={}
        write(run/(name.upper()+'-TASKS.json.gz'),specs)
        def checkpoint(i,item):
            ref=write(run/name/('task-%05d.json.gz'%i),item)
            observed[name][i]=dict(spec=specs[i],item=item,artifact=ref)
            write(run/'BUDGET-CHECKPOINT.json',dict(recorded_utc=U.now(),phase=name,
                parent_and_reaped_cpu_seconds=U.cpu()-startc,completed={k:len(v) for k,v in observed.items()}),False)
            if len(specs)<20 or len(observed[name])%20==0 or len(observed[name])==len(specs):
                print(json.dumps(dict(phase=name,completed=len(observed[name]),total=len(specs),status=item['status'])),flush=True)
        P.run_pool(worker,[(s,) for s in specs],workers=P.worker_count(),timeout=300,rss_gib=4,
            working_set_gib=protocol['resources']['working_set_gib'],
            projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
            on_result=checkpoint,cpu_budget_seconds=remaining)
        items=[observed[name][i]['item'] for i in range(len(specs))]
        if any(x['status']=='TIMEOUT' for x in items):raise TimeoutError(name+' worker timeout')
        need(all(x['status']=='OK' for x in items),name+' errors: '+repr([x for x in items if x['status']!='OK'])[:12000])
        storage();return [x['result'] for x in items]
    try:
        deadline()
        write(run/'PREPARATION-MEMORY-PROJECTION.json',P.project_memory(P.worker_count(),4,protocol['resources']['working_set_gib']))
        for ref in protocol['inputs'].values():need(sha(PKG/ref['path'])==ref['sha256'],'registered source '+ref['path'])
        ref=protocol['inputs']['cohort'];cohort_path=PKG/ref['path'];cohort=json.loads(cohort_path.read_text())
        prepared['features']=F.prepare(cohort_path,cohort_sha256=ref['sha256'])
        for p,h in pins.items():
            archive=ROUND/'SOURCES'/(h+'.py.gz')
            if not archive.exists():
                archive.parent.mkdir(exist_ok=True);archive.write_bytes(gzip.compress((ROOT/p).read_bytes(),mtime=0))
        write(run/'IMPLEMENTATION.json',dict(script_sha256=pins,prepared=prepared,
            frozen_utc=U.now(),parent_load_once=True,source_attribution=attribution,
            preregistration_sha256=sha(preg),implementation_pins_sha256=sha(pins_path)))
        checks=launch('feature_controls',[dict(kind='feature_controls',seed=s) for s in SEEDS])
        need(all(v['status']=='PASS' for v in checks),'feature positive and negative controls pass')
        specs=[]
        for seed in SEEDS:
            specs += [dict(s,kind='feature',seed=seed) for s in F.task_specs(seed)]
        features=launch('features',specs)
        paired={}
        for s,value in zip(specs,features):
            key=(value['pr'],value['provider']);paired.setdefault(key,{})[s['seed']]=value
        need(len(paired)*2==len(features),'exactly two feature receipts per release/provider')
        selected=[]
        for key,values in sorted(paired.items()):
            need(set(values)==set(SEEDS),'two independent confirmation seeds')
            need(clean(values[SEEDS[0]])==clean(values[SEEDS[1]]),'exact repeated paired feature extraction: '+str(key))
            selected.append(values[SEEDS[0]])
        feature_refs.append(write(run/'RELEASE-FEATURES.json.gz',selected))
        training_ref=protocol['inputs']['training_features']
        training_path=PKG/training_ref['path']
        training=json.loads(gzip.decompress(training_path.read_bytes()))
        prepared['model']=M.prepare(dict(rows=training,feature_names=F.FEATURE_NAMES,
            source_attribution=attribution,training_input=training_ref))
        state=M._state()
        need({r['release_id'] for r in state['eligible']}=={'2948','2957','2966'},
             'fixed three training releases from conservative ML2v2 coverage')
        heldout=M._aggregate(selected,state['names'])
        need(len(heldout)==1 and heldout[0]['release_id']=='3015','one fixed3015 source check')
        need(heldout[0]['features'] is not None,'complete heldout structural feature vector')
        H=heldout[0]
        write(run/'MODEL-PREPARATION.json',dict(training=prepared['model'],heldout=H,
            training_features=training_ref,outcome_known_before_registration=True))
        values=launch('predictions',[dict(kind='prediction',seed=s) for s in SEEDS])
        need(all(v['status'] in ('PASS_UNBLINDED_FROZEN_PREDICTION','EXPLORATORY_CENSORED_TARGET')
                 for v in values),'frozen source-check tasks completed')
        need(clean(values[0])==clean(values[1]),'deterministic source check repeated exactly')
        for seed,value in zip(SEEDS,values):
            stats[str(seed)]=dict(prepared_model=prepared['model'],prediction=value,
                feature_table=feature_refs[0],feature_seed_agreement=True,
                observed_model_seed_agreement=True,outcome_known_before_registration=True,
                blinded_prospective_validation=False,pattern_claim=False,kappa_claim=False)
        agreement=True;phase=None
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()[-18000:])
        status='TIMEOUT' if isinstance(error,(TimeoutError,P.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsedc,elapsedw=U.cpu()-startc,time.monotonic()-startw
    saved=[x for phase_rows in observed.values() for x in phase_rows.values()]
    overhead=max(0,elapsedc-sum(x['item'].get('cpu_seconds') or 0 for x in saved));refs=[]
    for i,seed in enumerate(SEEDS):
        mine=[x for x in saved if x['spec']['seed']==seed]
        refs.append(write(run/('seed-'+str(seed))/'RESULT.json',dict(schema_version=1,
            experiment=protocol['experiment'],milestone='CONTINUATION-07/ML3',seed=seed,status=status,
            recorded_utc=U.now(),script_sha256=pins,implementation_pins_sha256=sha(pins_path),
            preregistration_sha256=sha(preg),source_attribution=attribution,
            release_source_attribution=cohort,word_blob_ids={p['path']:p.get('git_blob') for p in attribution},
            inputs=protocol['inputs'],cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine)+(overhead if i==0 else 0),
            wall_seconds=elapsedw,peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine),default=0),
            statistics=stats.get(str(seed)),task_receipts=[x['artifact'] for x in mine],
            n_permutations=sum(x['spec'].get('permutation') is not None for x in mine),
            null_summary=stats.get(str(seed),{}).get('null_summary'),failure=failure,incomplete_phase=phase,
            scientific_decision_agreement=agreement,confirmed=failure is None and agreement,
            decision=dict(verdict=status,bar=protocol['pass_bar'],pattern_claim=False,kappa_claim=False),scope=protocol['scope'])))
    attempts=row.get('attempts',[])+[dict(attempt=args.attempt,status=status,cpu_seconds=elapsedc,
        wall_seconds=elapsedw,result_files=[r['path'] for r in refs])]
    row.update(status=status,execution='COMPLETED' if failure is None else 'INCOMPLETE',attempts=attempts,
        confirmed=failure is None and agreement,result_files=[r['path'] for r in refs],
        cpu_seconds=sum(a['cpu_seconds'] for a in attempts),wall_seconds=sum(a['wall_seconds'] for a in attempts),updated_utc=U.now())
    registry['no_active_experiments']=True;write(registry_path,registry,False)
    write(run/'RUN.json',dict(status=status,confirmed=failure is None and agreement,total_cpu_seconds=elapsedc,
        total_wall_seconds=elapsedw,failure=failure,incomplete_phase=phase,statistics=stats,results=refs,
        completed_by_phase={p:len(v) for p,v in observed.items()},workers=P.worker_count()))
    storage();print(json.dumps(dict(status=status,cpu_seconds=elapsedc,wall_seconds=elapsedw,failure=failure)),flush=True)
    if failure:raise SystemExit(1)

if __name__=='__main__':main()
