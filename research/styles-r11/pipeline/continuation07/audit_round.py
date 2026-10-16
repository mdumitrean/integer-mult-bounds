"""Administrative saved-artifact audit for CONTINUATION-07; no scientific imports.

Run only after the registry and final reports are closed. --write creates the
immutable AUDIT.json once; repeats compare the stable payload without rewriting.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG=Path(__file__).resolve().parents[2]
ROOT=PKG.parents[1]
ROUND=PKG/'results/CONTINUATION-07'
BASE='bbc18613878c80f4540da0604db8de74a73bb20c'
FAMILIES={'ML1-HISTORICAL-CONTROLS':'ML1','ML2-RELEASE-COMPARISON':'ML2'}
SEEDS={37003,74017}
IGNORE={'seed','cpu_seconds','wall_seconds','elapsed_seconds','seconds','recorded_utc'}
CHECKED_REFS=set()


def need(ok,message):
    if not ok:raise ValueError(message)


def digest(raw):return hashlib.sha256(raw).hexdigest()


def read(path):
    raw=path.read_bytes();return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def clean(x):
    if isinstance(x,list):return [clean(v) for v in x]
    if isinstance(x,dict):return {k:clean(v) for k,v in x.items() if k not in IGNORE}
    return x


def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)


def reference(ref):
    p=Path(ref['path']);p=(ROOT/p if str(p).startswith('research/styles-r11/') else PKG/p).resolve()
    need(p.is_relative_to(PKG),'local artifact confinement')
    raw=p.read_bytes();need(digest(raw)==ref['sha256'],'artifact hash: '+str(p))
    if 'bytes' in ref:need(len(raw)==ref['bytes'],'artifact size: '+str(p))
    if 'payload_sha256' in ref:
        payload=gzip.decompress(raw) if p.suffix=='.gz' else raw
        need(digest(payload)==ref['payload_sha256'],'artifact payload hash: '+str(p))
    CHECKED_REFS.add(str(p.relative_to(PKG)));return p


def references(x):
    if isinstance(x,dict):
        if isinstance(x.get('path'),str) and isinstance(x.get('sha256'),str):
            if x['path'].startswith(('data/','results/','pipeline/','research/styles-r11/')):
                reference(x)
        for v in x.values():references(v)
    elif isinstance(x,list):
        for v in x:references(v)


def original_credits(result,original):
    credits={x['path']:x for x in result['source_attribution']}
    for name,pin in original.items():
        need(name in credits and all(credits[name].get(k)==v for k,v in pin.items()),
             'all21 original source attributions retained')
    return len(credits)


def audit_attempt(experiment,label,attempt,original,cohort):
    version=attempt['attempt'];run=ROUND/experiment/version
    meta=read(run/'RUN.json');preg_path=ROUND/label/'PREREGISTRATION.json';preg=read(preg_path)
    implementation=read(run/'IMPLEMENTATION.json');pins_path=ROUND/label/('IMPLEMENTATION-PINS-'+version+'.json')
    pins=read(pins_path);preg_sha=digest(preg_path.read_bytes());pins_sha=digest(pins_path.read_bytes())
    need(preg['state']=='FROZEN' and set(preg['seeds'])==SEEDS,'fixed registration and seeds')
    need(implementation['preregistration_sha256']==preg_sha and implementation['implementation_pins_sha256']==pins_sha,'implementation registration bindings')
    need(implementation['script_sha256']==pins['sha256'],'exact prepinned source inventory')
    need(pins.get('freeze_before_import_or_preparation') is True,'preparation freeze declaration')
    frozen_time=pins.get('registered_utc',pins.get('recorded_utc'))
    need(datetime.fromisoformat(preg['registered_utc'])<=datetime.fromisoformat(frozen_time),'registration precedes implementation freeze')
    source_archives=set();historical_preimages=[]
    for name,expected in pins['sha256'].items():
        raw=gzip.decompress((ROUND/'SOURCES'/(expected+'.py.gz')).read_bytes())
        need(digest(raw)==expected,'immutable source archive: '+name);source_archives.add(expected)
        current=ROOT/name
        if not current.exists() or digest(current.read_bytes())!=expected:
            need(name.endswith(('/audit_round.py','/final_checkpoint.py','/build_release_cohort.py')),
                 'scientific source changed after freeze: '+name)
            historical_preimages.append(name)
    references(preg.get('inputs',{}));references(implementation)
    prepared=implementation['prepared']
    if label=='ML1':need(set(prepared)=={'dataset','history','learner'},'one parent preparation receipt for each ML1 component')
    else:need(implementation.get('parent_load_once') is True and 'features' in prepared,'ML2 parent preparation recorded once')
    phases={phase:read(run/(phase.upper()+'-TASKS.json.gz')) for phase in meta['completed_by_phase']}
    visits={phase:set() for phase in phases};seed_results={};tasks=[];statuses=Counter();rss=[];seconds=[];cpu=0.
    for ref in meta['results']:
        result=read(reference(ref));seed=result['seed'];need(seed not in seed_results,'unique seed RESULT')
        seed_results[seed]=result;cpu+=result['cpu_seconds']
        need(result['status']==meta['status']==attempt['status'],'RUN/RESULT/registry attempt status agreement')
        need(result['script_sha256']==pins['sha256'] and result['implementation_pins_sha256']==pins_sha and result['preregistration_sha256']==preg_sha,'RESULT frozen sources and protocol')
        need(datetime.fromisoformat(result['recorded_utc'])>=datetime.fromisoformat(frozen_time),'freeze precedes result')
        need(result['source_attribution']==implementation['source_attribution'],'implementation/RESULT original source credit equality')
        original_credits(result,original)
        need(result['decision']['pattern_claim'] is False and result['decision']['kappa_claim'] is False,'retrospective scope not promoted')
        if label=='ML2':need(result['release_source_attribution']==cohort,'all complete cohort source credits retained in each RESULT')
        references(result.get('inputs',{}));references(result.get('statistics',{}))
        for taskref in result['task_receipts']:
            path=reference(taskref);phase=path.parent.name;need(phase in phases,'declared task phase')
            index=int(path.name.split('.')[0].split('-')[-1]);need(0<=index<len(phases[phase]) and index not in visits[phase],'unique exact task index')
            visits[phase].add(index);spec=phases[phase][index];receipt=read(path)
            need(spec['seed']==seed,'task seed agrees with RESULT ownership')
            statuses[receipt['status']]+=1;rss.append(receipt.get('peak_rss_bytes') or 0);seconds.append(receipt.get('seconds') or 0)
            if receipt['status']=='OK':
                value=receipt['result'];need(value['seed']==seed,'saved task output seed');references(value)
                tasks.append((phase,spec,value,receipt))
            else:need(meta['failure'] is not None,'pool infrastructure error preserved, not scientific negative')
        mine=[(p,s,v) for p,s,v,_ in tasks if s['seed']==seed]
        need(result['n_permutations']==sum(s.get('permutation') is not None for _,s,_ in mine),'RESULT permutation coverage')
    need(set(seed_results)==SEEDS,'both distinct registered seeds retained')
    need(abs(cpu-meta['total_cpu_seconds'])<1e-5 and abs(cpu-attempt['cpu_seconds'])<1e-5,'exact experimental CPU accounting')
    need(abs(meta['total_wall_seconds']-attempt['wall_seconds'])<1e-8,'wall accounting')
    need(meta['workers']==61,'61-worker central pool recorded')
    for phase,seen in visits.items():need(len(seen)==meta['completed_by_phase'][phase],'all completed task receipts included exactly once')
    need(sum(len(v) for v in visits.values())==sum(meta['completed_by_phase'].values()),'pool receipt closure')
    projections=[]
    for p in sorted(run.glob('*MEMORY-PROJECTION.json')):
        v=read(p);need(v['workers']==min(120,int(v['ram_gib']//4))==61 and v['reserved_cores']>=8,'RAM/core worker rule')
        need(v['worker_rss_cap_gib']==4 and v['projected_peak_gib']<v['ram_gib'],'RSS and projected RAM bounds')
        projections.append(dict(path=str(p.relative_to(PKG)),sha256=digest(p.read_bytes()),projected_peak_gib=v['projected_peak_gib']))
    need(len(projections)==len(phases)+1,'parent and every pool launch have a projection')
    need(max(rss,default=0)<=4*1024**3,'all completed worker RSS receipts within cap')
    need(max(seconds,default=0)<=301,'all tasks within300-second timeout including receipt overhead')
    completed=meta['failure'] is None
    summary=dict(attempt=version,status=meta['status'],pool_tasks=sum(meta['completed_by_phase'].values()),
      completed_by_phase=meta['completed_by_phase'],pool_status_counts=dict(statuses),cpu_seconds=cpu,
      wall_seconds=meta['total_wall_seconds'],max_worker_rss_bytes=max(rss,default=0),max_task_seconds=max(seconds,default=0),
      memory_projections=projections,source_preimages_used=historical_preimages,
      source_credits_per_result={str(s):len(r['source_attribution']) for s,r in seed_results.items()})
    if not completed:
        need(meta['status'] in {'ERROR','TIMEOUT'} and not meta['confirmed'],'failed attempt explicitly preserved')
        summary['failure']=meta['failure'];return summary,source_archives
    need(meta['status']=='EXPLORATORY' and meta['confirmed'] is True,'completed ML remains exploratory')
    need(all(r['confirmed'] is True and r['scientific_decision_agreement'] is True and r['failure'] is None for r in seed_results.values()),'confirmed two-seed scoped decisions')
    for phase,spec,value,_ in tasks:
        if 'controls' in phase:need(value['status']=='PASS','all preregistered controls pass')
    n=preg['n_permutations']
    expected={'controls':6,'history':2,'observed':4,'permutations':2*n} if label=='ML1' else {
        'feature_controls':2,'features':2*sum(len(e['providers']) for e in cohort['entries']),
        'model_controls':2,'observed':2,'permutations':2*n}
    need(meta['completed_by_phase']==expected,'complete exact preregistered phase inventory')
    for phase,specs in phases.items():need(visits[phase]==set(range(len(specs))),'no omitted phase task')
    for seed in sorted(SEEDS):
        perm=[(s,v) for p,s,v,_ in tasks if p=='permutations' and s['seed']==seed]
        need({s['permutation'] for s,v in perm}==set(range(n)) and len(perm)==n,'every indexed permutation exactly once')
        observed=[v for p,s,v,_ in tasks if p=='observed' and s['seed']==seed]
        stats=seed_results[seed]['statistics'];need(stats==meta['statistics'][str(seed)],'RUN statistics match saved RESULT')
        if label=='ML1':
            primary=next(v for v in observed if v['target']=='frame_legal');secondary=next(v for v in observed if v['target']=='worse')
            need(len(observed)==2,'both fixed targets, no selected model')
            values=[v['delta_auroc'] for _,v in perm]
            p=(1+sum(v>=primary['delta_auroc'] for v in values))/(n+1)
            need(abs(p-stats['null_summary']['empirical_p'])<1e-15,'saved primary permutation p arithmetic')
            diagnostic=primary['delta_auroc']>=.05 and primary['delta_balanced_log_loss']>=.01 and p<=.01
            need(diagnostic==stats['diagnostic_bar_met'],'original diagnostic bar exactly applied')
        else:
            need(len(observed)==1,'one fixed release analysis')
            for scheme,report in observed[0]['grouped_validation'].items():
                calibration=stats['null_summary'][scheme]
                if report['status']!='PASS_GROUPED_OOF':need(calibration['status']=='UNASSESSABLE','unassessable grouped scheme censored');continue
                values=[v['grouped_validation'][scheme]['primary_statistic'] for _,v in perm]
                p=(1+sum(v>=report['primary_statistic'] for v in values))/(n+1)
                need(abs(p-calibration['empirical_p'])<1e-15 and calibration['status']=='DESCRIPTIVE_ONLY','release null arithmetic and noninferential scope')
    if label=='ML1':
        bars=[seed_results[s]['statistics']['diagnostic_bar_met'] for s in sorted(SEEDS)];need(bars[0]==bars[1],'two-seed diagnostic agreement')
        history=[v for p,s,v,_ in tasks if p=='history'];need(clean(history[0])==clean(history[1]),'historical exact arithmetic repeats')
    else:
        pairs={}
        for phase,spec,value,_ in tasks:
            if phase=='features':pairs.setdefault((value['pr'],value['provider']),{})[spec['seed']]=value
        wanted={(e['pr'],v) for e in cohort['entries'] for v in e['providers']}
        need(set(pairs)==wanted,'all and only registered release/provider pairs')
        for key,values in pairs.items():need(set(values)==SEEDS and clean(values[37003])==clean(values[74017]),'exact two-seed paired features: '+str(key))
        observed=[v for p,s,v,_ in tasks if p=='observed'];need(clean(observed[0])==clean(observed[1]),'deterministic observed release analysis repeats')
        summary['paired_release_provider_count']=len(pairs)
    return summary,source_archives


def audit_cohort():
    path=ROUND/'planning/RELEASE-COHORT.json';cohort=read(path);references(cohort)
    need(len(cohort['entries'])==12 and len({e['pr'] for e in cohort['entries']})==12,'twelve distinct complete source releases')
    receipt_matches=0
    for entry in cohort['entries']:
        labels=entry['labels'];need(labels['tier']=='SOURCE_REPORTED_CONDITIONAL_COMPLETE_FINITE_RELEASE' and labels['source_reported_only'] is True,'no source claim admission promotion')
        need(labels['matched_parent_pr']==entry['parent_pr'] and labels['structural_parent_match'] is True,'matched structural parent binding')
        before,after,gain=(Fraction(labels[k]) for k in ('kappa_before','kappa_after','matched_parent_gain'))
        need(after-before==gain and gain>0,'exact parent-matched published gain arithmetic')
        claim=read(reference(labels['claim_refs'][1]));need(claim['release_receipt_sha256'] in {r['sha256'] for r in entry['release_receipts']},'candidate full receipt bound to exact claim')
        receipt_matches+=1
        if entry['pr']==2875:need(labels['structural_regression_eligible'] is False,'precision-only release censored from structural regression')
    need([e['pr'] for e in cohort['excluded_pending']]==[2969],'outer-pending comparator remains excluded')
    acquired=0;blob_checks=0
    for pin in cohort['source_acquisitions']:
        acquisition=read(reference(pin))
        for file in acquisition['files']:
            p=reference(file);raw=p.read_bytes();need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==file['git_blob'],'all acquired data retain exact Git blob identities')
            need(p.suffix!='.py','remote programs never executable source paths');acquired+=len(raw);blob_checks+=1
    need(acquired<15000000,'bounded historical acquisition payload')
    return cohort,dict(sha256=digest(path.read_bytes()),releases=12,provider_pairs=24,exact_claim_release_receipt_matches=receipt_matches,
        acquired_file_blob_checks=blob_checks,acquired_payload_bytes=acquired,source_reported_only=True)


def build_audit():
    CHECKED_REFS.clear();registry=read(ROUND/'EXPERIMENTS.json');task=read(ROUND/'TASK.json')
    need(registry['no_active_experiments'] and task['base_work_commit']==BASE,'closed pools and exact pre-round base')
    need('RUNNING' not in registry.get('status','').upper(),'registry is final before administrative write')
    original=read(PKG/'data/words/PINS.json')['files'];need(len(original)==21,'all original attributions')
    cohort,cohort_report=audit_cohort();reports={};archives=set();cpu=0.;total_tasks=0
    for experiment,label in FAMILIES.items():
        row=next(x for x in registry['experiments'] if x['id']==experiment)
        need(row.get('execution')=='COMPLETED' and row['status']=='EXPLORATORY','each completed retrospective family closed without promoted claim')
        preg=ROUND/label/'PREREGISTRATION.json';need(row['preregistration_sha256']==digest(preg.read_bytes()),'registry preregistration hash')
        attempts=[]
        for attempt in row['attempts']:
            report,used=audit_attempt(experiment,label,attempt,original,cohort);attempts.append(report);archives.update(used)
            cpu+=report['cpu_seconds'];total_tasks+=report['pool_tasks']
        need(attempts[-1]['status']==row['status'] and abs(sum(a['cpu_seconds'] for a in attempts)-row['cpu_seconds'])<1e-5,'all attempts preserved and accounted')
        reports[experiment]=attempts
    need(cpu<task['round_cpu_budget_seconds'],'complete experimental CPU budget')
    tree=subprocess.check_output(['git','ls-tree','-rz',BASE,'--','research/styles-r11/'],cwd=ROOT)
    preserved=0
    for entry in tree.split(b'\0'):
        if not entry:continue
        info,name=entry.split(b'\t',1);_,kind,blob=info.split();need(kind==b'blob','ordinary base evidence file')
        raw=(ROOT/name.decode()).read_bytes();need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest().encode()==blob,'immutable previous-round evidence: '+name.decode());preserved+=1
    changed=subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    untracked=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith('research/styles-r11/') for p in changed+untracked),'authorized write confinement')
    documents={}
    for name in ['RESULTS.md','HANDBACK.md','PREDICTIONS.json','EXPERIMENTS.json','TASK.json']:
        documents[name]=digest((ROUND/name).read_bytes())
    checkpoints={}
    for label in ['checkpoint','final-checkpoint']:
        p=PKG/'data/continuation-07'/label/'RECEIPT.json';receipt=read(p);need(not receipt['errors'],'metadata checkpoint without unreported acquisition error')
        for relative,pin in receipt['files'].items():need(digest((p.parent/relative).read_bytes())==pin['sha256'],'checkpoint byte hash')
        checkpoints[label]=dict(sha256=digest(p.read_bytes()),canonical_main=receipt['canonical_main'],priority_revision=receipt.get('priority_revision'),files=len(receipt['files']))
    destination=ROUND/'AUDIT.json'
    result_bytes=sum(p.stat().st_size for p in (PKG/'results').rglob('*') if p.is_file() and p!=destination)
    round_bytes=sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file() and p!=destination)
    need(result_bytes<200000000 and round_bytes<18000000,'global and round artifact caps')
    return dict(schema_version=1,status='PASS',kind='Administrative saved-byte and receipt audit; no scientific reruns',
      script_sha256=digest(Path(__file__).read_bytes()),base_work_commit=BASE,preserved_pre_round_files=preserved,
      experiments=reports,cohort=cohort_report,source_checkpoints=checkpoints,final_documents=documents,
      source_archives_checked=len(archives),local_artifact_references_checked=len(CHECKED_REFS),
      total_pool_tasks=total_tasks,total_experimental_cpu_seconds=cpu,
      results_bytes_excluding_audit=result_bytes,round_bytes_excluding_audit=round_bytes)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    started=time.process_time();stable=build_audit();path=ROUND/'AUDIT.json'
    if path.exists():
        need(read(path)['stable']==stable,'immutable audit payload still agrees')
        print(json.dumps(dict(status='PASS',sha256=digest(path.read_bytes()),overwritten=False)));return
    value=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),administrative_cpu_seconds=time.process_time()-started,stable=stable)
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    need(stable['results_bytes_excluding_audit']+len(raw)<200000000 and stable['round_bytes_excluding_audit']+len(raw)<18000000,'storage including audit')
    if args.write:
        with path.open('xb') as out:out.write(raw)
    print(json.dumps(value,sort_keys=True))

if __name__=='__main__':main()
