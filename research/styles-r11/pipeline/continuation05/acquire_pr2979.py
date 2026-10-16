"""Read exact PR2979 Git objects into inert source data; never execute them."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

RR=Path(__file__).resolve().parents[2]
ROOT=RR.parents[1]
OUT=RR/'data/continuation-05/pr2979'
HEAD='be191346391661f4d35fc0d1508d0a6029572576'
SOURCE='research/rank7-joint-endframes'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(raw):return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()


def main():
    started=datetime.now(timezone.utc).isoformat()
    listing=subprocess.check_output(['git','ls-tree','-r','-z','-l',HEAD,'--',SOURCE],cwd=ROOT)
    files=[]
    for row in listing.split(b'\0'):
        if not row:continue
        meta,path=row.split(b'\t',1);mode,kind,git_blob,size=meta.split()
        if kind!=b'blob':raise ValueError('unexpected non-blob package tree entry')
        path=path.decode();relative=str(Path(path).relative_to(SOURCE))
        files.append(dict(path=relative,source_path=path,git_blob=git_blob.decode(),bytes=int(size),mode=mode.decode()))
    if not files or len(files)>512 or sum(p['bytes'] for p in files)>20*1024**2:
        raise ValueError('bounded exact source package exceeded or absent')
    print(json.dumps(dict(phase='inventory',files=len(files),bytes=sum(p['bytes'] for p in files))),flush=True)
    OUT.mkdir(parents=True,exist_ok=False)
    records=[]
    for pin in sorted(files,key=lambda x:(not(x['path'] in ('README.md','CLAIM.json','MANIFEST.json') or 'WORD' in x['path']),x['path'])):
        raw=subprocess.check_output(['git','cat-file','blob',pin['git_blob']],cwd=ROOT)
        if len(raw)!=pin['bytes'] or blob(raw)!=pin['git_blob']:
            raise ValueError('Git blob/size mismatch')
        relative=pin['path']+('.txt' if pin['path'].endswith('.py') else '')
        target=OUT/'package'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(raw)
        record=dict(pin,local_path=str(target.relative_to(RR)),sha256=sha(raw),
           treatment='Inert exact Git bytes; Python sources renamed .py.txt; never imported or executed.')
        if pin['path'].endswith('.gz'):record['uncompressed_sha256']=sha(gzip.decompress(raw))
        records.append(record)
        if pin['path'] in ('CLAIM.json','MANIFEST.json','README.md') or 'WORD' in pin['path']:
            print(json.dumps(dict(phase='source',path=pin['path'],bytes=len(raw),sha256=record['sha256'])),flush=True)
    manifest=json.loads((OUT/'package/MANIFEST.json').read_bytes())
    mapping=manifest.get('files',manifest) if isinstance(manifest,dict) else None
    checked=0
    if isinstance(mapping,dict):
        for pin in records:
            expected=mapping.get(pin['path'])
            if isinstance(expected,dict):expected=expected.get('sha256')
            if expected is not None:
                if expected!=pin['sha256']:raise ValueError('manifest digest mismatch: '+pin['path'])
                checked+=1
    receipt=dict(schema_version=1,pr=2979,head=HEAD,repository='CrocSwap/integer-mult-bounds',
      author='Marius-Paul Dumitrean (mdumitrean)',author_login='mdumitrean',source_package=SOURCE,
      started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),files=records,
      acquisition='Exact Git objects available from the explicitly requested canonical main fetch; git ls-tree and cat-file only.',
      acquisition_main_fetch='data/continuation-05/checkpoint/GIT-FETCH.json',
      acquisition_main_fetch_sha256=sha((RR/'data/continuation-05/checkpoint/GIT-FETCH.json').read_bytes()),
      script_sha256=sha(Path(__file__).read_bytes()),package_file_count=len(records),
      total_bytes=sum(p['bytes'] for p in records),manifest_entries_checked=checked,
      credits='Preserve complete CREDITS.md, NOTICE, SOURCES.json, PINS.json and all source lineage; original21 PINS remain authoritative.',
      scope='Entire bounded exact-head package acquired as inert data; no fetched program, source, checker or generated code imported or executed. No scientific trial or native/outer replay.',
      caveat='Producer-reported receipts and claim bytes are source evidence, not independent admission by this acquisition.')
    raw=(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode()
    with (OUT/'ACQUISITION.json').open('xb') as f:f.write(raw)
    print(json.dumps(dict(status='ACQUIRED_INERT_DATA',files=len(records),bytes=receipt['total_bytes'],
      manifest_entries_checked=checked,receipt_sha256=sha(raw))),flush=True)


if __name__=='__main__':main()
