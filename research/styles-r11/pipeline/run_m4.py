#!/usr/bin/env python3
"""Execute frozen held-out bookkeeping diagnostics; fetched content stays data."""
from __future__ import annotations
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
import argparse
import json
import os
from pathlib import Path
import random
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parent))
import records as R
import pool
import growth as G
import growth_m3 as M
import heldout_data as H

SEEDS = (11031, 29063)
PREG = R.RESULTS / 'M4/PREREGISTRATION.json'
SNAPSHOT = R.RESULTS / 'M4/PREDICTIONS-FROZEN.json'
IMPLEMENTATION = R.RESULTS / 'M4/IMPLEMENTATION.json'
PROTOCOL = None
ATTEMPT = 'v1'


def read(path):
    return json.loads(Path(path).read_text())


def reference(path):
    return dict(path=str(Path(path).relative_to(R.PKG)), sha256=R.sha256(path))


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def sign(value):
    return (value > 0) - (value < 0)


def task(seed):
    """All exact checks fit one bounded worker; no solver or null loop."""
    started = time.process_time()
    order = [2833, 2853]
    random.Random(seed).shuffle(order)
    packages = {}
    for pr in order:
        packages[str(pr)] = H.audit_package(pr, seed)
    audit_cpu = time.process_time() - started
    definitions = {p['id']: p for p in PROTOCOL['predictions']}
    outcomes = []
    unresolved = [name for name, item in packages.items() if item['status'] != 'PASS']
    if unresolved:
        for name in definitions:
            outcomes.append(dict(id=name, outcome='UNRESOLVED',
                reason='Exact held-out source validation did not pass', packages=unresolved))
        unresolved_status = 'ERROR' if any(packages[name]['status']=='ERROR' for name in unresolved) else 'EXPLORATORY'
        return dict(status=unresolved_status,seed=seed,packages=packages,outcomes=outcomes,
                    validation_cpu_seconds=audit_cpu, solver_calls=0)
    # The frozen L6 coefficient has this exact common geometry. Do not refit it.
    expected = definitions['D1-fixed-lambda']['normalization']
    geometry_ok = all(all(item[k] == expected[k]
        for k in ('dimension','wires','calls')) and
        item['coverage_rank_mass'] == expected['rank_mass'] for item in packages.values())
    profiles = {'2802': G._profile_records()['2802']['profile']}
    profiles.update({name:G.clean(item['complete_profile']) for name,item in packages.items()})
    if any(G.mass(profiles[name]) != item['coverage_rank_mass'] for name,item in packages.items()):
        raise ValueError('audited complete-profile rank mass disagrees with geometry')
    t0 = time.process_time()
    roots, phis, brackets = {}, {}, {}
    if geometry_ok:
        G._root_cached.cache_clear()
        for name, profile in profiles.items():
            roots[name] = G.root(profile)
            phis[name] = G.phi(profile)
            brackets[name] = G.root_interval(profile)
        with localcontext() as context:
            context.prec = 90
            lam = Decimal(definitions['D1-fixed-lambda']['lambda'])
            edges = []
            for before, after in definitions['D1-fixed-lambda']['edges']:
                exact = roots[after] - roots[before]
                predicted = lam * (phis[after] - phis[before])
                error = abs(predicted - exact) / abs(exact) if exact else None
                passes = ((error <= Decimal('.02') and sign(exact) == sign(predicted))
                          if exact else abs(predicted) <= Decimal('1e-30'))
                edges.append(dict(before=before,after=after,exact_margin=str(exact),
                    predicted_margin=str(predicted),relative_error=str(error) if error is not None else None,
                    matching_sign=sign(exact)==sign(predicted),outcome='PASS' if passes else 'FAIL'))
            names = ['2802','2833','2853']
            bad_order = [[a,b] for i,a in enumerate(names) for b in names[i+1:]
                         if sign(roots[a]-roots[b]) != sign(phis[a]-phis[b])]
        outcomes.append(dict(id='D1-fixed-lambda',outcome='PASS' if
            all(e['outcome']=='PASS' for e in edges) and not bad_order else 'FAIL',
            edges=edges,lambda_value=str(lam),pairwise_order_disagreements=bad_order,
            roots={k:str(v) for k,v in roots.items()},phi={k:str(v) for k,v in phis.items()},
            root_brackets=brackets,cpu_seconds=time.process_time()-t0))
    else:
        outcomes.append(dict(id='D1-fixed-lambda',outcome='UNRESOLVED',
            reason='Frozen coefficient requires the preregistered common geometry.',
            cpu_seconds=time.process_time()-t0))
    t0 = time.process_time()
    scalar = [dict(pr=name,calls=item['calls'],distinct_local_profiles=item['distinct_local_profiles'],
        stage_orientation_profiles=item['stage_orientation_profiles'],
        outcome='PASS' if item['calls']==666 and len(item['distinct_local_profiles'])==1 else 'FAIL')
        for name,item in sorted(packages.items())]
    outcomes.append(dict(id='D2-scalar-profile',packages=scalar,
        outcome='PASS' if all(x['outcome']=='PASS' for x in scalar) else 'FAIL',
        cpu_seconds=time.process_time()-t0,
        scope='Dispatched local paid profiles only; no recursive child-type inheritance claim.'))
    t0 = time.process_time()
    definition = definitions['D3-fixed-class-exit']
    baseline = definition['fixed_class']
    ceiling = Fraction(definition['certified_ceiling'])
    class_rows = []
    for name,item in sorted(packages.items()):
        changes = {}
        for key in ('aggregate_local_profile','role_width_counts','capacity_counts'):
            changes[key] = G.clean(item[key]) != G.clean(baseline[key])
        for key in ('dimension','wires','calls','coverage_rank_mass'):
            changes[key] = item[key] != baseline[key]
        profile = profiles[name]
        if item['dimension']==73 and all(0<r<73 for r in profile):
            upper = sum(Fraction(c)*M.rational_cost(r,str(ceiling))[1] for r,c in profile.items())
            lower = sum(Fraction(c)*M.rational_cost(r,str(ceiling))[0] for r,c in profile.items())
            above = upper < item['wires']
            not_above = lower >= item['wires']
            certified = above or not_above
        else:
            upper=lower=None;above=False;certified=False
        input_change = changes['aggregate_local_profile'] or changes['role_width_counts']
        implication = (not above) or any(changes.values())
        outcome = ('PASS' if input_change and implication else 'FAIL') if certified else 'UNRESOLVED'
        class_rows.append(dict(pr=name,outcome=outcome,changed_fixed_inputs=changes,
            frozen_ceiling=str(ceiling),moment_lower_at_ceiling=str(lower),
            moment_upper_at_ceiling=str(upper),wires=item['wires'],
            root_strictly_above_ceiling_certified=above,comparison_resolved=certified,
            class_implication_holds=implication,
            proof='Exact rational rank-cost enclosure; positive-profile moment increases in exponent.'))
    class_status = ('UNRESOLVED' if any(x['outcome']=='UNRESOLVED' for x in class_rows)
                    else 'PASS' if all(x['outcome']=='PASS' for x in class_rows) else 'FAIL')
    outcomes.append(dict(id='D3-fixed-class-exit',packages=class_rows,outcome=class_status,
                         cpu_seconds=time.process_time()-t0))
    return dict(status='EXPLORATORY',seed=seed,packages=packages,outcomes=outcomes,
        validation_cpu_seconds=audit_cpu,solver_calls=0,eligible_patterns=0,
        scope='Predeclared bookkeeping transfer; no five-criterion structural pattern or new candidate price.')


