"""Read-only, exact-head acquisition of PR2930 cap and claim metadata.

Fetched Python text is renamed .py.txt and is never imported or executed.
The large fill, native caches and executable dependency trees are not fetched.
"""
from datetime import datetime, timezone
from pathlib import Path
import base64
import hashlib
import json
import subprocess

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
OUT = PKG/'data/continuation-02/checkpoint/pr2930'
HEAD = '81f3b5d12977eba09e06fbff729167d59faabe90'
PACKAGE = 'research/paired-extension-cap-fill'
FILES = ('CLAIM.json','SOURCES.json','ALLOCATION-PINS.json','PINS.json',
         'MANIFEST.json','README.md','CREDITS.md','NOTICE','check_cap.py',
         'certificates/RELAX-CAP.json','allocation/PROFILE.json',
         'allocation/PROVIDERS.json','allocation/ORDER.json','allocation/DISPATCH.json',
         'allocation/SEARCH.json','evidence/ADMISSION-RESULT.json',
         'evidence/RELEASE-RECEIPT.json','evidence/FULL-NATIVE-RECEIPT.json',
         'evidence/FULL-NATIVE-RESULT.json','evidence/FULL-REPLAY-RESULT.json')


def main():
    if OUT.exists():
        raise FileExistsError('immutable source checkpoint already exists')
    OUT.mkdir(parents=True)
    manifest = dict(schema_version=1,pr=2930,commit=HEAD,package=PACKAGE,
                    author='Marius-Paul Dumitrean (mdumitrean)',
                    fetched_utc=datetime.now(timezone.utc).isoformat(),files=[],
                    scope='Partial inert cap/claim/profile/source evidence only. No large fill or native cache acquired, no certificate replay.',
                    script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    for relative in FILES:
        remote = PACKAGE+'/'+relative
        result = subprocess.run(['gh','api','repos/CrocSwap/integer-mult-bounds/contents/'+remote+'?ref='+HEAD],
                                cwd=ROOT,text=True,capture_output=True,timeout=25)
        if result.returncode:
            raise RuntimeError('read-only source fetch failed: '+relative)
        record = json.loads(result.stdout)
        if record.get('encoding') != 'base64':
            raise ValueError('expected small immutable source file')
        raw = base64.b64decode(record['content'])
        blob = hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if blob != record['sha'] or len(raw) != record['size']:
            raise ValueError('Git source byte binding failed')
        local = OUT/(relative+'.txt' if relative.endswith('.py') else relative)
        local.parent.mkdir(parents=True,exist_ok=True)
        with local.open('xb') as handle:
            handle.write(raw)
        manifest['files'].append(dict(relative_path=relative,path=remote,
            local_path=str(local.relative_to(PKG)),git_blob=blob,sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),pr=2930,commit=HEAD,author=manifest['author'],
            treatment='INERT DATA; read with Python -I; no imports or execution'))
    manifest['finished_utc'] = datetime.now(timezone.utc).isoformat()
    with (OUT/'ACQUISITION.json').open('x') as handle:
        json.dump(manifest,handle,sort_keys=True,indent=2);handle.write('\n')
    print(json.dumps(dict(pr=2930,head=HEAD,files=len(manifest['files']),
                         acquisition=str((OUT/'ACQUISITION.json').relative_to(PKG)),
                         sha256=hashlib.sha256((OUT/'ACQUISITION.json').read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
