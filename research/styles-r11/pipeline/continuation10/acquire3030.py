"""Acquire compact inert PR3030 evidence; no fetched executable is imported."""
from pathlib import Path
import base64,datetime,hashlib,json,subprocess
PKG=Path(__file__).resolve().parents[2]
OUT=PKG/'data/continuation-10/pr3030'
HEAD='78e77d820393c6b8648b47af219e991edfcc54e6'
REPO='petalas/integer-mult-bounds'
PREFIX='research/rank7-t740-release'
def gh(path):
 return json.loads(subprocess.check_output(['gh','api',path],timeout=40))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=False)
 started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 receipt=dict(schema_version=1,pr=3030,author='Nick Petalas (petalas)',author_login='petalas',head=HEAD,repository=REPO,source_prefix=PREFIX,started_utc=started,script_sha256=sha(Path(__file__).read_bytes()),scope='Compact source-reported conditional release evidence; no fresh admission, native replay, scientific extraction or fetched code execution. Large fill/dependency archives omitted; exact prior word references retained.',files=[],errors=[])
 try:
  root=gh(f'repos/{REPO}/contents/{PREFIX}?ref={HEAD}')
  evidence=gh(f'repos/{REPO}/contents/{PREFIX}/evidence?ref={HEAD}')
  names={'README.md','SOURCES.json','TASK.json','VENDOR.json','VERIFY.json','PINS.json','GIT-SOURCES.json','ENGINEERING.md','reproduce.py','verify_release.py','materialize.py'}
  selected=[x for x in root if x['type']=='file' and x['name'] in names]+[x for x in evidence if x['type']=='file']
  for x in selected:
   blob=gh(f'repos/{REPO}/git/blobs/{x["sha"]}')
   raw=base64.b64decode(blob['content']);assert len(raw)==x['size']
   assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==x['sha']
   relative=x['path'][len(PREFIX)+1:];relative=relative+'.txt' if relative.endswith('.py') else relative
   p=OUT/'package'/relative;p.parent.mkdir(parents=True,exist_ok=True)
   with p.open('xb') as f:f.write(raw)
   receipt['files'].append(dict(path=str(p.relative_to(PKG)),source_path=x['path'],sha256=sha(raw),git_blob=x['sha'],bytes=len(raw),author_login='petalas',head=HEAD,treatment='Inert data; Python source has .py.txt suffix and is never imported or executed.'))
  receipt['total_bytes']=sum(x['bytes'] for x in receipt['files'])
 except Exception as e:
  receipt['errors'].append(dict(type=type(e).__name__,message=str(e)));raise
 finally:
  receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  raw=(json.dumps(receipt,indent=2,sort_keys=True)+'\n').encode()
  with (OUT/'ACQUISITION.json').open('xb') as f:f.write(raw)
  print(json.dumps(dict(path=str((OUT/'ACQUISITION.json').relative_to(PKG)),sha256=sha(raw),files=len(receipt['files']),errors=receipt['errors'])),flush=True)
if __name__=='__main__':main()
