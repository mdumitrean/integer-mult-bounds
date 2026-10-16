"""Administrative exact-source cohort assembly; no scientific feature extraction."""
import pathlib,json,gzip,hashlib,datetime
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[2]
O=R/'results/CONTINUATION-07/planning/RELEASE-COHORT.json'
def read(p):
 b=(R/p).read_bytes();return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def ref(p):
 p=pathlib.Path(p);b=(R/p).read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
metadata={x['number']:x for x in read('data/continuation-03/checkpoint/all-prs-reconciled.json.gz')}
for p in ['data/continuation-07/checkpoint/pr-2979.json.gz','data/continuation-04/checkpoint/pr-2966.json.gz']:
 if not (R/p).exists():continue
 m=read(p);metadata[m['number']]={'head':m['head']['sha'],'author':m['user']['login'],'created_at':m['created_at'],'title':m['title']}
# Exact acquired package locations. Different allocation normalizations remain explicit.
P={n:f'data/continuation-07/releases/pr{n}/package' for n in [2857,2863,2875,2894,2908,2948]}
P.update({2917:'data/continuation-01/pr2917/package',2957:'data/continuation-03/checkpoint/pr2957/package',2966:'data/continuation-04/pr2966/package',2979:'data/continuation-05/pr2979/package'})
C={n:P[n]+'/CLAIM.json' for n in P}
C.update({2833:'data/heldout/2833/package/outer/OUTER-CLAIM.json',2930:'data/continuation-02/checkpoint/pr2930/CLAIM.json',2942:P[2979]+'/comparators/PR2942-CLAIM.json'})
claims={n:read(p) for n,p in C.items()}
words={}
for n in [2857,2894,2908,2917,2948,2957,2966,2979]:
 sub='words/WORD-' if n==2857 else 'vendor/pm/words/WORD-PM-' if n==2894 else 'rewrite/FINAL-WORD-' if n in [2948,2957,2966] else 'data/WORD-'
 words[n]={v:P[n]+'/'+sub+v+'.json.gz' for v in ['base','extra']}
words[2833]={v:f'data/heldout/2833/package/new/borrow/words/BORROW-WORD-43{v}.json.gz' for v in ['base','extra']}
words[2863]=dict(words[2857]);words[2875]=dict(words[2857]);words[2930]=dict(words[2917]);words[2942]={v:P[2979]+f'/data/PARENT-{v}.json.gz' for v in ['base','extra']}
allocdirs={2857:P[2857],2863:P[2863]+'/data',2875:P[2863]+'/data',2894:P[2894]+'/data',2908:P[2908]+'/allocation',2917:P[2917]+'/allocation',2930:P[2957]+'/allocation',2942:P[2966]+'/allocation',2948:P[2957]+'/allocation',2957:P[2957]+'/allocation',2966:P[2966]+'/allocation',2979:P[2979]+'/allocation',2833:'data/heldout/2833/package/new/borrow-fill'}
parents={2979:2942,2966:2942,2957:2930,2948:2930,2942:2930,2930:2917,2917:2908,2908:2894,2894:2863,2875:2863,2863:2857,2857:2833}
mechanism={2979:'joint_endpoint_lowering_paired_extraction_and_declared_rewrites',2966:'declared_rewrites_on_paired_endpoint_word',2957:'declared_gate_rewrites',2948:'declared_gate_rewrites',2942:'shared_paired_endpoint_extraction',2930:'allocation_only',2917:'paired_extractions_and_frame_substitutions',2908:'paired_input_output_helper_extraction',2894:'preload_resynthesis_and_allocation',2875:'precision_only',2863:'allocation_only',2857:'shared_kernel_rewrite_and_allocation'}
heads={2833:'e9307b48d7d1b690939935ecef0f8e524e6d92f4',2966:'e62d3eb9005117d82a9babcfa937ecc53237c490',2979:'be191346391661f4d35fc0d1508d0a6029572576'}
meta_fallback={2966:('jeremykothe2',None),2979:('mdumitrean',None)}
def author(n):return metadata.get(n,{}).get('author',meta_fallback.get(n,('jeremykothe2',None))[0])
def head(n):return metadata.get(n,{}).get('head',heads.get(n))
def kappa(n):return str(Fraction(claims[n]['kappa_rational'] if n==2833 else claims[n]['kappa']))
credits={}
for n in parents:
 dirs=[R/P[n]] if n in P else [R/(P[2979] if n==2942 else 'data/continuation-02/checkpoint/pr2930')]
 paths=[]
 for d in dirs:
  for f in d.rglob('*'):
   if f.is_file() and (f.name in ['CREDITS.md','NOTICE','SOURCES.json'] or 'CREDITS' in f.name or f.name.endswith('-NOTICE')):paths.append(str(f.relative_to(R)))
 credits[n]=[ref(p) for p in sorted(set(paths))]
