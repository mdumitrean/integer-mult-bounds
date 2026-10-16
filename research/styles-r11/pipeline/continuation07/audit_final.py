"""Final administrative extension for ML2's coverage correction and ML3.

Only the hash-pinned earlier administrative auditor is imported. No scientific
module is imported or rerun. All v1/v2 source and result bytes remain immutable.
"""
import argparse
from datetime import datetime,timezone
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE=Path(__file__).resolve().parent
PREVIOUS=HERE/'audit_round.py'
PREVIOUS_SHA='d451f7ccea9c4ad01503624ca5caa150869b825c83df6a5790059d607b54addd'
if hashlib.sha256(PREVIOUS.read_bytes()).hexdigest()!=PREVIOUS_SHA:
    raise ValueError('immutable previous administrative auditor changed')
spec=importlib.util.spec_from_file_location('styles07_saved_artifact_audit',PREVIOUS)
A=importlib.util.module_from_spec(spec);spec.loader.exec_module(A)
PKG,ROOT,ROUND=A.PKG,A.ROOT,A.ROUND


def source_archives(pins):
    historical=[]
    for name,expected in pins['sha256'].items():
        raw=gzip.decompress((ROUND/'SOURCES'/(expected+'.py.gz')).read_bytes())
        A.need(A.digest(raw)==expected,'exact source archive: '+name)
        current=ROOT/name
        if not current.exists() or A.digest(current.read_bytes())!=expected:
            A.need(name.endswith(('/audit_round.py','/audit_final.py','/final_checkpoint.py','/build_release_cohort.py')),
                   'frozen scientific implementation changed: '+name)
            historical.append(name)
    return historical


def correction_audit():
    p=ROUND/'ML2/COVERAGE-CORRECTION-v2.json';value=A.read(p);A.references(value)
    run=ROUND/'ML2-RELEASE-COMPARISON/v2';implementation=A.read(run/'IMPLEMENTATION.json')
    reference={'path':str(p.relative_to(PKG)),'sha256':A.digest(p.read_bytes())}
    A.need(value['state']=='FROZEN' and value['prior_outputs_known'] is True,'honest registered post-v1 coverage repair')
    A.need(implementation['protocol_addendum']==reference,'coverage correction implementation binding')
    pins=A.read(ROUND/'ML2/IMPLEMENTATION-PINS-v2.json')
    A.need(datetime.fromisoformat(value['registered_utc'])<=datetime.fromisoformat(pins['registered_utc']),'correction frozen before v2 implementation')
    for ref in A.read(run/'RUN.json')['results']:
        result=A.read(A.reference(ref));A.need(result['protocol_addendum']==reference,'both seed coverage addendum bindings')
    # Saved feature and model reports are inspected; no extraction or fitting.
    rows=A.read(run/'RELEASE-FEATURES.json.gz')
    accepted={int(r['pr']) for r in rows if r['predictor_coverage']['regression_supported']}
    A.need(accepted=={2948,2957,2966},'conservative coverage accepts only the three fixed-fill releases')
    for row in rows:
        diagnostic=row['diagnostics']['allocation'];supported=row['predictor_coverage']['regression_supported']
        if supported:
            A.need(diagnostic['whole_gain_word_regression_fixed_allocation'] is True and
                   diagnostic['rows_comparable'] is True and diagnostic['moved_roles']==0 and
                   diagnostic['changed_offsets']==0,'coverage supported by saved literal identity checks')
    return dict(addendum=reference,prior_outputs_known=True,retained_v1=True,
                fixed_fill_regression_releases=sorted(accepted),source_scopes_not_relabelled=True)


def holdout_source(cohort):
    A.references(cohort);A.need(len(cohort['entries'])==1,'one post-cohort episode')
    entry=cohort['entries'][0];labels=entry['labels']
    A.need(entry['pr']==3015 and entry['parent_pr']==2979,'exact declared post-cohort pair')
    A.need(labels['outcome_known_before_registration'] is True and cohort['selection']['outcome_known_before_registration'] is True,'no blinded prediction claim')
    before,after,gain=(Fraction(labels[k]) for k in ['kappa_before','kappa_after','matched_parent_gain'])
    A.need(after-before==gain and gain>0 and labels['matched_parent_pr']==2979,'exact parent-matched complete claim difference')
    claim=A.read(A.reference(labels['claim_refs'][1]))
    A.need(claim['release_receipt_sha256'] in {r['sha256'] for r in entry['release_receipts']},'new source complete receipt hash')
    for name in ['fill','order','dispatch']:
        A.need(entry['allocation']['before']['artifacts'][name]['sha256']==entry['allocation']['after']['artifacts'][name]['sha256'],'exact unchanged holdout allocation '+name)
    count,size=0,0
    for ref in cohort['source_acquisitions']:
        acquisition=A.read(A.reference(ref));manifest_path=PKG/'data/continuation-07/holdout3015/package/MANIFEST.json';manifest=A.read(manifest_path)
        checked=0
        for file in acquisition['files']:
            path=A.reference(file);raw=path.read_bytes()
            A.need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==file['git_blob'],'post-cohort exact Git blob')
            A.need(path.suffix!='.py','remote programs remain inert')
            relative=file['source_path'].split('research/rank7-joint-endframes-restore-edit/',1)[1]
            if relative in manifest:
                A.need(manifest[relative]==file['sha256'],'selected post-cohort source manifest membership');checked+=1
            count+=1;size+=len(raw)
        A.need(checked==acquisition['manifest_entries_checked']==36 and len(acquisition['files'])==37,'compact selected3015source coverage')
    return dict(pr=3015,parent_pr=2979,exact_parent_gain=str(gain),acquired_files=count,
                acquired_bytes=size,source_only=True,outcome_known_before_registration=True)


