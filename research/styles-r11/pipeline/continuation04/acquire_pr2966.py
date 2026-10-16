"""Acquire PR2966's exact source package as inert, attributed data only."""
from datetime import datetime, timezone
from pathlib import Path
import base64
import gzip
import hashlib
import json
import subprocess

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
OUT = PKG / 'data/continuation-04/pr2966'
REPOSITORY = 'CrocSwap/integer-mult-bounds'
HEAD = 'e62d3eb9005117d82a9babcfa937ecc53237c490'
SOURCE = 'research/paired-extension-normal45-rewrites'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def gh(endpoint):
    process = subprocess.run(['gh', 'api', endpoint], cwd=ROOT, capture_output=True,
                             text=True, timeout=45)
    if process.returncode:
        raise RuntimeError('read-only GitHub acquisition failed: exit' + str(process.returncode))
    return json.loads(process.stdout)


def main():
    if OUT.exists():
        raise FileExistsError('immutable source acquisition already exists')
    OUT.mkdir(parents=True)
    started = datetime.now(timezone.utc).isoformat()
    listing = gh(f'repos/{REPOSITORY}/contents/{SOURCE}?ref={HEAD}')
    files, trees = [], []
    for item in listing:
        if item['type'] == 'file':
            files.append(dict(path=item['name'], git_blob=item['sha'], bytes=item['size']))
        elif item['type'] == 'dir':
            tree = gh(f'repos/{REPOSITORY}/git/trees/{item["sha"]}?recursive=1')
            if tree['truncated']:
                raise ValueError('package subtree truncated')
            trees.append(dict(path=item['name'], git_tree=item['sha']))
            for child in tree['tree']:
                if child['type'] == 'blob':
                    files.append(dict(path=item['name'] + '/' + child['path'],
                                      git_blob=child['sha'], bytes=child['size']))
    if len(files) > 128 or sum(p['bytes'] for p in files) > 10 * 1024 ** 2:
        raise ValueError('bounded source package exceeded')
    records = []
    for pin in sorted(files, key=lambda p:(p['path'] not in ('README.md', 'CLAIM.json', 'MANIFEST.json', 'rewrite/FINAL-WORD-base.json.gz', 'rewrite/FINAL-WORD-extra.json.gz'),p['path'])):
        value = gh(f'repos/{REPOSITORY}/git/blobs/{pin["git_blob"]}')
        if value['encoding'] != 'base64':
            raise ValueError('expected base64 Git blob')
        raw = base64.b64decode(value['content'])
        if len(raw) != pin['bytes'] or blob(raw) != pin['git_blob']:
            raise ValueError('exact Git blob/size mismatch')
        relative = pin['path'] + ('.txt' if pin['path'].endswith('.py') else '')
        target = OUT / 'package' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as handle:
            handle.write(raw)
        record = dict(pin, source_path=SOURCE + '/' + pin['path'], local_path=str(target.relative_to(PKG)),
                      sha256=sha(raw), treatment='Inert bytes; Python sources renamed .py.txt and never imported or executed')
        if pin['path'].endswith('.gz'):
            record['uncompressed_sha256'] = sha(gzip.decompress(raw))
        records.append(record)
        if pin['path'] in ('CLAIM.json', 'MANIFEST.json', 'rewrite/FINAL-WORD-base.json.gz', 'rewrite/FINAL-WORD-extra.json.gz'):
            print(json.dumps(dict(phase='source', path=pin['path'], bytes=len(raw), sha256=record['sha256'])), flush=True)
    manifest = json.loads((OUT / 'package/MANIFEST.json').read_bytes())
    mapping = manifest.get('files', manifest) if isinstance(manifest, dict) else None
    matches = 0
    if isinstance(mapping, dict):
        for pin in records:
            expected = mapping.get(pin['path'])
            if isinstance(expected, dict):
                expected = expected.get('sha256')
            if expected is not None:
                if expected != pin['sha256']:
                    raise ValueError('package manifest SHA256 mismatch: ' + pin['path'])
                matches += 1
    receipt = dict(schema_version=1, pr=2966, head=HEAD, repository=REPOSITORY,
        author='Jeremy Kothe (jeremykothe2)', author_login='jeremykothe2', source_package=SOURCE,
        started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
        files=records, subtree_pins=trees, script_sha256=sha(Path(__file__).read_bytes()),
        manifest_entries_checked=matches, package_file_count=len(records), total_bytes=sum(p['bytes'] for p in records),
        credits='Retain CREDITS.md, NOTICE, SOURCES.json and all predecessor credits; package acquisition does not endorse its scientific claims.',
        scope='Entire bounded exact-head package as inert data. No fetched producer, checker, auditor, source or generated code was imported or executed. No scientific trial was run.',
        caveat='The OUTER-CLAIM location in the PR body may refer to a reproduction output; acquisition records only exact committed files. Stored author claims/receipts are not a local admission replay.')
    raw = (json.dumps(receipt, sort_keys=True, indent=2) + '\n').encode()
    with (OUT / 'ACQUISITION.json').open('xb') as handle:
        handle.write(raw)
    print(json.dumps(dict(status='ACQUIRED_INERT_DATA', files=len(records), bytes=receipt['total_bytes'],
                         manifest_entries_checked=matches, receipt_sha256=sha(raw))), flush=True)


if __name__ == '__main__':
    main()
