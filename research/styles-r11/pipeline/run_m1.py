#!/usr/bin/env python3
"""Execute the frozen M1 grammar gate and enforce the cross-milestone lane stop."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time
import traceback
sys.dont_write_bytecode=True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import records as R
import pool
import run_m0
import string_screen as S


def registry_row(experiment):
    return next(x for x in json.loads((R.PKG/'EXPERIMENTS.json').read_text())['experiments'] if x['id']==experiment)


def compact_grammar(value):
    """Keep exact decision evidence; keep a full constructive witness only on PASS."""
    if value.get('status')=='PASS':
        return value
    for field in ('terminals','rules'):
        data=value.pop(field,None)
        value[field+'_sha256']=hashlib.sha256(json.dumps(data,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    for row in value.get('per_word',{}).values():
        axiom=row.pop('axiom',None)
        row['axiom_sha256']=hashlib.sha256(json.dumps(axiom,separators=(',',':')).encode()).hexdigest()
    return value


class BudgetExhausted(Exception):
    pass


def grammar(attempt):
    prereg,definition=R.preregistration('M1','L-1')
    registration=json.loads(prereg.read_text())
    protocol=registration['protocol'];seeds=protocol['seeds']
    words=protocol['word_scope']['screen']
    triples=protocol['L1']['triples']
    assert len(triples)==84
    scripts=R.source_manifest()
    R.registry_update('L-1','running',attempt=attempt,preregistration_sha256=R.sha256(prereg))
    tprep,cprep=time.monotonic(),time.process_time()
    S.prepare([R.ROOT/w['path'] for w in words],controls=False)
    prep=dict(wall_seconds=time.monotonic()-tprep,cpu_seconds=time.process_time()-cprep,peak_rss_bytes=run_m0.peak())
    paths=[]
    for seed in seeds:
        directory=R.RESULTS/'L-1'/attempt/('seed-'+str(seed))
        assert not directory.exists(),directory
        specs=[dict(experiment='L-1',seed=seed,paths=[str(R.ROOT/p) for p in t['paths']],
                    triple_id=t['triple_id'],max_rules=201) for t in triples]
        completed={};cpu=0.;started=time.monotonic();cpustart=time.process_time()
        children=resource.getrusage(resource.RUSAGE_CHILDREN)
        def save(index,item):
            nonlocal cpu
            cpu+=item.get('cpu_seconds') or 0
            if item['status']=='OK':item['result']=compact_grammar(item['result'])
            completed[index]=dict(spec=specs[index],**item)
            R.write_json(directory/'checkpoints'/('task-%03d.json'%index),completed[index],immutable=True)
            if len(completed)%10==0 or len(completed)==len(specs):
                print(json.dumps(dict(experiment='L-1',seed=seed,completed=len(completed),total=len(specs),cpu_seconds=cpu)),flush=True)
            if cpu>=protocol['L1']['budget_cpu_seconds_per_seed'] and len(completed)<len(specs):
                raise BudgetExhausted('registered grammar CPU cap reached; unfinished tasks terminated without retry')
        stopped=None
        try:
            pool.run_pool(S.task,[(s,) for s in specs],workers=pool.worker_count(),timeout=300,rss_gib=4,
                          projection_path=directory/'MEMORY-PROJECTION.json',on_result=save)
        except BaseException as exc:
            stopped=str(exc) if isinstance(exc,BudgetExhausted) else traceback.format_exc()[-6000:]
        after=resource.getrusage(resource.RUSAGE_CHILDREN)
        actual_cpu=time.process_time()-cpustart+after.ru_utime+after.ru_stime-children.ru_utime-children.ru_stime+prep['cpu_seconds']/len(seeds)
        states=Counter(x['status'] if x['status']!='OK' else x['result']['status'] for x in completed.values())
        if states['PASS']:
            status='PASS'
        elif states['ERROR']:
            status='ERROR'
        elif states['TIMEOUT'] or len(completed)<len(specs):
            status='TIMEOUT' if not stopped or isinstance(stopped,str) and 'CPU cap' in stopped else 'ERROR'
        elif states['NULL']==len(specs):
            status='NULL'
        else:
            status='EXPLORATORY'
        result=R.run_record('L-1','M1',seed,status,
            dict(preparation=prep,triples=[completed[i] for i in sorted(completed)],counts=dict(states),
                 completed_triples=len(completed),planned_triples=84,stopped=stopped),
            n=0,wall_seconds=time.monotonic()-started,cpu_seconds=actual_cpu,
            peak_rss_bytes=max([prep['peak_rss_bytes']]+[x.get('peak_rss_bytes') or 0 for x in completed.values()]),
            words=[w['pin_key'] for w in words],run_id=attempt+'/seed-'+str(seed),scripts=scripts,
            decision=dict(verdict=status,pass_bar=definition['pass_bar'],scope_of_null=protocol['L1']['scope_of_null'],
                          pattern_status='not established by the exact grammar gate'))
        paths.append(result)
    status=R.confirm('L-1',paths)
    previous=registry_row('L-2')
    if status=='NULL' and previous['status']=='NULL' and previous.get('confirmed'):
        triggers=previous['result_files']+[str(p.relative_to(R.PKG)) for p in paths]
        reason='Two consecutive confirmed scientific NULLs in Lane A: L-2 literal cleanup and L-1 fixed capped RePair on all 84 triples. PLAN section 6 stops the string lane.'
        for experiment in ('L-3','L-4','L-5'):
            receipts=[]
            for seed in seeds:
                receipts.append(R.run_record(experiment,'M1',seed,'EXPLORATORY',
                    dict(not_run=True,skip_reason=reason,stop_trigger_results=triggers),n=0,
                    null=dict(model='not run: binding lane stop',mean=None,sd=None,empirical_p=None,q=None),
                    words=[w['pin_key'] for w in words],run_id='stopped/seed-'+str(seed),scripts=scripts,
                    decision=dict(verdict='EXPLORATORY',not_run=True,skip_reason=reason)))
            R.confirm(experiment,receipts)
            R.registry_update(experiment,'EXPLORATORY',not_run=True,skip_reason=reason,stop_trigger_results=triggers)
        R.write_json(R.RESULTS/'M1'/'STOP.json',dict(lane='A',registered_utc=R.utcnow(),reason=reason,
            trigger_results=triggers,not_run=['540-cell screen','L-3','L-4','L-5','N4 constructor control'],
            scientific_nulls=['L-2','L-1'],skipped_items_are_not_nulls=True),immutable=True)
    print(json.dumps(dict(experiment='L-1',status=status,lane_stopped=(R.RESULTS/'M1'/'STOP.json').exists())),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--attempt',default='v1');args=p.parse_args()
    os.chdir(R.ROOT)
    grammar(args.attempt)