def audit_ml3():
    label='ML3';experiment='ML3-OUT-OF-COHORT';registry=A.read(ROUND/'EXPERIMENTS.json')
    row=next(x for x in registry['experiments'] if x['id']==experiment)
    A.need(row['execution']=='COMPLETED' and row['status']=='EXPLORATORY','completed scoped post-cohort task')
    A.need(len(row['attempts'])==1,'unexpected attempt needs explicit preservation review')
    attempt=row['attempts'][0];run=ROUND/experiment/attempt['attempt'];meta=A.read(run/'RUN.json')
    preg_path=ROUND/label/'PREREGISTRATION.json';preg=A.read(preg_path);preg_sha=A.digest(preg_path.read_bytes())
    A.need(row['preregistration_sha256']==preg_sha and preg['state']=='FROZEN' and set(preg['seeds'])==A.SEEDS,'post-cohort frozen registration')
    pins_path=ROUND/label/('IMPLEMENTATION-PINS-'+attempt['attempt']+'.json');pins=A.read(pins_path);pinsha=A.digest(pins_path.read_bytes())
    implementation=A.read(run/'IMPLEMENTATION.json');source_archives(pins)
    A.need(implementation['script_sha256']==pins['sha256'] and implementation['implementation_pins_sha256']==pinsha and implementation['preregistration_sha256']==preg_sha,'post-cohort source binding')
    A.need(implementation['parent_load_once'] is True,'once-parent loading recorded')
    A.need(datetime.fromisoformat(preg['registered_utc'])<=datetime.fromisoformat(pins['registered_utc']),'registration precedes source freeze')
    A.references(preg['inputs']);A.references(implementation)
    cohort=A.read(A.reference(preg['inputs']['cohort']));source=holdout_source(cohort)
    original=A.read(PKG/'data/words/PINS.json')['files'];results={};tasks=[];cpu=0.;rss=[];seconds=[]
    expected={'feature_controls':2,'features':4,'predictions':2}
    A.need(meta['completed_by_phase']==expected and meta['workers']==61,'exact post-cohort pool inventory')
    specs={phase:A.read(run/(phase.upper()+'-TASKS.json.gz')) for phase in expected};visits={p:set() for p in specs}
    for ref in meta['results']:
        result=A.read(A.reference(ref));seed=result['seed'];A.need(seed not in results,'unique post-cohort seed');results[seed]=result;cpu+=result['cpu_seconds']
        A.need(result['status']==meta['status']==attempt['status']=='EXPLORATORY' and result['confirmed'] is True and result['scientific_decision_agreement'] is True and result['failure'] is None,'confirmed nonpromoted post-cohort status')
        A.need(result['script_sha256']==pins['sha256'] and result['implementation_pins_sha256']==pinsha and result['preregistration_sha256']==preg_sha,'post-cohort RESULT source binding')
        A.need(result['source_attribution']==implementation['source_attribution'] and result['release_source_attribution']==cohort,'all post-cohort source credits')
        A.original_credits(result,original);A.references(result['inputs']);A.references(result['statistics'])
        A.need(result['n_permutations']==0 and result['decision']['pattern_claim'] is False and result['decision']['kappa_claim'] is False,'no added inferential/κ claim')
        A.need(result['statistics']==meta['statistics'][str(seed)],'post-cohort RUN/RESULT statistics equality')
        for ref in result['task_receipts']:
            path=A.reference(ref);phase=path.parent.name;index=int(path.name.split('.')[0].split('-')[-1])
            A.need(phase in specs and 0<=index<len(specs[phase]) and index not in visits[phase],'unique registered post-cohort task')
            visits[phase].add(index);spec=specs[phase][index];receipt=A.read(path);value=receipt['result']
            A.need(receipt['status']=='OK' and spec['seed']==seed==value['seed'],'successful post-cohort task seed binding')
            tasks.append((phase,spec,value));rss.append(receipt['peak_rss_bytes']);seconds.append(receipt['seconds']);A.references(value)
    A.need(set(results)==A.SEEDS and meta['confirmed'] is True and meta['failure'] is None,'both registered post-cohort seeds')
    A.need(abs(cpu-meta['total_cpu_seconds'])<1e-5 and abs(cpu-row['cpu_seconds'])<1e-5 and abs(cpu-attempt['cpu_seconds'])<1e-5,'post-cohort CPU closure')
    for phase in expected:A.need(visits[phase]==set(range(expected[phase])),'every post-cohort task retained')
    for phase,spec,value in tasks:
        if phase=='feature_controls':A.need(value['status']=='PASS','post-cohort controls')
    features={}
    for phase,spec,value in tasks:
        if phase=='features':features.setdefault(value['provider'],{})[spec['seed']]=value
    A.need(set(features)=={'base','extra'},'both source providers')
    for provider,values in features.items():A.need(set(values)==A.SEEDS and A.clean(values[37003])==A.clean(values[74017]),'repeated source-bound features')
    predictions=[v for p,s,v in tasks if p=='predictions'];A.need(A.clean(predictions[0])==A.clean(predictions[1]),'exact deterministic prediction repeat')
    for value in predictions:
        A.need(value['training_release_ids']==['2948','2957','2966'] and value['release_id']=='3015','fixed separated training/holdout inventory')
        A.need(value['outcome_known_before_registration'] is True and value['blinded_prospective_validation'] is False and value['model_updated_with_heldout'] is False and value['tuning'] is False,'honest unblinded no-tuning scope')
        A.need(value['pattern_claim'] is False and value['kappa_claim'] is False,'no claim promotion')
    projections=[]
    for p in sorted(run.glob('*MEMORY-PROJECTION.json')):
        v=A.read(p);A.need(v['workers']==min(120,int(v['ram_gib']//4))==61 and v['reserved_cores']>=8 and v['worker_rss_cap_gib']==4 and v['projected_peak_gib']<v['ram_gib'],'post-cohort memory/core rule');projections.append(str(p.relative_to(PKG)))
    A.need(len(projections)==4 and max(rss)<=4*1024**3 and max(seconds)<=301,'post-cohort resource receipt limits')
    return dict(attempt=attempt['attempt'],status='EXPLORATORY',pool_tasks=8,completed_by_phase=expected,
        cpu_seconds=cpu,wall_seconds=meta['total_wall_seconds'],source=source,
        distinct_archived_sources=len(set(pins['sha256'].values())),outcome_known_before_registration=True,
        source_binding_and_seed_agreement='PASS',scientific_functions_rerun=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--write',action='store_true');args=parser.parse_args()
    started=time.process_time();path=ROUND/'AUDIT.json'
    if args.write:
        raw=Path(__file__).read_bytes();archive=ROUND/'SOURCES'/(A.digest(raw)+'.py.gz')
        if not archive.exists():
            with archive.open('xb') as out:out.write(gzip.compress(raw,mtime=0))
    stable=A.build_audit();stable['administrative_base_script_sha256']=PREVIOUS_SHA
    stable['script_sha256']=A.digest(Path(__file__).read_bytes());stable['coverage_correction']=correction_audit()
    extra=audit_ml3();stable['experiments']['ML3-OUT-OF-COHORT']=[extra]
    stable['total_pool_tasks']+=extra['pool_tasks'];stable['total_experimental_cpu_seconds']+=extra['cpu_seconds']
    A.need(stable['total_experimental_cpu_seconds']<14400,'all-family CPU budget')
    A.need(stable['cohort']['acquired_payload_bytes']+extra['source']['acquired_bytes']<15000000,'bounded combined compact release acquisition')
    A.need(set(stable['experiments'])=={r['id'] for r in A.read(ROUND/'EXPERIMENTS.json')['experiments']},'every registered family audited')
    all_archives=set()
    for family,label in {'ML1-HISTORICAL-CONTROLS':'ML1','ML2-RELEASE-COMPARISON':'ML2','ML3-OUT-OF-COHORT':'ML3'}.items():
        registry_row=next(r for r in A.read(ROUND/'EXPERIMENTS.json')['experiments'] if r['id']==family)
        for attempt in registry_row['attempts']:
            all_archives.update(A.read(ROUND/label/('IMPLEMENTATION-PINS-'+attempt['attempt']+'.json'))['sha256'].values())
    stable['source_archives_checked']=len(all_archives)
    stable['local_artifact_references_checked']=len(A.CHECKED_REFS)
    if path.exists():
        A.need(A.read(path)['stable']==stable,'immutable final administrative payload still matches')
        print(json.dumps(dict(status='PASS',sha256=A.digest(path.read_bytes()),overwritten=False)));return
    value=dict(recorded_utc=datetime.now(timezone.utc).isoformat(),administrative_cpu_seconds=time.process_time()-started,stable=stable)
    raw=(json.dumps(value,indent=2,sort_keys=True)+'\n').encode()
    A.need(stable['results_bytes_excluding_audit']+len(raw)<200000000 and stable['round_bytes_excluding_audit']+len(raw)<18000000,'storage including final audit')
    if args.write:
        with path.open('xb') as out:out.write(raw)
    print(json.dumps(value,sort_keys=True))

if __name__=='__main__':main()