def main():
    global PROTOCOL, IMPLEMENTATION, ATTEMPT
    parser=argparse.ArgumentParser()
    parser.add_argument('--attempt',choices=('v1','v2'),default='v1')
    ATTEMPT=parser.parse_args().attempt
    if ATTEMPT != 'v1':
        IMPLEMENTATION=R.RESULTS/('M4/IMPLEMENTATION-'+ATTEMPT+'.json')
    run_directory=R.RESULTS/'M4-PRED'/ATTEMPT
    milestone_directory=R.RESULTS/'M4' if ATTEMPT=='v1' else R.RESULTS/'M4'/ATTEMPT
    pre = read(PREG)
    PROTOCOL = pre['protocol']
    if R.sha256(SNAPSHOT) != pre['prediction_snapshot']['sha256']:
        raise ValueError('frozen prediction snapshot changed')
    if datetime.now(timezone.utc) >= datetime.fromisoformat(PROTOCOL['hard_stop_utc']):
        raise RuntimeError('registered hard stop reached')
    implementation = read(IMPLEMENTATION)
    if implementation['preregistration_sha256'] != R.sha256(PREG):
        raise ValueError('implementation is not bound to the frozen protocol')
    for source in implementation['heldout_manifests']:
        if R.sha256(R.PKG/source['path']) != source['sha256']:
            raise ValueError('held-out source manifest changed: '+source['path'])
    amendment=None
    if ATTEMPT!='v1':
        amendment=implementation['amendment']
        amendment_path=R.PKG/amendment['path']
        if R.sha256(amendment_path)!=amendment['sha256']:
            raise ValueError('amendment hash changed')
        amended=read(amendment_path)
        if amended['state']!='FROZEN' or amended['applies_to']!=ATTEMPT or amended['preregistration_sha256']!=R.sha256(PREG):
            raise ValueError('attempt lacks an applicable frozen amendment')
    required = ['records.py','pool.py','growth.py','growth_m3.py','wordio.py',
                'fill.py','heldout_data.py','run_m4.py']
    for name in required:
        path=R.PKG/'pipeline'/name
        if implementation['script_sha256'][str(path.relative_to(R.ROOT))] != R.sha256(path):
            raise ValueError('source drift: '+name)
    for seed in SEEDS:
        if (run_directory/('seed-'+str(seed))/'RESULT.json').exists():
            raise FileExistsError('M4 receipts already exist; no silent repetition')
    prior_paths=sorted((R.RESULTS/'M4-PRED').glob('*/seed-*/RESULT.json'))
    prior_cpu=sum(read(path)['cpu_seconds'] for path in prior_paths)
    R.registry_update('M4-PRED','running')
    c0,w0=cpu(),time.monotonic()
    prepared=None;observed={};failure=None;projection=None
    try:
        prepared=H.prepare()
        projection=pool.project_memory(pool.worker_count(),rss_gib=6,working_set_gib=1)
        R.write_json(milestone_directory/'PREPARATION.json',dict(prepared,source=reference(IMPLEMENTATION),
            cpu_seconds=cpu()-c0,memory_projection=projection,parent_objects_loaded_once=True,
            protocol_amendment=amendment,prior_attempt_cpu_seconds=prior_cpu),immutable=True)
        remaining=7200-prior_cpu-(cpu()-c0)
        def checkpoint(index,value):
            observed[index]=value
            R.write_json(run_directory/('seed-'+str(SEEDS[index]))/'TASK.json',value,immutable=True)
            print(json.dumps(dict(seed=SEEDS[index],task_status=value['status'])),flush=True)
        pool.run_pool(task,[(s,) for s in SEEDS],workers=pool.worker_count(),timeout=600,rss_gib=6,
            working_set_gib=1,projection_path=milestone_directory/'MEMORY-PROJECTION.json',
            on_result=checkpoint,cpu_budget_seconds=remaining)
    except BaseException as exc:
        failure=dict(error=traceback.format_exc(),kind=type(exc).__name__)
        R.write_json(milestone_directory/'FAILURE.json',failure,immutable=True)
    elapsed=cpu()-c0;wall=time.monotonic()-w0
    worker_total=sum((v.get('cpu_seconds') or 0) for v in observed.values())
    overhead=max(0,elapsed-worker_total)/len(SEEDS)
    attribution=R.provenance()+((prepared or {}).get('source_attribution',[]))
    blob_ids={p['path']:p['git_blob'] for p in attribution}
    scripts=R.source_manifest();paths=[];seed_outcomes=[]
    for i,seed in enumerate(SEEDS):
        item=observed.get(i,dict(status='TIMEOUT' if failure and 'Timeout' in failure['kind'] else 'ERROR',
                                 error=failure,cpu_seconds=0,peak_rss_bytes=None))
        outcome=item.get('result',{})
        status=outcome.get('status','EXPLORATORY') if item['status']=='OK' else item['status']
        paths.append(R.run_record('M4-PRED','M4',seed,status,
            dict(tasks=[item],preparation=prepared,failure=failure,memory_projection=projection,
                 family_cpu_seconds=elapsed,prior_attempt_cpu_seconds=prior_cpu,
                 cumulative_family_cpu_seconds=prior_cpu+elapsed,protocol_amendment=amendment,
                 eligible_patterns=0,implementation=reference(IMPLEMENTATION)),
            cpu_seconds=(item.get('cpu_seconds') or 0)+overhead,wall_seconds=wall,
            peak_rss_bytes=max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                               item.get('peak_rss_bytes') or 0),run_id=ATTEMPT+'/seed-'+str(seed),scripts=scripts,
            decision=dict(verdict=status,pass_bar=PROTOCOL['decisions'],outcomes=outcome.get('outcomes',[])),
            additional=dict(source_attribution=attribution,word_blob_ids=blob_ids,
                heldout_source_files=(prepared or {}).get('source_files',[]))))
        seed_outcomes.append(dict(seed=seed,outcomes=outcome.get('outcomes',[]),result=reference(paths[-1])))
    final_status=R.confirm('M4-PRED',paths)
    current=read(SNAPSHOT)
    current.update(state='COMPLETED',completed_utc=R.utcnow(),outcomes=seed_outcomes,
        preregistration=reference(PREG),frozen_prediction_snapshot=reference(SNAPSHOT),
        implementation=reference(IMPLEMENTATION),status=final_status,
        source_attribution=attribution,eligible_pattern_count=0,protocol_amendment=amendment,
        preserved_prior_attempts=[reference(path) for path in prior_paths])
    current['confirmation']={p['id']: dict(
        outcomes=[next((o['outcome'] for o in row['outcomes'] if o['id']==p['id']),'UNRESOLVED')
                  for row in seed_outcomes],
        confirmed=len({next((o['outcome'] for o in row['outcomes'] if o['id']==p['id']),'UNRESOLVED')
                       for row in seed_outcomes})==1 and all(
            next((o['outcome'] for o in row['outcomes'] if o['id']==p['id']),'UNRESOLVED')
            in ('PASS','FAIL') for row in seed_outcomes))
        for p in current['predictions']}
    R.write_json(R.RESULTS/'PREDICTIONS.json',current)
    print(json.dumps(dict(status=final_status,cpu_seconds=elapsed,wall_seconds=wall,
                          confirmation=current['confirmation'])),flush=True)


if __name__=='__main__':
    main()
