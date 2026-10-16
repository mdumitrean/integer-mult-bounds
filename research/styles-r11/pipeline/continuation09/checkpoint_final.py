"""Bounded, read-only continuation09 final source checkpoint; no scientific imports."""
from pathlib import Path
import gzip
import hashlib
import importlib.util
import json
import re
import subprocess

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[1]
HELPER = HERE.parent/'continuation03/checkpoint_sources.py'
HELPER_SHA = '5b16a7b2b4a23d7367a10f3909836b959336a8eef8e80360f7b714da4ec84ed5'
if hashlib.sha256(HELPER.read_bytes()).hexdigest() != HELPER_SHA:
    raise ValueError('trusted acquisition helper drift')
spec = importlib.util.spec_from_file_location('styles_cont09_metadata', HELPER)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
OUTPUT = PKG/'data/continuation-09/final_checkpoint'
INITIAL = PKG/'data/continuation-09/checkpoint'
INITIAL_RECEIPT = json.loads((INITIAL/'RECEIPT.json').read_text())
C.TOTAL_SECONDS = 300
CUTOFF = INITIAL_RECEIPT['started_utc'][:19]+'Z'  # Conservative overlap with the initial paginated sample.
GUIDANCE = ('AGENTS.md','CONTRIBUTING.md','autoresearch.md',
 'docs/research/agent-task-catalog.json','docs/research/bottleneck-brief.md',
 'docs/research/research-family-status.md','certificates/selected-result.json',
 'docs/research/current-priorities.md','docs/research/agent-procedure.md')


def fields(p):
    return {k:p.get(k) for k in ('number','title','body','html_url','updated_at','created_at',
      'closed_at','merged_at','state','draft')} | dict(head=p['head']['sha'],
      author=p['user']['login'],base=p['base']['sha'])


def main():
    a=C.Acquisition(OUTPUT)
    a.receipt.update(script_sha256=C.digest(Path(__file__).read_bytes()),
       trusted_acquisition_helper_sha256=HELPER_SHA,prior_cutoff_utc=CUTOFF,
       previous_checkpoint=dict(path='data/continuation-09/checkpoint/RECEIPT.json',
          sha256=C.digest((INITIAL/'RECEIPT.json').read_bytes()),
          started_utc=INITIAL_RECEIPT['started_utc'],finished_utc=INITIAL_RECEIPT['finished_utc']),
       limits=['Read-only bounded continuation09 final source checkpoint, no fetched code execution or scientific tests.',
       'All-state PR metadata is paged in update-descending order until a page reaches the prior cutoff, at most4pages; pagination is not atomic.',
       'Discussions2612,1163,1166,1167 are fully refreshed regardless of discussion updatedAt; other threads and arbitrary linked resources remain outside this delta.',
       'Remote claims and archival merges are not independent admission or novelty evidence.'])
    try:
        started=C.utc()
        command=['git','fetch','--no-tags','https://github.com/CrocSwap/integer-mult-bounds','main']
        process=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=90)
        if process.returncode:
            raise RuntimeError('canonical read-only git fetch failed')
        head=subprocess.check_output(['git','rev-parse','FETCH_HEAD'],cwd=ROOT,text=True).strip()
        a.save('GIT-FETCH.json',dict(command=command,fetched_commit=head,started_utc=started,
           finished_utc=C.utc(),scope='Read-only fetch; local branch and working tree unchanged.'),
           dict(kind='git-fetch'))
        a.receipt['canonical_main']=head
        endpoint=f'repos/{C.REPOSITORY}/commits/{head}'
        a.save('main.json.gz',a.gh([endpoint]),dict(kind='REST',endpoint=endpoint))
        prior=json.loads((PKG/'data/continuation-09/checkpoint/guidance/PINS.json').read_text())
        guidance={}
        for path in GUIDANCE:
            raw=subprocess.check_output(['git','show',head+':'+path],cwd=ROOT)
            name=path.replace('/','__')+'.gz'
            data=gzip.compress(raw,mtime=0)
            target=OUTPUT/'guidance'/name;target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write(data)
            prior_path=PKG/'data/continuation-09/checkpoint/guidance'/name
            if not prior_path.exists():
                prior_path=PKG/'data/continuation-09/checkpoint/guidance'/name
            old=gzip.decompress(prior_path.read_bytes()) if prior_path.exists() else None
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            pin=dict(commit=head,source_path=path,git_blob=blob,sha256=C.digest(data),
               source_sha256=C.digest(raw),bytes=len(data),unchanged_from_previous_checkpoint=old==raw)
            guidance[name]=pin
            a.receipt['files']['guidance/'+name]=dict(pin,source=dict(kind='git-show-exact-head'))
            if path.endswith('agent-task-catalog.json'):
                a.receipt['priority_revision']=json.loads(raw)['priority_revision']
        a.save('guidance/PINS.json',dict(commit=head,files=guidance,prior_pin_sha256=C.digest(
           (PKG/'data/continuation-09/checkpoint/guidance/PINS.json').read_bytes())),dict(kind='guidance-pins'))
        a.receipt['guidance']=dict(path='data/continuation-09/final_checkpoint/guidance/PINS.json',
            sha256=C.digest((OUTPUT/'guidance/PINS.json').read_bytes()))
        print(json.dumps(dict(phase='guidance',main=head,priority_revision=a.receipt['priority_revision'],
            changes=[k for k,v in guidance.items() if not v['unchanged_from_previous_checkpoint']])),flush=True)
        a.receipt['named_comparators']={}
        for number in (3028,3024):
            endpoint=f'repos/{C.REPOSITORY}/pulls/{number}'
            p=a.gh([endpoint]);a.save(f'pr-{number}.json.gz',p,dict(kind='REST',endpoint=endpoint))
            a.receipt['named_comparators'][str(number)]=fields(p)
        for number in (2612,1163,1166,1167):
            a.discussion_thread(number)
        rows=[];reached=False;pages=0
        endpoint=f'repos/{C.REPOSITORY}/pulls?state=all&sort=updated&direction=desc'
        for page in range(1,5):
            batch=[fields(p) for p in a.gh([endpoint+f'&per_page=100&page={page}'])]
            pages+=1;rows.extend(batch)
            if len(batch)<100 or any(p['updated_at']<CUTOFF for p in batch):
                reached=True;break
        a.save('updated-prs.json.gz',rows,dict(kind='REST',endpoint=endpoint))
        delta=[p for p in rows if p['updated_at']>=CUTOFF]
        a.receipt['remote']['updated_prs']=dict(pages=pages,rows=len(rows),unique_numbers=len({p['number'] for p in rows}),
           updates_since_cutoff=len(delta),new_since_cutoff=sum(p['created_at']>=CUTOFF for p in rows),
           reached_cutoff=reached,complete_recent_delta=reached,complete_all_prs=False)
        a.save('delta-index.json',dict(cutoff=CUTOFF,rows=[{k:p[k] for k in ('number','title','author','head','state','created_at','updated_at')}|
          dict(decimal_tokens=sorted(set(re.findall(r'0\.001[0-9]{6,}',p['body'] or '')))) for p in delta]),
          dict(kind='inert-local-metadata-index'))
        print(json.dumps(dict(phase='delta',rows=[{k:p[k] for k in ('number','title','head','state','created_at','updated_at')}|
          dict(decimal_tokens=sorted(set(re.findall(r'0\.001[0-9]{6,}',p['body'] or '')))) for p in delta])),flush=True)
    finally:
        a.finish()


if __name__=='__main__':main()
