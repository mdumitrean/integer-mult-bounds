#!/usr/bin/env python3
"""Registered semantic-equivalence validation; never changes the scientific null."""
import argparse
import json
import os
from pathlib import Path
import sys
import time
sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[key] = '1'
sys.path.insert(0,str(Path(__file__).resolve().parent))
import records as R
import pool
import run_m0
import word_tasks
import word_frame_fast


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--attempt',default='accelerator-v1')
    args=p.parse_args()
    os.chdir(R.ROOT)
    prereg=R.RESULTS/'M0'/'ACCELERATOR-PREREGISTRATION.json'
    protocol=json.loads(prereg.read_text())
    words=protocol['words'];seeds=protocol['seeds']
    scripts=R.source_manifest()
    directory=R.RESULTS/'P-1'/args.attempt
    assert not directory.exists(),directory
    t0,c0=time.monotonic(),time.process_time()
    word_tasks.prepare([run_m0.pin_path(n) for n in words],controls=True)
    certification=word_frame_fast.accelerate(word_tasks,enabled=True)
    prep=dict(wall_seconds=time.monotonic()-t0,cpu_seconds=time.process_time()-c0,
              peak_rss_bytes=run_m0.peak(),certification=certification)
    R.write_json(directory/'PREPARATION.json',prep,immutable=True)
    specs=[dict(path=str(run_m0.pin_path(n)),seed=s,sweeps=1) for n in words for s in seeds]
    outputs=pool.run_pool(word_frame_fast.verification_task,[(s,) for s in specs],
        workers=pool.worker_count(),timeout=300,rss_gib=4,
        projection_path=directory/'MEMORY-PROJECTION.json',
        on_result=run_m0.checkpoint_callback(directory/'checkpoints',specs))
    paths=[];states=[]
    for seed in seeds:
        pairs=[(s,o) for s,o in zip(specs,outputs) if s['seed']==seed]
        status=run_m0.status_of([o for _,o in pairs]);states.append(status)
        paths.append(R.run_record('P-1','M0',seed,status,
            dict(subfamily='accelerator exact equivalence',preparation=prep,tasks=[dict(spec=s,**o) for s,o in pairs]),
            n=0,wall_seconds=time.monotonic()-t0,
            cpu_seconds=prep['cpu_seconds']/len(seeds)+sum(o.get('cpu_seconds') or 0 for _,o in pairs),
            peak_rss_bytes=max([prep['peak_rss_bytes']]+[o.get('peak_rss_bytes') or 0 for _,o in pairs]),
            words=words,run_id=args.attempt+'/seed-'+str(seed),scripts=scripts,
            decision=dict(verdict=status,pass_bar=protocol['protocol']['pass_bar']),
            additional=dict(accelerator_preregistration_sha256=R.sha256(prereg))))
    status='PASS' if states==['PASS']*len(seeds) else 'ERROR'
    R.write_json(directory/'CONFIRMATION.json',dict(status=status,seeds=seeds,
        result_files=[str(p.relative_to(R.PKG)) for p in paths],
        accelerator_preregistration_sha256=R.sha256(prereg)),immutable=True)
    print(json.dumps(dict(status=status,result_files=[str(p) for p in paths])),flush=True)


if __name__=='__main__':
    main()
