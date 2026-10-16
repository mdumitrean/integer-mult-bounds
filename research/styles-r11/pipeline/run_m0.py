#!/usr/bin/env python3
"""Preregistered M0 runner. Run only with -I -B; no held-out data are opened."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import records as R
import pool

SEEDS = (11031,29063)


def pin_path(name):
    return R.ROOT / name if '/' in name else R.PKG / 'data/words' / name


def status_of(outputs):
    states = [x['status'] if x['status'] != 'OK' else x['result'].get('status','PASS') for x in outputs]
    for value in ('ERROR','TIMEOUT','NULL','EXPLORATORY'):
        if value in states:
            return value
    return 'PASS'


def peak():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024


def checkpoint_callback(directory, specs):
    def save(index,value):
        item = dict(task=specs[index],**value)
        R.write_json(directory / ('task-%05d.json' % index),item,immutable=True)
        if index % 10 == 0 or index + 1 == len(specs):
            print(json.dumps(dict(completed=index+1,tasks=len(specs),last_status=value['status'])),flush=True)
    return save


def run_small(experiment,attempt):
    preg,protocol = R.preregistration('M0',experiment)
    scripts = R.source_manifest()
    R.registry_update(experiment,'running',attempt=attempt,preregistration_sha256=R.sha256(preg))
    t0,c0=time.monotonic(),time.process_time()
    specs=[]; prep_errors=[]; rss=4; timeout=300; control_outputs=[]
    words=list(R.pins())
    try:
        if experiment in ('P-1','L-2'):
            import word_tasks as module
            for name in words:
                path=pin_path(name)
                try:
                    module.prepare([path],controls=experiment=='P-1')
                    for seed in SEEDS:
                        specs.append(dict(experiment=experiment,path=str(path),seed=seed,controls=True))
                except BaseException:
                    err=traceback.format_exc()[-6000:]
                    print(json.dumps(dict(preparation_error=name,error=err)),flush=True)
                    for seed in SEEDS:
                        prep_errors.append(dict(seed=seed,path=name,status='ERROR',error=err))
        elif experiment in ('L-6','L-7'):
            import growth as module
            specs=[dict(experiment=experiment,seed=s,n_permutations=2000) for s in SEEDS]
            timeout=900 if experiment=='L-7' else 300
        elif experiment in ('P-3','S-6'):
            import fill as module
            names=('2802','2751','1672') if experiment=='P-3' else ('2802',)
            indexes=module.prepare(R.ROOT,names)
            specs=[dict(experiment=experiment,index=x['index'],seed=s,n_permutations=2000,budget_seconds=300)
                   for x in indexes for s in SEEDS]
            rss=6;timeout=600
        elif experiment=='S-1':
            import matching as module
            indexes=module.prepare([pin_path(name) for name in words])
            specs=[dict(index=x['index'],seed=s,n_permutations=2000) for x in indexes for s in SEEDS]
            timeout=300
        else:
            raise ValueError(experiment)
    except BaseException:
        err=traceback.format_exc()[-6000:]
        prep_errors.extend(dict(seed=s,status='ERROR',error=err) for s in SEEDS)
        print(err,flush=True)
    prep=dict(wall_seconds=time.monotonic()-t0,cpu_seconds=time.process_time()-c0,peak_rss_bytes=peak())
    directory=R.RESULTS/experiment/attempt
    directory.mkdir(parents=True,exist_ok=True)
    R.write_json(directory/'PREPARATION.json',dict(metrics=prep,errors=prep_errors),immutable=True)
    outputs=[]
    if specs:
        try:
            if experiment=='P-3':
                control_specs=[dict(experiment='P3-CEILING',index=x['index'],seed=SEEDS[0]) for x in indexes]
                control_outputs=pool.run_pool(module.task,[(s,) for s in control_specs],
                    workers=pool.worker_count(),timeout=600,rss_gib=6,
                    projection_path=directory/'CONTROL-MEMORY-PROJECTION.json',
                    on_result=checkpoint_callback(directory/'controls',control_specs))
            if experiment=='S-1':
                control_specs=[dict(seed=s) for s in SEEDS]
                control_outputs=pool.run_pool(module.lineage_task,[(s,) for s in control_specs],
                    workers=pool.worker_count(),timeout=300,rss_gib=4,
                    projection_path=directory/'LINEAGE-MEMORY-PROJECTION.json',
                    on_result=checkpoint_callback(directory/'lineage',control_specs))
            outputs=pool.run_pool(module.task,[(s,) for s in specs],workers=pool.worker_count(),
                timeout=timeout,rss_gib=rss,projection_path=directory/'MEMORY-PROJECTION.json',
                on_result=checkpoint_callback(directory/'checkpoints',specs))
        except BaseException:
            err=traceback.format_exc()[-6000:]
            prep_errors.extend(dict(seed=s,status='ERROR',error=err) for s in SEEDS)
            print(err,flush=True)
    paths=[]
    for seed in SEEDS:
        pairs=[(s,o) for s,o in zip(specs,outputs) if s['seed']==seed]
        errors=[e for e in prep_errors if e['seed']==seed]
        status=status_of([o for _,o in pairs]) if pairs else 'ERROR'
        aggregate=None
        if experiment=='S-1':
            lineage=control_outputs[SEEDS.index(seed)] if len(control_outputs)==2 else None
            ledger_registry=next(e for e in json.loads((R.PKG/'EXPERIMENTS.json').read_text())['experiments'] if e['id']=='L-7')
            ledger=None
            for path in ledger_registry.get('result_files',[]):
                record=json.loads((R.PKG/path).read_text())
                if record['seed']==seed:
                    completed=record['statistics']['tasks']
                    if completed and completed[0]['status']=='OK': ledger=completed[0]['result']
            aggregate=module.summarize_s1([o for _,o in pairs],lineage,ledger,seed)
            status=aggregate['status']
        if errors: status='ERROR'
        data=dict(preparation=prep,preparation_errors=errors,once_per_word_controls=control_outputs,aggregate=aggregate,
                  tasks=[dict(spec=s,**o) for s,o in pairs])
        cpu=prep['cpu_seconds']/2 + sum(o.get('cpu_seconds') or 0 for _,o in pairs) + sum(o.get('cpu_seconds') or 0 for o in control_outputs)/2
        ns=dict(model=protocol['null_model'],mean=None,sd=None,empirical_p=None,
                by_task=[o['result'].get('null_summary') for _,o in pairs if o['status']=='OK'])
        paths.append(R.run_record(experiment,'M0',seed,status,data,
            n=2000 if experiment in ('L-6','L-7','S-1','S-6') else 0,
            null=ns,
            wall_seconds=time.monotonic()-t0,cpu_seconds=cpu,
            peak_rss_bytes=max([prep['peak_rss_bytes']]+[o.get('peak_rss_bytes') or 0 for _,o in pairs]),
            words=words,run_id=attempt+'/seed-'+str(seed),scripts=scripts,
            additional={'checkpoint_directory':str((directory/'checkpoints').relative_to(R.PKG))}))
    status=R.confirm(experiment,paths)
    if experiment=='P-1' and status=='PASS':
        import word_tasks
        for name in words:
            data=word_tasks.output_language(pin_path(name))
            key=R.pins()[name]['git_blob'][:12]
            dest=R.RESULTS/'M0'/'language'/(key+'.json.gz')
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(gzip.compress(json.dumps(data,separators=(',',':')).encode(),mtime=0))
    print(json.dumps(dict(experiment=experiment,status=status,results=[str(p) for p in paths])),flush=True)


class BudgetExhausted(Exception):
    pass


def run_p2(attempt, accelerated=False):
    import word_tasks as module
    preg, protocol = R.preregistration('M0','P-2')
    scripts=R.source_manifest()
    R.registry_update('P-2','running',attempt=attempt)
    names=[]
    for path in protocol['inputs']:
        key=path.split('research/styles-r11/data/words/')[-1]
        assert key in R.pins()
        names.append(key)
    tprep,cprep=time.monotonic(),time.process_time()
    module.prepare([pin_path(n) for n in names],controls=True)
    acceleration=None
    if accelerated:
        verification=R.RESULTS/'P-1'/'accelerator-v1'/'CONFIRMATION.json'
        verified=json.loads(verification.read_text())
        assert verified['status']=='PASS','accelerator has not passed exact verification'
        checked=json.loads((R.PKG/verified['result_files'][0]).read_text())['script_sha256']
        for filename in ('word_commute_fast.py','word_frame_fast.py','nulls.py','wordio.py','word_tasks.py'):
            key='research/styles-r11/pipeline/'+filename
            assert R.sha256(R.PKG/'pipeline'/filename)==checked[key],('validated code changed',filename)
        import word_frame_fast
        acceleration=word_frame_fast.accelerate(module,enabled=True)
        acceleration['verification_file']=str(verification.relative_to(R.PKG))
    prep=dict(wall_seconds=time.monotonic()-tprep,cpu_seconds=time.process_time()-cprep,peak_rss_bytes=peak(),acceleration=acceleration)
    result_paths=[]
    for seed in SEEDS:
        directory=R.RESULTS/'P-2'/attempt/('seed-'+str(seed))
        directory.mkdir(parents=True,exist_ok=True)
        specs=[dict(experiment='P-2',path=str(pin_path(name)),seed=seed,
                    null=control,n=50,start=start,alphabet='mid')
               for start in range(0,2000,50)
               for name in names for control in ('N1','N1b','N1c','N2')]
        cells={}; failed=[]; completed_cpu=0.0; measured_rss=prep['peak_rss_bytes']
        started=time.monotonic(); child0=resource.getrusage(resource.RUSAGE_CHILDREN)

        def save(index,item):
            nonlocal completed_cpu,measured_rss
            completed_cpu+=item.get('cpu_seconds') or 0
            measured_rss=max(measured_rss,item.get('peak_rss_bytes') or 0)
            spec=specs[index]
            compact=dict(task=spec,**item)
            if item['status']=='OK':
                value=item['result']; raw=value.pop('values')
                moments={}
                key=(spec['path'],spec['null'])
                cell=cells.setdefault(key,dict(path=spec['path'],null=spec['null'],n=0,statistics={},diagnostics=Counter()))
                cell['n']+=value['n'];cell['diagnostics'].update(value['diagnostics'])
                for stat,values in raw.items():
                    n=len(values);mean=sum(values)/n;m2=sum((v-mean)**2 for v in values)
                    mn,mx=min(values),max(values)
                    moments[stat]=dict(n=n,mean=mean,M2=m2,min=mn,max=mx)
                    dst=cell['statistics'].setdefault(stat,dict(n=0,mean=0.0,M2=0.0,real=value['real'][stat],min=mn,max=mx))
                    delta=mean-dst['mean'];total=dst['n']+n
                    dst['M2']+=m2+delta*delta*dst['n']*n/total
                    dst['mean']+=delta*n/total;dst['n']=total
                    dst['min']=min(dst['min'],mn);dst['max']=max(dst['max'],mx)
                value['sufficient_statistics']=moments
            else:
                failed.append(dict(index=index,task=spec,status=item['status'],error=item.get('error')))
            R.write_json(directory/'checkpoints'/('task-%05d.json'%index),compact,immutable=True)
            if index%36==0:
                print(json.dumps(dict(experiment='P-2',seed=seed,batches=index+1,total_batches=len(specs),completed_cpu_seconds=round(completed_cpu,2))),flush=True)
            if completed_cpu>=protocol['run_budget_core_seconds']:
                raise BudgetExhausted('registered P2 CPU budget reached; unfinished tasks terminated, never retried')

        stopped=None
        try:
            pool.run_pool(module.task,[(s,) for s in specs],workers=pool.worker_count(),
                timeout=300,rss_gib=4,projection_path=directory/'MEMORY-PROJECTION.json',on_result=save)
        except BaseException as exc:
            stopped=str(exc) if isinstance(exc,BudgetExhausted) else traceback.format_exc()[-6000:]
            print(stopped,flush=True)
        child1=resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu=child1.ru_utime+child1.ru_stime-child0.ru_utime-child0.ru_stime+prep['cpu_seconds']/2
        summaries=[]
        for cell in cells.values():
            for stat,d in cell['statistics'].items():
                d['population_sd']=math.sqrt(max(0,d.pop('M2'))/d['n'])
                d['empirical_p']=None;d['q']=None
            cell['diagnostics']=dict(cell['diagnostics']);summaries.append(cell)
        complete=len(cells)==len(names)*4 and all(c['n']==2000 for c in cells.values())
        status='ERROR' if any(x['status']=='ERROR' for x in failed) else ('PASS' if complete and not stopped else 'TIMEOUT')
        result_paths.append(R.run_record('P-2','M0',seed,status,
            dict(cells=summaries,failed_tasks=failed,stopped=stopped,planned_samples_per_cell=2000,
                 cell_count_planned=len(names)*4,completed_samples=sum(c['n'] for c in cells.values()),preparation=prep),
            n=min([c['n'] for c in cells.values()]) if len(cells)==len(names)*4 else 0,
            null={'model':'N1/N1b/N1c/N2 calibration; per-cell summaries in statistics','mean':None,'sd':None,'empirical_p':None,'inferential':False},
            wall_seconds=time.monotonic()-started,cpu_seconds=cpu,peak_rss_bytes=measured_rss,
            words=names,run_id=attempt+'/seed-'+str(seed),scripts=scripts,
            decision={'pass_bar':protocol['pass_bar'],'verdict':status,'complete':complete,'incomplete_samples_are_not_null':True}))
        print(json.dumps(dict(experiment='P-2',seed=seed,status=status,cpu_seconds=cpu,cells=len(cells))),flush=True)
    print(json.dumps(dict(experiment='P-2',status=R.confirm('P-2',result_paths))),flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('experiment')
    p.add_argument('--attempt',default='v1')
    p.add_argument('--accelerated',action='store_true')
    args=p.parse_args()
    os.chdir(R.ROOT)
    if args.experiment=='P-2':
        run_p2(args.attempt,args.accelerated)
    else:
        run_small(args.experiment,args.attempt)


if __name__=='__main__':
    main()
