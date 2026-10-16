"""Read-only compact source binding for newer, source-reported releases."""
from pathlib import Path
import base64
from datetime import datetime, timezone
import hashlib
import json
import subprocess

PKG=Path(__file__).resolve().parents[2]
OUT=PKG/'data/continuation-11/latest-sources'
REPO='CrocSwap/integer-mult-bounds'
SOURCES={
 3042:dict(head='84cc406ad91ec53fff329a11a445d7effe564a77',author_login='dcharb78',prefix='research/rank7-restore-carrier-skips',
           paths=['CLAIM.json','CREDITS.md','NOTICE','SOURCES.json','EDIT-PINS.json','MANIFEST.json',
                  'edits/EDITS.json','edits/FINAL-WORD-base.json.gz','edits/FINAL-WORD-extra.json.gz']),
 3054:dict(head='4773c3ea67b471415870e38411fae313ec44a675',author_login='petalas',author='Nick Petalas',prefix='research/rank7-t740-carrier-skips',
           paths=['README.md','SOURCES.json','GIT-SOURCES.json','PINS.json','evidence/FINITE.json','evidence/NATIVE-RECEIPT.json',
                  'evidence/ADMISSION-RESULT.json','evidence/COMPOSITION-RESULT.json','evidence/OUTER-CLAIM.json',
                  'evidence/RELEASE-RECEIPT.json','evidence/RECIPE.json'])}

def sha(b):return hashlib.sha256(b).hexdigest()
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],timeout=45))
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    receipt=dict(schema_version=1,started_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__).read_bytes()),
       source_reported_only=True,scientific_replay=False,scope='Compact source/claim/word binding; no fetched code and no native/outer replay.',
       omitted=['Full native cache','Literal T740 allocation already pinned by predecessors','Generated logs','Fetched scientific programs'],files=[],sources=SOURCES)
    for pr,s in SOURCES.items():
        for rel in s['paths']:
            source=s['prefix']+'/'+rel
            metadata=gh(f'repos/{REPO}/contents/{source}?ref={s["head"]}')
            if metadata.get('encoding')=='base64':raw=base64.b64decode(metadata['content'])
            else:
                blob=gh(f'repos/{REPO}/git/blobs/{metadata["sha"]}')
                if blob['encoding']!='base64':raise ValueError('unsupported inert blob encoding')
                raw=base64.b64decode(blob['content'])
            actual=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if actual!=metadata['sha'] or len(raw)!=metadata['size']:raise ValueError('Git source byte mismatch')
            path=OUT/str(pr)/rel;path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(raw)
            receipt['files'].append(dict(pr=pr,author_login=s['author_login'],head=s['head'],source_path=source,
                path=str(path.relative_to(PKG)),sha256=sha(raw),git_blob=actual,bytes=len(raw)))
    receipt['finished_utc']=datetime.now(timezone.utc).isoformat()
    receipt['payload_bytes']=sum(r['bytes'] for r in receipt['files'])
    path=OUT/'ACQUISITION.json';raw=(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode()
    with path.open('xb') as f:f.write(raw)
    print(json.dumps(dict(path=str(path.relative_to(PKG)),sha256=sha(raw),files=len(receipt['files']),payload_bytes=receipt['payload_bytes'])))
if __name__=='__main__':main()
