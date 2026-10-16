"""Registered two-seed anchored rank-seven screen; all parallel work via pool.py.

Local grammar/cap headroom is never a released kappa. Sources and prior rounds
remain immutable. Every scientific attempt owns a new result directory.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction as Q
from pathlib import Path
import gzip
import hashlib
import json
import os
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_key] = '1'
HERE = Path(__file__).resolve().parent
OLD = HERE.parent/'continuation'
sys.path[:0] = [str(HERE),str(OLD),str(HERE.parent)]
import records as R
import pool
import latest_fill as F
import admission as A
import run_g1 as LEGACY
import rank7_search as G
import packing_cap as K

ROUND = R.RESULTS/'CONTINUATION-02'
EXPERIMENT = 'G2-ANCHORED-RANK7'
PREG = ROUND/'G2/PREREGISTRATION.json'
PREG_SHA = '678046f825d5943bc768afba378c3e59a37e7de1194e7b1f8c3b149a13a41526'
SEEDS = (12037,31069)
PROVIDERS = {}
ATTRIBUTION = []


def need(ok,message):
    if not ok:
        raise ValueError(message)


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+children.ru_utime+children.ru_stime


def canonical(value):
    return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def artifact(path,value):
    raw=canonical(value)
    data=gzip.compress(raw,mtime=0) if path.name.endswith('.gz') else raw
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)
    return dict(path=str(path.relative_to(R.PKG)),sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),payload_sha256=hashlib.sha256(raw).hexdigest())


def snapshot():
    paths=set((R.PKG/'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            p=Path(name).resolve()
            if p.is_relative_to(R.ROOT/'research') and p.suffix=='.py':
                paths.add(p)
    sources={}
    directory=ROUND/'SOURCES'
    directory.mkdir(exist_ok=True)
    for p in sorted(paths):
        raw=p.read_bytes(); sha=hashlib.sha256(raw).hexdigest()
        sources[str(p.relative_to(R.ROOT))]=sha
        target=directory/(sha+'.py.gz')
        if not target.exists():
            with target.open('xb') as handle:
                handle.write(gzip.compress(raw,mtime=0))
        else:
            need(gzip.decompress(target.read_bytes())==raw,'immutable source archive preimage')
    return sources


def address(row):
    return (int(row['helper']),tuple(row['plane']),row['mode'],tuple(row['basis_indices']))


def encoded_address(key):
    return [key[0],list(key[1]),key[2],list(key[3])]


def candidate_words(addresses):
    need(set(addresses)=={'gauge44','extra'},'both provider addresses required')
    keys={address(row) for row in addresses.values()}
    need(len(keys)==1,'provider helper/dualplane/mode/basisindices must match')
    words={}; reconstructed={}
    for pid in sorted(addresses):
        raw,transform,proof=G.reconstruct_nominee(addresses[pid])
        words[pid]=dict(raw=raw,attribution=PROVIDERS[pid]['attribution'])
        reconstructed[pid]=(raw,transform,proof)
    return words,reconstructed


def worker(spec):
    kind=spec['kind']
    if kind=='published_control':
        return LEGACY.control_task(spec)
    if kind=='rank7_control':
        return G.controls_task(spec['seed'])
    if kind=='cap_control':
        return K.controls_task(spec['seed'])
    if kind=='screen':
        return G.screen_task(spec)
    if kind=='cap':
        words,_=candidate_words(spec['addresses'])
        result=K.screen_task(dict(seed=spec['seed'],words=words,include_brackets=False,physical_families=66805))
        result.update(ledger_id=spec['ledger_id'],identity=spec['identity'])
        return result
    if kind=='validation':
        words,constructed=candidate_words(spec['addresses'])
        cap=K.screen_task(dict(seed=spec['seed'],words=words,include_brackets=True,physical_families=66805))
        need(cap['status']=='PASS_OPTIMISTIC_LOCAL_COST_SCREEN','retained nominee keeps exact optimistic headroom')
        output={}
        directory=Path(spec['directory'])
        for pid,(raw,transform,proof) in constructed.items():
            audit=A.local_admission(raw,PROVIDERS[pid]['attribution'])
            need(audit['audit']['checked_columns']==632,'all632 independent nominee columns')
            need(len(raw['helper_final'])==83,'one additional private buffer')
            output[pid]=dict(local_admission=audit,
                word=artifact(directory/('WORD-'+pid+'.json.gz'),raw),
                transform=artifact(directory/('TRANSFORM-'+pid+'.json.gz'),transform),
                certificate=artifact(directory/('CERTIFICATE-'+pid+'.json.gz'),proof))
        return dict(status='PASS_LOCAL_RANK7_AND_OPTIMISTIC_CAP',seed=spec['seed'],identity=spec['identity'],
            providers=output,cap=cap,complete_allocation='UNRUN_REQUIRED',fresh_native_admission='UNRUN_REQUIRED',
            full_physical_supplier_outer='UNRUN_REQUIRED',scope='Finite local proof and optimistic headroom only; no kappa claim.')
    raise ValueError('unregistered worker kind: '+kind)


def main():
    global PROVIDERS,ATTRIBUTION
    protocol=json.loads(PREG.read_text())
    need(R.sha256(PREG)==PREG_SHA and protocol['state']=='FROZEN' and tuple(protocol['seeds'])==SEEDS,'frozen family binding')
    need(not sys.flags.optimize,'assertions enabled')
    need(sys.pycache_prefix is not None,'fresh private bytecode namespace required')
    need(not Path(sys.pycache_prefix).exists(),'private bytecode namespace must not preexist')
    pins_path=ROUND/'G2/IMPLEMENTATION-PINS.json'
    pins=json.loads(pins_path.read_text())
    for path,sha in pins['sha256'].items():
        need(R.sha256(R.ROOT/path)==sha,'pre-execution implementation pin: '+path)
    registry_path=ROUND/'EXPERIMENTS.json'
    registry=json.loads(registry_path.read_text())
    row=next(r for r in registry['experiments'] if r['id']==EXPERIMENT)
    need(row['status']=='planned','new registered run only')
    run=ROUND/EXPERIMENT/'v1'
    run.mkdir(parents=True,exist_ok=False)
    row.update(status='running',started_utc=R.utcnow(),execution='RUNNING')
    registry['no_active_experiments']=False
    R.write_json(registry_path,registry)
    start_cpu,start_wall=cpu(),time.monotonic()
    initial_bytes=sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file())
    artifact_bytes=0
    observed={'controls':{},'screen':{},'cap':{},'validation':{}}
    tasks={}; manifest={}; prepared={}; failure=None; phase=None
    inventories={}; coverage={}; ledger_groups={}; matched=[]; favorable=[]; retained=[]
    counts={}; comparison=None
    ATTRIBUTION=R.provenance()+F.provenance()['source_attribution']

    def deadline():
        now=datetime.now(timezone.utc)
        need(now<datetime.fromisoformat(protocol['hard_stop_utc']),'registered hard stop reached')
        if now>=datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered science launch cutoff reached')
        remaining=protocol['resources']['cpu_budget_seconds_family']-(cpu()-start_cpu)
        if remaining<=0:
            raise pool.PoolCpuBudgetExceeded('whole registered family CPU budget exhausted')
        return remaining

    def launch(name,specs):
        nonlocal phase,artifact_bytes
        phase=name
        remaining=deadline()
        tasks[name]=specs
        artifact(run/(name.upper()+'-TASKS.json.gz'),specs)
        def checkpoint(index,item):
            nonlocal artifact_bytes
            blob=gzip.compress(canonical(item),mtime=0)
            if artifact_bytes+len(blob)>protocol['resources']['new_artifact_bytes_cap']:
                raise RuntimeError('new artifact budget exceeded; incomplete family')
            ref=artifact(run/name/('task-%05d.json.gz'%index),item)
            artifact_bytes+=ref['bytes']
            observed[name][index]=dict(spec=specs[index],item=item,artifact=ref)
            R.write_json(run/'BUDGET-CHECKPOINT.json',dict(phase=name,recorded_utc=R.utcnow(),
                parent_and_reaped_cpu_seconds=cpu()-start_cpu,completed_by_phase={k:len(v) for k,v in observed.items()},
                completed_task_cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for v in observed.values() for x in v.values()),
                scope='pool.py also enforces cumulative budget including live workers'))
            if name!='screen' or len(observed[name])%16==0 or len(observed[name])==len(specs):
                result=item.get('result',{})
                print(json.dumps(dict(phase=name,completed=len(observed[name]),total=len(specs),pool_status=item['status'],
                    result_status=result.get('status'),nominees=len(result.get('witnesses',[])))),flush=True)
        pool.run_pool(worker,[(spec,) for spec in specs],workers=pool.worker_count(),timeout=300,rss_gib=4,
            working_set_gib=1,projection_path=run/(name.upper()+'-MEMORY-PROJECTION.json'),
            on_result=checkpoint,cpu_budget_seconds=remaining)
        need(len(observed[name])==len(specs),'complete pool coverage: '+name)
        bad=[x['item'] for x in observed[name].values() if x['item']['status']!='OK']
        if bad:
            if any(x['status']=='TIMEOUT' for x in bad):
                raise TimeoutError(name+' task timeout')
            raise RuntimeError(name+' task failure: '+repr([(x['status'],x.get('error')) for x in bad])[:6000])
        need(sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file())<protocol['resources']['result_bytes_cap'],
             'total results storage cap')

    try:
        deadline()
        prepared['source']=F.prepare(pr=2917)
        record=F.get_record()
        source_pin=dict(pr=2917,commit=F.HEAD,manifest_sha256=F.MANIFEST_SHA,
            manifest_path='data/continuation-01/pr2917/MANIFEST.json')
        prepared['semantic_admission']=A.prepare(record,source_pin)
        for pid,relative in record['word_files'].items():
            tag='base' if pid=='gauge44' else 'extra'
            credit=deepcopy(record['file_pins'][relative])
            credit['inherited_source_attribution']=deepcopy(ATTRIBUTION)
            PROVIDERS[pid]=dict(raw=record['data'][relative],attribution=credit)
            LEGACY._CONTROL[pid]=dict(parent_raw=record['data']['data/PARENT-'+tag+'.json.gz'],
                expected_raw=record['data'][relative],attribution=credit,
                transforms=[record['data']['data/TRANSFORM-%d.json'%h] for h in LEGACY.TRANSFORM_HELPERS])
        LEGACY._ATTRIBUTION=ATTRIBUTION
        prepared['rank7']=G.prepare(PROVIDERS)
        target=protocol['target']
        prepared['cap']=K.prepare(record,dict(label='PR2930',source=dict(path=target['path'],sha256=target['sha256']),
            endpoint_field=['complex_lower'],endpoint=target['complex_lower']))
        comparison=prepared['cap']['target']
        manifest=snapshot()
        artifact(run/'IMPLEMENTATION.json',dict(script_sha256=manifest,prepared=prepared,
            preregistration_sha256=PREG_SHA,implementation_pins_sha256=R.sha256(pins_path),
            source_attribution=ATTRIBUTION,comparison_source=target,frozen_utc=R.utcnow(),
            private_bytecode_namespace=sys.pycache_prefix,workers=pool.worker_count(),parent_load_once=True))
        control_specs=[dict(kind='published_control',provider=pid,seed=seed) for seed in SEEDS for pid in sorted(PROVIDERS)]
        control_specs += [dict(kind=kind,seed=seed) for kind in ('rank7_control','cap_control') for seed in SEEDS]
        launch('controls',control_specs)
        need(all(x['item']['result']['status']=='PASS' for x in observed['controls'].values()),'all registered controls pass')
        screen_specs=[dict(kind='screen',**spec) for seed in SEEDS for spec in G.task_specs(seed)]
        launch('screen',screen_specs)
        for seed in SEEDS:
            inventories[seed]={}
            for pid in PROVIDERS:
                inv={}
                for mode in ('literal','downward_cap'):
                    rows=[x['item']['result'] for x in observed['screen'].values()
                          if x['spec']['seed']==seed and x['spec']['provider']==pid and x['item']['result']['mode']==mode]
                    planes=[tuple(p) for r in rows for p in r['planes']]
                    need(len(planes)==763 and len(set(planes))==763 and set(planes)==set(G.planes()),'exact763 registered unique frame coverage')
                    if any(r['status']=='TIMEOUT' for r in rows):
                        raise TimeoutError('internal registered rank7 construction cutoff')
                    need(all(r['complete'] for r in rows),'complete registered construction coverage')
                    need(all(r['attempted_constructions']==r['expected_constructions'] for r in rows),
                         'every bounded construction processed')
                    coverage[f'{seed}:{pid}:{mode}']=dict(frames=len(planes),unique_frames=len(set(planes)),tasks=len(rows),
                        attempted=sum(r['attempted_constructions'] for r in rows),nominees=sum(len(r['witnesses']) for r in rows))
                    for r in rows:
                        for candidate in r['witnesses']:
                            key=address(candidate)
                            need(key not in inv,'unique canonical nominee address')
                            inv[key]=candidate
                inventories[seed][pid]=inv
        for pid in PROVIDERS:
            first,second=(inventories[seed][pid] for seed in SEEDS)
            need(first==second,'second-seed full nominee inventory agreement: '+pid)
        common=set(inventories[SEEDS[0]]['gauge44'])&set(inventories[SEEDS[0]]['extra'])
        matched=sorted(common)
        counts=dict(nominees_by_provider={pid:len(inventories[SEEDS[0]][pid]) for pid in PROVIDERS},
            matched_addresses=len(matched),unmatched_by_provider={pid:len(set(inventories[SEEDS[0]][pid])-common) for pid in PROVIDERS})
        for key in matched:
            addresses={pid:inventories[SEEDS[0]][pid][key] for pid in PROVIDERS}
            ledger={pid:dict(helper=key[0],local_profile=c['local_profile'],width_inventory=c['width_inventory'],
                private_buffers=c['private_buffers']) for pid,c in addresses.items()}
            ledger_id=digest(ledger)
            if ledger_id not in ledger_groups:
                ledger_groups[ledger_id]=dict(ledger=ledger,addresses=addresses,members=[])
            ledger_groups[ledger_id]['members'].append(encoded_address(key))
        artifact(run/'COVERAGE.json',coverage)
        artifact(run/'MATCHED-LEDGERS.json.gz',dict(counts=counts,ledger_groups=ledger_groups))
        cap_specs=[dict(kind='cap',seed=seed,ledger_id=lid,addresses=g['addresses'],identity=g['members'][0])
                   for lid,g in sorted(ledger_groups.items()) for seed in SEEDS]
        if cap_specs:
            launch('cap',cap_specs)
            cap_by={}
            for saved in observed['cap'].values():
                spec,result=saved['spec'],saved['item']['result']
                cap_by[spec['ledger_id'],spec['seed']]=result
            for lid,g in ledger_groups.items():
                one,two=(cap_by[lid,seed] for seed in SEEDS)
                need(one['caps']==two['caps'] and one['status']==two['status'],'two-seed exact cap agreement')
                if one['status']=='EXPLORATORY':
                    raise RuntimeError('exact cap interval unresolved')
                if one['status']=='PASS_OPTIMISTIC_LOCAL_COST_SCREEN':
                    for identity in g['members']:
                        key=(identity[0],tuple(identity[1]),identity[2],tuple(identity[3]))
                        favorable.append((Q(one['caps'][0]['target_moment_upper']),key,lid))
                else:
                    need(one['status']=='NULL_OPTIMISTIC_CAP_NO_HEADROOM','known cap classification')
        favorable.sort()
        retained=favorable[:protocol['resources']['retained_matched_candidates_cap']]
        if retained:
            validate_specs=[]
            for i,(_,key,lid) in enumerate(retained):
                for seed in SEEDS:
                    validate_specs.append(dict(kind='validation',seed=seed,identity=encoded_address(key),ledger_id=lid,
                        addresses={pid:inventories[seed][pid][key] for pid in PROVIDERS},
                        directory=str(run/('seed-'+str(seed))/'nominees'/('candidate-%03d'%i))))
            launch('validation',validate_specs)
            for _,key,lid in retained:
                selected=[x['item']['result'] for x in observed['validation'].values() if x['spec']['identity']==encoded_address(key)]
                need(len(selected)==2 and all(x['status']=='PASS_LOCAL_RANK7_AND_OPTIMISTIC_CAP' for x in selected),
                     'retained local nominee both-seed validation')
                need({pid:selected[0]['providers'][pid]['word']['sha256'] for pid in PROVIDERS}==
                     {pid:selected[1]['providers'][pid]['word']['sha256'] for pid in PROVIDERS},'retained byte-identical words across seeds')
        phase=None
    except BaseException:
        failure=traceback.format_exc()[-10000:]
    total_cpu,total_wall=cpu()-start_cpu,time.monotonic()-start_wall
    all_saved=[x for values in observed.values() for x in values.values()]
    overhead=max(0,total_cpu-sum(x['item'].get('cpu_seconds') or 0 for x in all_saved))
    if failure:
        status='TIMEOUT' if any(t in failure for t in ('Timeout','Budget','cutoff','hard stop')) else 'ERROR'
    elif favorable:
        status='EXPLORATORY'
    else:
        status='NULL'
    results=[]
    for index,seed in enumerate(SEEDS):
        seed_items=[x for x in all_saved if x['spec']['seed']==seed]
        statistics=dict(complete=failure is None,coverage={k:v for k,v in coverage.items() if k.startswith(str(seed)+':')},
            counts=counts,matched_unique_cost_ledgers=len(ledger_groups),favorable_addresses=len(favorable),
            retained_addresses=len(retained),unretained_favorable=len(favorable)-len(retained),
            comparison_source=comparison,controls=[x['item'].get('result') for x in observed['controls'].values() if x['spec']['seed']==seed],
            native_admission='UNRUN_REQUIRED_FOR_ANY_CHANGED_WORD',full_allocation_supplier_outer='UNRUN_REQUIRED',
            original_pattern_status='No prior pattern meets all five criteria; unchanged.',
            scope='Anchored rank7 canonical basis/pivot-capped paired-provider family only; no global rank7 obstruction or kappa claim.')
        result=dict(schema_version=1,experiment=EXPERIMENT,milestone='CONTINUATION-02',recorded_utc=R.utcnow(),seed=seed,
            n_permutations=0,status=status,word_blob_ids={p['path']:p['git_blob'] for p in ATTRIBUTION},
            source_attribution=ATTRIBUTION,comparison_attribution=protocol['target'],script_sha256=manifest,
            script_manifest_sha256=digest(manifest),preregistration_sha256=PREG_SHA,
            implementation_pins_sha256=R.sha256(pins_path),statistics=statistics,
            wall_seconds=total_wall,cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in seed_items)+(overhead if index==0 else 0),
            peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in seed_items),default=None),
            null_summary=dict(model='none: exact bounded constructive grammar and necessary cost screen',mean=None,sd=None,empirical_p=None),
            decision=dict(verdict=status,pass_bar=protocol['pass_bar'],null_bar=protocol['null_bar']),confirmation_required=True,
            launch_failure=failure,incomplete_phase=phase,task_errors=[x['item'].get('error') for x in seed_items if x['item'].get('error')])
        artifact(run/('seed-'+str(seed))/'RESULT.json',result)
        results.append(result)
    confirmed=failure is None and status=='NULL'
    row.update(status=status,execution='COMPLETED' if failure is None else 'INCOMPLETE',confirmed=confirmed,
        scientific_decision_agreement=failure is None,cpu_seconds=total_cpu,wall_seconds=total_wall,
        result_files=[str((run/('seed-'+str(s))/'RESULT.json').relative_to(R.PKG)) for s in SEEDS],updated_utc=R.utcnow())
    registry['no_active_experiments']=True
    registry['status']='ROUND_CHECKS_PENDING'
    registry['lane_status']['constructive-word'].update(consecutive_confirmed_nulls=1 if confirmed else 0,
        stopped=False,latest_experiment=EXPERIMENT,scope='No next pivot or experiment scheduled in this bounded round.')
    R.write_json(registry_path,registry)
    artifact(run/'RUN.json',dict(status=status,confirmed=confirmed,total_cpu_seconds=total_cpu,total_wall_seconds=total_wall,
        failure=failure,incomplete_phase=phase,coverage=coverage,counts=counts,matched_unique_cost_ledgers=len(ledger_groups),
        favorable_addresses=len(favorable),retained_addresses=[encoded_address(x[1]) for x in retained],
        completed_by_phase={k:len(v) for k,v in observed.items()},baseline_target=protocol['target'],
        source_implementation_sha256=R.sha256(run/'IMPLEMENTATION.json') if (run/'IMPLEMENTATION.json').exists() else None,
        scope='No released kappa; changed-word native/full supplier admission is separate and mandatory.'))
    print(json.dumps(dict(experiment=EXPERIMENT,status=status,confirmed=confirmed,cpu_seconds=total_cpu,
        wall_seconds=total_wall,failure=failure,counts=counts,favorable=len(favorable))),flush=True)
    if failure:
        raise SystemExit(1)


if __name__=='__main__':
    main()
