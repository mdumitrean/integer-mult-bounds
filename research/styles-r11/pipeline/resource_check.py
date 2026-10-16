#!/usr/bin/env python3
import json
import os
from pathlib import Path
import resource
import sys
import time
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pool
import records as R

def work(seed):
    t=time.process_time();value=seed
    while time.process_time()-t<30:
        for _ in range(2000):value=(value*1664525+1013904223)&0xffffffff
    return value

def cpu():
    c=resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+c.ru_utime+c.ru_stime

if __name__=='__main__':
    preg=R.RESULTS/'M2'/'RESOURCE-VALIDATION-PREREGISTRATION.json'
    protocol=json.loads(preg.read_text());scripts=R.source_manifest();statuses=[]
    for seed in protocol['seeds']:
        c0,t0=cpu(),time.monotonic();completed=[];caught=False;message=None
        try:
            pool.run_pool(work,[(seed+i,) for i in range(8)],workers=pool.worker_count(),timeout=60,rss_gib=4,
                cpu_budget_seconds=15,projection_path=R.RESULTS/'P-1'/'cpu-limit-v1'/('MEMORY-'+str(seed)+'.json'),
                on_result=lambda i,x:completed.append(dict(index=i,**x)))
        except pool.PoolCpuBudgetExceeded as exc:caught=True;message=str(exc)
        used=cpu()-c0;status='PASS' if caught and not completed and used<=15 else 'ERROR';statuses.append(status)
        R.run_record('P-1','M0',seed,status,dict(subfamily='live CPU resource guard',completed=completed,
            budget_exception=caught,message=message,measured_cpu_seconds=used),n=0,
            wall_seconds=time.monotonic()-t0,cpu_seconds=used,
            peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
            run_id='cpu-limit-v1/seed-'+str(seed),scripts=scripts,
            decision=dict(verdict=status,pass_bar=protocol['pass_bar']),
            additional=dict(resource_validation_preregistration_sha256=R.sha256(preg)))
        print(json.dumps(dict(seed=seed,status=status,cpu_seconds=used,message=message)),flush=True)
    R.write_json(R.RESULTS/'P-1'/'cpu-limit-v1'/'CONFIRMATION.json',dict(status='PASS' if statuses==['PASS','PASS'] else 'ERROR',seeds=protocol['seeds']),immutable=True)
