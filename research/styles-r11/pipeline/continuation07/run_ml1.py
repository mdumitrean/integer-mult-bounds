"""Frozen retrospective controls, historical interactions and blocked models."""
from datetime import datetime, timezone
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import resource
import statistics
import sys
import time
import traceback

sys.dont_write_bytecode=True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key]='1'
HERE=Path(__file__).resolve().parent
PKG=HERE.parents[1]
ROOT=PKG.parents[1]
ROUND=PKG/'results/CONTINUATION-07'
SEEDS=(37003,74017)
D=H=L=P=None

def need(ok,message):
    if not ok:raise ValueError(message)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def now():return datetime.now(timezone.utc).isoformat()

def cpu():
    r=resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+r.ru_utime+r.ru_stime

def write(path,value,immutable=True):
    raw=(json.dumps(value,sort_keys=True,allow_nan=False,separators=(',',':'))+'\n').encode()
    packed=gzip.compress(raw,mtime=0) if path.name.endswith('.gz') else raw
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb' if immutable else 'wb') as f:f.write(packed)
    return dict(path=str(path.relative_to(PKG)),sha256=sha(path),bytes=len(packed),payload_sha256=hashlib.sha256(raw).hexdigest())

def worker(spec):
    kind=spec['kind'];seed=spec['seed']
    if kind=='dataset':return D.audit_task(seed)
    if kind=='history_controls':return H.controls_task(seed)
    if kind=='history':return H.analysis_task(seed)
    if kind=='model_controls':return L.controls_task(seed)
    if kind=='model':return L.evaluate_task(spec)
    raise ValueError(kind)

