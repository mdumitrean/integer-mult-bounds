"""Read-only exact source acquisition; fetched programs remain inert text."""
from pathlib import Path
from datetime import datetime,timezone
import base64
import hashlib
import json
import subprocess

PKG=Path(__file__).resolve().parents[2]
OUT=PKG/'data/continuation-12/allocation-source'
REPO='CrocSwap/integer-mult-bounds'
SOURCES={
3024:dict(head='315df10c07cf8b8ee9af9b2122750635bb2582ae',author_login='petalas',author='Nick Petalas',prefix='research/rank7-cap740',paths=['README.md','EXCHANGE.json','PR3018-EXCHANGE.json','RESULT.json','RETAINED.json','SOURCES.json','cap_proof.py','lift.py','verify.py']),
3054:dict(head='4773c3ea67b471415870e38411fae313ec44a675',author_login='petalas',author='Nick Petalas',prefix='research/rank7-t740-carrier-skips',paths=['materialize.py','vendor/pr3042/allocation/PROVIDERS.json','vendor/PR3030-INVOICE.json.gz']),
3051:dict(head='10a45bd361554709840becb5bc26016ca49944c3',author_login='jeremydiviney',author='Jeremy Diviney',prefix='research/rank7-six-skip-cap-release',paths=['CLAIM.json','NOTICE','SOURCE-PINS.json','MANIFEST.json','README.md'])}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def gh(path):return json.loads(subprocess.check_output(['gh','api',path],timeout=45))
def main():
    OUT.mkdir(parents=True,exist_ok=False)
    rec=dict(schema_version=1,started_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__).read_bytes()),source_reported_only=True,scientific_execution=False,sources=SOURCES,files=[],scope='Compact exact allocation recipe/journal/cap/claim acquisition only. Materialized T740 fill is not publicly committed in the inspected package listings; no materializer is executed.')
    for pr,s in SOURCES.items():
        for rel in s['paths']:
            source=s['prefix']+'/'+rel
            meta=gh(f'repos/{REPO}/contents/{source}?ref={s["head"]}')
            data=meta if meta.get('encoding')=='base64' else gh(f'repos/{REPO}/git/blobs/{meta["sha"]}')
            if data['encoding']!='base64':raise ValueError('unsupported blob encoding')
            raw=base64.b64decode(data['content'])
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            if blob!=meta['sha'] or len(raw)!=meta['size']:raise ValueError('upstream Git source hash mismatch')
            path=OUT/str(pr)/(rel+'.txt' if rel.endswith('.py') else rel);path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as f:f.write(raw)
            rec['files'].append(dict(pr=pr,head=s['head'],author_login=s['author_login'],source_path=source,path=str(path.relative_to(PKG)),sha256=sha(raw),git_blob=blob,bytes=len(raw),fetched_program_inert=rel.endswith('.py')))
    rec['finished_utc']=datetime.now(timezone.utc).isoformat();rec['payload_bytes']=sum(v['bytes'] for v in rec['files'])
    p=OUT/'ACQUISITION.json'
    with p.open('x') as f:json.dump(rec,f,sort_keys=True,indent=2);f.write('\n')
    print(json.dumps(dict(path=str(p.relative_to(PKG)),sha256=sha(p.read_bytes()),files=len(rec['files']),payload_bytes=rec['payload_bytes'])))
if __name__=='__main__':main()
