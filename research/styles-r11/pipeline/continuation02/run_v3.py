"""Frozen two-seed inventory-cap audit, launched only through pipeline/pool.py."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import gzip
import json
import os
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent/'continuation'), str(HERE.parent)]
import records as R
import pool
import latest_fill as F
import run_g2 as U
import inventory_cap as V

ROUND = R.RESULTS/'CONTINUATION-02'
EXPERIMENT = 'V3-INVENTORY-CAP'
PREG = ROUND/'V3/PREREGISTRATION.json'
PREG_SHA = '94333b7f1ad4ae62405f60f76999cc4dd6da7d774086128046912d2b6b9a5d1f'
SEEDS = (12037,31069)
TEMPLATE = dict(path='data/continuation-01/pr2917/package/allocation/vendor/TEMPLATE.json.gz',
                sha256='21297b20f1f2dc76eb9dd8124416068c3cb096bab9df17fa4da19bc68dfe082e')


def main():
    protocol=json.loads(PREG.read_text())
    U.need(R.sha256(PREG)==PREG_SHA and tuple(protocol['seeds'])==SEEDS and protocol['state']=='FROZEN',
           'frozen preregistration and seeds')
    U.need(not sys.flags.optimize and sys.pycache_prefix is not None and not Path(sys.pycache_prefix).exists(),
           'assertions and unused private bytecode namespace')
    pins_path=ROUND/'V3/IMPLEMENTATION-PINS.json'
    pins=json.loads(pins_path.read_text())
    for path,sha in pins['sha256'].items():
        U.need(R.sha256(R.ROOT/path)==sha,'pre-execution source pin: '+path)
    registry_path=ROUND/'EXPERIMENTS.json'
    registry=json.loads(registry_path.read_text())
    row=next(r for r in registry['experiments'] if r['id']==EXPERIMENT)
    U.need(row['status']=='planned','one immutable attempt only')
    run=ROUND/EXPERIMENT/'v1'
    run.mkdir(parents=True,exist_ok=False)
    row.update(status='running',execution='RUNNING',started_utc=R.utcnow())
    registry['no_active_experiments']=False
    R.write_json(registry_path,registry)
    start_cpu,start_wall=U.cpu(),time.monotonic()
    failure=None;observed={};manifest={};prepared={};agreement=False
    attribution=R.provenance()+F.provenance()['source_attribution']
    prior_cpu=sum(float(r.get('cpu_seconds',0)) for r in registry['experiments'] if r['id']!=EXPERIMENT)
    inputs=deepcopy(protocol['inputs'])
    module_pin={k:inputs[k] for k in ('target','basis','ledger_source','g2_results')}
    module_pin.update(matched_ledgers=inputs['matched_ledger'],template=TEMPLATE,source_attribution=attribution)

    def checkpoint(index,item):
        observed[index]=dict(item=item,artifact=U.artifact(run/('seed-'+str(SEEDS[index]))/'TASK.json.gz',item))
        print(json.dumps(dict(seed=SEEDS[index],pool_status=item['status'],
                             decision=item.get('result',{}).get('status'))),flush=True)

    try:
        now=datetime.now(timezone.utc)
        U.need(now<datetime.fromisoformat(protocol['science_launch_cutoff_utc']), 'science launch cutoff')
        for ref in [inputs['g2_run'],*inputs['g2_results']]:
            U.need(R.sha256(R.PKG/ref['path'])==ref['sha256'],'immutable prior G2 result binding')
        prepared['source']=F.prepare(pr=2917)
        record=F.get_record();model=record['model']
        U.need((record['dimension'],record['wires'],model.calls,model.ports)==(73,66304,666,112),
               'actual fixed source geometry')
        U.need({owner for owner,child in model.win}==set(range(74)), 'all74 source replica windows')
        supply=Counter(cap for cap,start,stop in model.win.values() if cap>0)
        expected={int(c):n for c,n in protocol['domain']['supplies_per_replica'].items()}
        U.need({c:n*model.ports for c,n in supply.items()}=={c:n*74 for c,n in expected.items()},
               'actual source window capacities equal registered per-replica supplies')
        prepared['actual_window_supply']=dict(capacity_types_all_replicas=dict(supply),ports=model.ports,
            replicas=74,supplies_per_replica=expected,template=TEMPLATE,
            statement='Bound directly to the once-parent-loaded source FillModel.win; only zero capacity omitted.')
        ledger_path=R.PKG/inputs['ledger_source']['path']
        U.need(R.sha256(ledger_path)==inputs['ledger_source']['sha256'],'input ledger hash')
        prepared['inventory_cap']=V.prepare(module_pin,json.loads(gzip.decompress(ledger_path.read_bytes())))
        manifest=U.snapshot()
        U.artifact(run/'IMPLEMENTATION.json',dict(script_sha256=manifest,prepared=prepared,
            preregistration_sha256=PREG_SHA,implementation_pins_sha256=R.sha256(pins_path),
            source_attribution=attribution,comparison_attribution=protocol['source_attribution'],
            private_bytecode_namespace=sys.pycache_prefix,frozen_utc=R.utcnow(),parent_load_once=True))
        now=datetime.now(timezone.utc)
        U.need(now<datetime.fromisoformat(protocol['science_launch_cutoff_utc']), 'pool launch cutoff')
        remaining=min(protocol['resources']['cpu_budget_seconds_family']-(U.cpu()-start_cpu),
                      protocol['resources']['round_cpu_budget_seconds']-prior_cpu-(U.cpu()-start_cpu))
        pool.run_pool(V.task,[(seed,) for seed in SEEDS],workers=pool.worker_count(),timeout=300,rss_gib=4,
            working_set_gib=1,projection_path=run/'MEMORY-PROJECTION.json',
            on_result=checkpoint,cpu_budget_seconds=remaining)
        U.need(len(observed)==2,'both seed tasks complete')
        bad=[x['item'] for x in observed.values() if x['item']['status']!='OK']
        if bad:
            if any(x['status']=='TIMEOUT' for x in bad):
                raise TimeoutError('registered worker timeout')
            raise RuntimeError('pool task error: '+repr(bad)[:6000])
        decisions=[]
        for i in range(2):
            scientific=deepcopy(observed[i]['item']['result'])
            scientific.pop('seed');scientific.pop('cpu_seconds')
            decisions.append(scientific)
        agreement=decisions[0]==decisions[1]
        U.need(agreement,'two seeds agree on all exact scientific certificates')
        U.need(datetime.now(timezone.utc)<datetime.fromisoformat(protocol['hard_stop_utc']), 'hard stop')
    except BaseException as error:
        failure=dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc()[-8000:])

    elapsed_cpu,elapsed_wall=U.cpu()-start_cpu,time.monotonic()-start_wall
    if failure:
        status='TIMEOUT' if failure['type'] in ('TimeoutError','PoolCpuBudgetExceeded') else 'ERROR'
    else:
        status=observed[0]['item']['result']['status']
    confirmed=status=='NULL' and agreement and failure is None
    task_cpu=sum(x['item'].get('cpu_seconds') or 0 for x in observed.values())
    overhead=max(0,elapsed_cpu-task_cpu)
    results=[]
    for i,seed in enumerate(SEEDS):
        saved=observed.get(i,{});item=saved.get('item',{});statistics=item.get('result',{})
        result=dict(schema_version=1,experiment=EXPERIMENT,milestone='CONTINUATION-02/V3',
            recorded_utc=R.utcnow(),seed=seed,status=status,confirmed=confirmed,n_permutations=0,
            word_blob_ids={p['path']:p['git_blob'] for p in attribution},source_attribution=attribution,
            comparison_attribution=protocol['source_attribution'],inputs=inputs,script_sha256=manifest,
            script_manifest_sha256=U.digest(manifest),preregistration_sha256=PREG_SHA,
            implementation_pins_sha256=R.sha256(pins_path),statistics=statistics,
            cpu_seconds=(item.get('cpu_seconds') or 0)+(overhead if i==0 else 0),wall_seconds=elapsed_wall,
            peak_rss_bytes=item.get('peak_rss_bytes'),pool_receipt=saved.get('artifact'),launch_failure=failure,
            scientific_decision_agreement=agreement,confirmation_required=True,
            null_summary=dict(model='exact fixed-template helper-inventory relaxation; no permutation model',
                              mean=None,sd=None,empirical_p=None),
            decision=dict(verdict=status,null_bar=protocol['null_bar'],headroom_bar=protocol['headroom_bar']),
            no_actual_allocation_or_native_claim=True)
        results.append(U.artifact(run/('seed-'+str(seed))/'RESULT.json',result))
    row.update(status=status,execution='COMPLETED' if failure is None else 'INCOMPLETE',confirmed=confirmed,
        scientific_decision_agreement=agreement,cpu_seconds=elapsed_cpu,wall_seconds=elapsed_wall,
        result_files=[r['path'] for r in results],updated_utc=R.utcnow())
    registry['no_active_experiments']=True
    registry['status']='ROUND_CHECKS_PENDING'
    registry['lane_status']['constructive-word'].update(consecutive_confirmed_nulls=1 if confirmed else 0,
        latest_experiment=EXPERIMENT,stopped=confirmed,
        scope='If NULL, all matched G2 nominees are capped under this registered model; no further pivot this round.')
    R.write_json(registry_path,registry)
    U.artifact(run/'RUN.json',dict(status=status,confirmed=confirmed,scientific_decision_agreement=agreement,
        total_cpu_seconds=elapsed_cpu,total_wall_seconds=elapsed_wall,prior_round_cpu_seconds=prior_cpu,
        cumulative_round_cpu_seconds=prior_cpu+elapsed_cpu,results=results,failure=failure,
        actual_window_supply=prepared.get('actual_window_supply'),workers=pool.worker_count(),
        implementation_sha256=R.sha256(run/'IMPLEMENTATION.json') if (run/'IMPLEMENTATION.json').exists() else None,
        stop_rule=protocol['stop_rule'],scope='No new kappa claim or allocation/native admission.'))
    print(json.dumps(dict(experiment=EXPERIMENT,status=status,confirmed=confirmed,
        cpu_seconds=elapsed_cpu,wall_seconds=elapsed_wall,failure=failure)),flush=True)
    if failure:
        raise SystemExit(1)


if __name__=='__main__':
    main()
