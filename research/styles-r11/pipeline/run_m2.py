#!/usr/bin/env python3
"""Frozen M2 audits and bounded confluence tasks with exact seed bookkeeping."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback
sys.dont_write_bytecode=True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key]='1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import records as R
import pool
import run_m0
import fill
import sandpile as S
SEEDS=(11031,29063)


class BudgetExhausted(Exception): pass


def row(experiment):
    return next(x for x in json.loads((R.PKG/'EXPERIMENTS.json').read_text())['experiments'] if x['id']==experiment)


def cpu_now():
    c=resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+c.ru_utime+c.ru_stime


def stopped_receipts(experiments,reason,triggers,scripts):
    for experiment in experiments:
        paths=[]
        for seed in SEEDS:
            paths.append(R.run_record(experiment,'M2',seed,'EXPLORATORY',
                dict(not_run=True,skip_reason=reason,stop_trigger_results=triggers),n=0,
                null=dict(model='not run: binding lane stop',mean=None,sd=None,empirical_p=None,q=None),
                run_id='stopped/seed-'+str(seed),scripts=scripts,
                decision=dict(verdict='EXPLORATORY',not_run=True,skip_reason=reason)))
        R.confirm(experiment,paths)
        R.registry_update(experiment,'EXPLORATORY',not_run=True,skip_reason=reason,stop_trigger_results=triggers)
    R.write_json(R.RESULTS/'M2'/'STOP.json',dict(lane='C',reason=reason,trigger_results=triggers,
                 not_run=experiments,skipped_items_are_not_nulls=True),immutable=True)


def fill_run(experiment,attempt):
    prereg,protocol=R.preregistration('M2',experiment)
    full=json.loads(prereg.read_text())['protocol']
    scripts=R.source_manifest();R.registry_update(experiment,'running',attempt=attempt)
    started,c0=time.monotonic(),cpu_now()
    models=fill.prepare(R.ROOT,('2802','2751','1672'))
    prep=dict(cpu_seconds=cpu_now()-c0,peak_rss_bytes=run_m0.peak(),models=models)
    directory=R.RESULTS/experiment/attempt
    specs=[dict(experiment=experiment,index=x['index'],seed=s,moves=300000,pilot=10000,initial_checkpoint=1000) for x in models for s in SEEDS]
    done={};budget=full['S4']['budget_total_cpu_seconds'] if experiment=='S-4' else 600
    task_cpu=0.;failure=None
    def checkpoint(i,item):
        nonlocal task_cpu
        task_cpu+=item.get('cpu_seconds') or 0;done[i]=item
        R.write_json(directory/'checkpoints'/('task-%03d.json'%i),dict(spec=specs[i],**item),immutable=True)
        if task_cpu+prep['cpu_seconds']>=budget and len(done)<len(specs):
            raise BudgetExhausted('registered CPU budget exhausted; unfinished tasks terminated')
    try:
        pool.run_pool(S.fill_task,[(s,) for s in specs],workers=pool.worker_count(),timeout=600,rss_gib=6,
            projection_path=directory/'MEMORY-PROJECTION.json',on_result=checkpoint)
    except BaseException as exc:
        failure=str(exc) if isinstance(exc,BudgetExhausted) else traceback.format_exc()[-6000:]
    total_cpu=cpu_now()-c0
    paths=[]
    for seed in SEEDS:
        selected=[dict(spec=specs[i],**item) for i,item in sorted(done.items()) if specs[i]['seed']==seed]
        status=run_m0.status_of(selected) if len(selected)==len(models) else ('TIMEOUT' if failure and 'budget' in failure else 'ERROR')
        paths.append(R.run_record(experiment,'M2',seed,status,
            dict(preparation=prep,tasks=selected,stopped=failure,total_family_cpu_seconds=total_cpu),
            n=0,wall_seconds=time.monotonic()-started,cpu_seconds=total_cpu/2,
            peak_rss_bytes=max([prep['peak_rss_bytes']]+[x.get('peak_rss_bytes') or 0 for x in selected]),
            run_id=attempt+'/seed-'+str(seed),scripts=scripts,
            additional=dict(cpu_allocation='Family measured CPU divided equally between seed receipts; task CPU retained separately.')))
    status=R.confirm(experiment,paths)
    print(json.dumps(dict(experiment=experiment,status=status)),flush=True)
    return status


def confluence(attempt):
    preg,definition=R.preregistration('M2','S-2')
    protocol=json.loads(preg.read_text())['protocol']['S2']
    scripts=R.source_manifest();R.registry_update('S-2','running',attempt=attempt)
    started,c0=time.monotonic(),cpu_now()
    names=protocol['primary_words']+[protocol['preregistered_replication_word']]
    metadata=S.prepare_s2([R.ROOT/p for p in names],protocol['endpoint'])
    prep=dict(cpu_seconds=cpu_now()-c0,peak_rss_bytes=run_m0.peak(),words=metadata)
    directory=R.RESULTS/'S-2'/attempt
    R.write_json(directory/'PREPARATION.json',prep,immutable=True)
    refs={};orders={};launches=[];failure=None;spent=prep['cpu_seconds']
    budget=protocol['budgets']['total_cpu_seconds']
    def launch(label,target,specs,timeout=600):
        nonlocal spent
        output={}
        def checkpoint(i,item):
            nonlocal spent
            spent+=item.get('cpu_seconds') or 0;output[i]=item
            R.write_json(directory/label/('task-%04d.json'%i),dict(spec=specs[i],**item),immutable=True)
            if len(output)%25==0 or len(output)==len(specs):
                print(json.dumps(dict(experiment='S-2',phase=label,completed=len(output),total=len(specs),accounted_cpu_seconds=spent)),flush=True)
            if spent>=budget and len(output)<len(specs):
                raise BudgetExhausted('registered S2 family CPU cap reached; unfinished tasks terminated, never retried')
        error=None
        try:
            pool.run_pool(target,[(s,) for s in specs],workers=pool.worker_count(),timeout=timeout,rss_gib=4,
                projection_path=directory/(label+'-MEMORY-PROJECTION.json'),on_result=checkpoint,
                cpu_budget_seconds=max(0.01,budget-(cpu_now()-c0)))
        except BaseException as exc:
            error=str(exc) if isinstance(exc,(BudgetExhausted,pool.PoolCpuBudgetExceeded)) else traceback.format_exc()[-6000:]
        launches.append(dict(label=label,specs=specs,completed=len(output),error=error))
        return output,error
    for group,indexes in [('primary',[0,1]),('replication',[2])]:
        if spent>=budget:
            failure='registered S2 budget exhausted before '+group;break
        specs=[dict(index=i,endpoint=protocol['endpoint'],timeout=min(600,max(1,int(budget-spent)))) for i in indexes]
        found,error=launch(group+'-references',S.optimum_task,specs)
        for j,out in found.items():
            index=specs[j]['index'];refs[index]=out
            if out['status']=='OK' and out['result'].get('certified'):
                S.install_optimum(index,out['result'])
        if error:failure=error
        active=[i for i in indexes if i in S._OPTIMA]
        if active and spent<budget:
            specs=[dict(index=i,seed=seed,start_order=order,order_count=1)
                   for order in range(100) for i in active for seed in SEEDS]
            found,error=launch(group+'-orders',S.confluence_batch_task,specs,
                               timeout=protocol['budgets']['order_task_wall_seconds'])
            for j,out in found.items():
                s=specs[j];orders.setdefault((s['index'],s['seed']),[]).append(out)
            if error:failure=error
        if failure:break
    total_cpu=cpu_now()-c0
    receipts=[];all_summaries={}
    for seed in SEEDS:
        summaries=[S.summarize_confluence(orders.get((i,seed),[]),i,seed) for i in range(len(names))]
        all_summaries[seed]=summaries
        primary=summaries[:2]
        states=[x['status'] for x in primary]
        for i in (0,1):
            reference=refs.get(i)
            if reference is not None:
                state=reference['status'] if reference['status']!='OK' else reference['result'].get('status','PASS')
                if state in ('ERROR','TIMEOUT'):states.append(state)
        if 'ERROR' in states:status='ERROR'
        elif 'TIMEOUT' in states:status='TIMEOUT'
        elif any(x.get('statistics',{}).get('completed_orders',100)<100 for x in primary):
            status='TIMEOUT' if failure and 'budget' in failure else 'EXPLORATORY'
        elif 'NULL' in states:status='NULL'
        elif states==['PASS','PASS']:status='PASS'
        else:status='EXPLORATORY'
        receipts.append(R.run_record('S-2','M2',seed,status,
            dict(words=summaries,reference_controls=refs,preparation=prep,launches=launches,
                 stopped=failure,total_family_cpu_seconds=total_cpu),
            n=min(x.get('n_permutations',0) for x in primary),
            null=dict(model='certified optimum reference, not a permutation-significance test',mean=None,sd=None,empirical_p=None,q=None),
            wall_seconds=time.monotonic()-started,cpu_seconds=total_cpu/2,
            peak_rss_bytes=max([prep['peak_rss_bytes']]+[o.get('peak_rss_bytes') or 0 for xs in orders.values() for o in xs]),
            words=names,run_id=attempt+'/seed-'+str(seed),scripts=scripts,
            decision=dict(verdict=status,pass_bar=definition['pass_bar'],primary_words=names[:2],replication=names[2]),
            additional=dict(cpu_allocation='Measured family CPU divided equally between seed receipts; individual task CPU retained.')))
    status=R.confirm('S-2',receipts)
    previous=row('S-6')
    if status=='NULL' and previous['status']=='NULL' and previous.get('confirmed'):
        stopped_receipts(['S-4','S-5'],
            'Two consecutive confirmed scientific NULLs in Lane C: S-6 binding-interval prediction and S-2 greedy lowering. PLAN section 6 stops the lane.',
            previous['result_files']+[str(p.relative_to(R.PKG)) for p in receipts],scripts)
    print(json.dumps(dict(experiment='S-2',status=status,lane_stopped=(R.RESULTS/'M2'/'STOP.json').exists())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('experiment',choices=['M2-AUDIT','S-2','S-4']);p.add_argument('--attempt',default='v1');a=p.parse_args()
    os.chdir(R.ROOT)
    if a.experiment=='S-2':confluence(a.attempt)
    else:fill_run(a.experiment,a.attempt)