pins=ref('data/words/PINS.json');pin_data=read('data/words/PINS.json')
def attribution(n):
 return {'pr':n,'head':head(n),'author':author(n),'source_url':f'https://github.com/CrocSwap/integer-mult-bounds/pull/{n}','original_pins':pins,'credit_files':credits.get(n,[]),'credit_scope':'Named author plus every original PINS credit and complete linked acquired CREDITS/NOTICE/SOURCES; retained predecessor attribution is not replaced.'}
def wordref(n,v):
 z=ref(words[n][v]);z['attribution']=attribution(n);z['provider']=v;z['artifact_kind']='inert_json_word';return z
def allocation(n):
 a={'normalization':{'replicas':claims[n].get('replicas',37),'calls':claims[n].get('calls',333),'live_families':claims[n].get('live_families',claims[n].get('live',33152 if n==2833 else None))},'artifacts':{},'missingness':[],'complete_profile_source':dict(ref(C[n]),field='profile' if 'profile' in claims[n] else 'paid_profile' if 'paid_profile' in claims[n] else 'complete profile separately in allocation PROFILE; claim root is complete outer'),'attribution':attribution(n)}
 if n==2875:a['normalization']={'replicas':185,'calls':1665,'live_families':165760}
 for key,name in [('fill','FILL.json.gz'),('order','ORDER.json'),('dispatch','DISPATCH.json'),('providers','PROVIDERS.json')]:
  p=allocdirs[n]+'/'+name
  if n==2930 and key=='fill':p='data/continuation-02/packing-source/FILL.json.gz'
  if (R/p).exists():a['artifacts'][key]=ref(p)
  else:a['missingness'].append(key+' unavailable in selected compact acquisition')
 a['profile']=claims[n].get('profile',claims[n].get('paid_profile'))
 a['same_t_comparison_required']='Different replica counts are not forcibly identified; normalize only under separately registered exact convention.'
 return a
entries=[]
for n,b in parents.items():
 ca,cb=kappa(n),kappa(b);gain=Fraction(ca)-Fraction(cb);assert gain>0,(n,b)
 c=claims[n];m=metadata.get(n,{})
 e={'pr':n,'parent_pr':b,'head':head(n),'author':author(n),'created_at':m.get('created_at'),'title':m.get('title'),'parent_head':head(b),'change_scope':mechanism[n],'lineage_group':f'parent-pr-{b}','ancestral_lineage_group':'PR2833_shared_kernel_paired_release_lineage','source_attribution':attribution(n),'providers':{v:{'before':wordref(b,v),'after':wordref(n,v)} for v in ['base','extra']},'allocation':{'before':allocation(b),'after':allocation(n)},'labels':{'tier':'SOURCE_REPORTED_CONDITIONAL_COMPLETE_FINITE_RELEASE','source_reported_only':True,'kappa_before':cb,'kappa_after':ca,'matched_parent_gain':str(gain),'matched_parent_pr':b,'structural_parent_match':True,'matched_parent_gain_decimal_approx':format(float(gain),'.17g'),'reported_gain':c.get('gain',c.get('gain_over_full_pr2857')),'reported_comparator_pr':c.get('baseline_pr',c.get('primary_comparison',{}).get('pr')),'source_status':c.get('status'),'source_scope':c.get('scope'),'claim_refs':[dict(ref(C[b]),field='kappa_rational' if b==2833 else 'kappa',role='paired_parent_complete_outer'),dict(ref(C[n]),field='kappa',role='candidate_complete_outer')],'structural_regression_eligible':n!=2875,'precision_only':n==2875},'missingness':[],'interpretation':'Exact rational labels are arithmetic differences of source-reported complete conditional outer claims for this paired parent state; no fresh release admission and no unconditional theorem claim.'}
 if n in [2948,2957,2966]:e['missingness'].append('Source CLAIM scope or baseline wording is inherited/stale; final rewrite/FINAL-WORD is the candidate, and matched parent claim is selected explicitly rather than copying reported gain.')
 if n==2979:e['missingness'].append('Reported comparator2969 is outer-pending; matched parent is released2942 with exact PARENT words and its original allocation.')
 if n==2894:e['missingness'].append('Structural predecessor2863 has the same2857 word bytes but T185 fill; source headline also compares precision-refined2875. Matched label uses2863 explicitly.')
 if n==2875:e['missingness'].append('Only certificate precision changes; word and fill features are identical. Descriptive control, excluded from structural gain regression.')
 entries.append(e)