def main():
    global D,H,L,P
    parser=argparse.ArgumentParser();parser.add_argument('--registration-sha256',required=True)
    parser.add_argument('--attempt',default='v1');args=parser.parse_args()
    need(sys.flags.isolated and not sys.flags.optimize,'isolated Python with assertions')
    need(sys.pycache_prefix and not Path(sys.pycache_prefix).exists(),'fresh unused bytecode namespace')
    preg=ROUND/'ML1/PREREGISTRATION.json';protocol=json.loads(preg.read_text())
    need(sha(preg)==args.registration_sha256 and protocol['state']=='FROZEN','frozen preregistration')
    pins_path=ROUND/'ML1'/('IMPLEMENTATION-PINS-'+args.attempt+'.json')
    pins=json.loads(pins_path.read_text())['sha256']
    for p,h in pins.items():need(sha(ROOT/p)==h,'implementation before import: '+p)
    need(str(Path(__file__).relative_to(ROOT)) in pins,'runner frozen')
    sys.path[:0]=[str(HERE),str(HERE.parent)]
    import dataset as D
    import history as H
    import learner as L
    import pool as P
    registry_path=ROUND/'EXPERIMENTS.json';registry=json.loads(registry_path.read_text())
    row=next(r for r in registry['experiments'] if r['id']==protocol['experiment'])
    need(registry['no_active_experiments'],'one pool')
    need(row['status']=='planned' or row.get('execution')=='INCOMPLETE','new or mechanical repair attempt')
    run=ROUND/protocol['experiment']/args.attempt;run.mkdir(parents=True,exist_ok=False)
    row.update(status='running',execution='RUNNING',started_utc=now());registry['no_active_experiments']=False
    write(registry_path,registry,False)
    startc,startw=cpu(),time.monotonic();prior=sum(r.get('cpu_seconds',0) for r in registry['experiments'])
    observed={};prepared={};stats={};failure=None;status='EXPLORATORY';phase=None
    original=json.loads((PKG/'data/words/PINS.json').read_text())['files']
    attribution=[dict(path=k,**v) for k,v in original.items()]
    def deadline():
        if datetime.now(timezone.utc)>=datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('science launch cutoff')
        remaining=min(protocol['resources']['cpu_budget_seconds_family']-(cpu()-startc),
            protocol['resources']['round_cpu_budget_seconds']-prior-(cpu()-startc))
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
            write(run/'BUDGET-CHECKPOINT.json',dict(recorded_utc=now(),phase=name,
                parent_and_reaped_cpu_seconds=cpu()-startc,completed={k:len(v) for k,v in observed.items()}),False)
            if len(specs)<20 or len(observed[name])%40==0 or len(observed[name])==len(specs):
                print(json.dumps(dict(phase=name,completed=len(observed[name]),total=len(specs),status=item['status'])),flush=True)
        P.run_pool(worker,[(s,) for s in specs],workers=P.worker_count(),timeout=300,rss_gib=4,
            working_set_gib=0.65,projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
            on_result=checkpoint,cpu_budget_seconds=remaining)
        items=[observed[name][i]['item'] for i in range(len(specs))]
        if any(x['status']=='TIMEOUT' for x in items):raise TimeoutError(name+' worker timeout')
        need(all(x['status']=='OK' for x in items),name+' errors: '+repr([x for x in items if x['status']!='OK'])[:12000])
        storage();return [x['result'] for x in items]
    try:
        deadline()
        write(run/'PREPARATION-MEMORY-PROJECTION.json',P.project_memory(P.worker_count(),4,0.65))
        for ref in protocol['inputs'].values():need(sha(PKG/ref['path'])==ref['sha256'],'registered source '+ref['path'])
        prepared['dataset']=D.prepare();prepared['history']=H.prepare()
        rows=D.get_rows();prepared['learner']=L.prepare(rows,prepared['dataset'])
        attribution=prepared['dataset']['source_attribution']
        table=write(run/'HISTORICAL-ROWS.json.gz',rows)
        history_table=write(run/'PRICE-ROWS.json.gz',H.get_rows())
        write(run/'IMPLEMENTATION.json',dict(script_sha256=pins,prepared=prepared,table=table,history_table=history_table,
            source_attribution=attribution,preregistration_sha256=sha(preg),implementation_pins_sha256=sha(pins_path)))
        for p,h in pins.items():
            archive=ROUND/'SOURCES'/(h+'.py.gz')
            if not archive.exists():
                archive.parent.mkdir(exist_ok=True);archive.write_bytes(gzip.compress((ROOT/p).read_bytes(),mtime=0))
        checks=launch('controls',[dict(kind=k,seed=s) for s in SEEDS for k in ('dataset','history_controls','model_controls')])
        need(all(v['status']=='PASS' for v in checks),'all mechanical controls pass')
        histories=launch('history',[dict(kind='history',seed=s) for s in SEEDS])
        need(histories[0]['rows_sha256']==histories[1]['rows_sha256'],'two-seed source arithmetic agreement')
        values=launch('observed',[dict(kind='model',seed=s,target=t,permutation=None)
            for s in SEEDS for t in ('frame_legal','worse')])
        need(all(v['status']=='PASS_RETROSPECTIVE_MODEL' for v in values),'all grouped model folds assessable')
        nulls=launch('permutations',[dict(kind='model',seed=s,target='frame_legal',permutation=i)
            for s in SEEDS for i in range(protocol['n_permutations'])])
        need(all(v['status']=='PASS_RETROSPECTIVE_MODEL' for v in nulls),'complete fixed permutation family')
        for seed in SEEDS:
            primary=next(v for v in values if v['seed']==seed and v['target']=='frame_legal')
            secondary=next(v for v in values if v['seed']==seed and v['target']=='worse')
            samples=[v['delta_auroc'] for v in nulls if v['seed']==seed]
            p=(1+sum(v>=primary['delta_auroc'] for v in samples))/(len(samples)+1)
            lead=primary['delta_auroc']>=0.05 and primary['delta_balanced_log_loss']>=0.01 and p<=0.01
            stats[str(seed)]=dict(primary={k:v for k,v in primary.items() if k!='out_of_fold'},
                secondary={k:v for k,v in secondary.items() if k!='out_of_fold'},
                null_summary=dict(model='whole original-pair label vectors, exact proposal coefficient strata',
                    n=len(samples),mean=statistics.mean(samples),sd=statistics.pstdev(samples),empirical_p=p,
                    minimum=min(samples),maximum=max(samples)),diagnostic_bar_met=lead,
                historical_interactions=histories[0]['same_W_interactions'],
                history_cross_W_additive=histories[0]['all_cross_W_unions_additive'])
        phase=None
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()[-16000:])
        status='TIMEOUT' if isinstance(error,(TimeoutError,P.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsedc,elapsedw=cpu()-startc,time.monotonic()-startw
    saved=[x for phase_rows in observed.values() for x in phase_rows.values()]
    overhead=max(0,elapsedc-sum(x['item'].get('cpu_seconds') or 0 for x in saved))
    agreement=failure is None and stats[str(SEEDS[0])]['diagnostic_bar_met']==stats[str(SEEDS[1])]['diagnostic_bar_met']
    refs=[]
    for i,seed in enumerate(SEEDS):
        mine=[x for x in saved if x['spec']['seed']==seed]
        refs.append(write(run/('seed-'+str(seed))/'RESULT.json',dict(schema_version=1,
            experiment=protocol['experiment'],milestone='CONTINUATION-07/ML1',seed=seed,status=status,
            recorded_utc=now(),script_sha256=pins,implementation_pins_sha256=sha(pins_path),
            preregistration_sha256=sha(preg),source_attribution=attribution,
            historical_price_attribution=prepared.get('history',{}).get('source_attribution'),
            word_blob_ids={p['path']:p.get('git_blob') for p in attribution},inputs=protocol['inputs'],
            cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine)+(overhead if i==0 else 0),
            wall_seconds=elapsedw,peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine),default=0),
            statistics=stats.get(str(seed)),task_receipts=[x['artifact'] for x in mine],
            n_permutations=sum(x['spec'].get('permutation') is not None for x in mine),
            null_summary=stats.get(str(seed),{}).get('null_summary'),failure=failure,incomplete_phase=phase,
            scientific_decision_agreement=agreement,confirmed=failure is None and agreement,
            decision=dict(verdict=status,bar=protocol['pass_bar'],pattern_claim=False,kappa_claim=False),
            scope=protocol['scope'])))
    attempts=row.get('attempts',[])+[dict(attempt=args.attempt,status=status,cpu_seconds=elapsedc,
        wall_seconds=elapsedw,result_files=[r['path'] for r in refs])]
    row.update(status=status,execution='COMPLETED' if failure is None else 'INCOMPLETE',attempts=attempts,
        confirmed=failure is None and agreement,result_files=[r['path'] for r in refs],
        cpu_seconds=sum(a['cpu_seconds'] for a in attempts),wall_seconds=sum(a['wall_seconds'] for a in attempts),updated_utc=now())
    registry['no_active_experiments']=True;write(registry_path,registry,False)
    write(run/'RUN.json',dict(status=status,confirmed=failure is None and agreement,total_cpu_seconds=elapsedc,
        total_wall_seconds=elapsedw,failure=failure,incomplete_phase=phase,statistics=stats,results=refs,
        completed_by_phase={p:len(v) for p,v in observed.items()},workers=P.worker_count()))
    storage()
    print(json.dumps(dict(status=status,cpu_seconds=elapsedc,wall_seconds=elapsedw,failure=failure)),flush=True)
    if failure:raise SystemExit(1)

if __name__=='__main__':main()