# Exact byte-level release-state assertions, not scientific feature checks.
for n in [2930,2948,2957]:assert allocation(n)['artifacts']['fill']['sha256']==claims[2930]['fill_sha256']
assert ref(words[2917]['base'])['sha256']==ref(P[2957]+'/data/WORD-base.json.gz')['sha256']
assert ref(words[2942]['base'])['sha256']==ref(P[2966]+'/data/WORD-base.json.gz')['sha256']
for n in [2857,2863,2875,2894,2908,2917,2948,2957,2966,2979]:
 receipts=[f for f in (R/P[n]).rglob('*.json') if 'RELEASE' in f.name and 'RECEIPT' in f.name]
 if n==2875:receipts=[R/P[n]/'evidence/CANDIDATE-RELEASE.json']
 e=next(x for x in entries if x['pr']==n);e['release_receipts']=[ref(str(f.relative_to(R))) for f in receipts]
 if not receipts:e['missingness'].append('Full release receipt unavailable in compact acquisition; claim hash/status retained.')
for n,sub in [(2930,'data/continuation-02/checkpoint/pr2930'),(2942,P[2966]+'/evidence/pr2942')]:
 e=next(x for x in entries if x['pr']==n);e['release_receipts']=[ref(str(f.relative_to(R))) for f in (R/sub).rglob('*RELEASE*RECEIPT*.json')]
 if not e['release_receipts']:e['missingness'].append('Complete release status and receipt hash are source-reported in exact CLAIM; full receipt bytes not locally acquired.')
cohort={'schema':'R11_RELEASE_COHORT_V1','assembled_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_cutoff':'2026-10-16T17:39:24Z','selection':{'rule':'Latest12 chronological public complete conditional finite improving release episodes visible in pinned recent metadata, with exact structural parent state; no title-only gain admission. Pending2969 is excluded. Precision-only2875 is retained explicitly as a descriptive control.','count':len(entries),'ordering':'descending PR creation chronology','independence':'One cumulative ancestry with branches; these are not12 independent discoveries or causal interventions.','source_only':True},'entries':entries,'excluded_pending':[{'pr':2969,'tier':'FINITE_NATIVE_OWNER_AND_MOMENT_CANDIDATE_OUTER_PENDING','reason':'Source explicitly leaves complete outer release pending; not admitted to complete cohort or gain regression.','metadata':ref('data/continuation-07/checkpoint/pr-2969.json.gz'),'candidate_claim':ref(P[2979]+'/allocation/baseline/CLAIM.json')}],'original_source_attribution':{'pins':pins,'files':pin_data['files']},'source_acquisitions':[ref(str(p.relative_to(R))) for p in sorted((R/'data/continuation-07/releases').glob('pr*/*ACQUISITION.json'))]+[ref('data/continuation-07/releases/pr2857/ALLOCATION-SUPPLEMENT.json')],'coverage_limits':['Chronological latest12 released positive conditional claims, not all independent proof audits; selection has survivor bias.','No new scientific extraction, pricing, native execution or fetched code execution occurred during assembly.','Provider copies, repeated seeds, immediate siblings and shared ancestry must remain grouped; κ values are complete outer headlines, not supplier-only roots.','Allocation arrays retain their actual replica counts; different T values are observable metadata and cannot be treated as an unproved bijection.'],'input_checkpoint':ref('data/continuation-07/checkpoint/RECEIPT.json')}
with O.open('x') as f:json.dump(cohort,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'path':str(O.relative_to(R)),'sha256':hashlib.sha256(O.read_bytes()).hexdigest(),'bytes':O.stat().st_size,'entries':len(entries),'provider_pairs':sum(len(x['providers']) for x in entries),'fill_pairs':sum(bool(x['allocation']['before']['artifacts'].get('fill')) and bool(x['allocation']['after']['artifacts'].get('fill')) for x in entries),'new_acquisition_bytes':sum(p.stat().st_size for p in (R/'data/continuation-07/releases').rglob('*') if p.is_file())}))
