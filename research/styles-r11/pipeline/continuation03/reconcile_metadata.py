"""Reconcile moving updated-order PR pages with stable created-order all-state pages.

Only metadata is acquired. Separate original snapshots remain immutable.
"""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import subprocess

PKG = Path(__file__).resolve().parents[2]
OUT = PKG / 'data/continuation-03/checkpoint'
REPO = 'CrocSwap/integer-mult-bounds'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    started = datetime.now(timezone.utc).isoformat()
    rows, complete = [], False
    endpoint = f'repos/{REPO}/pulls?state=all&sort=created&direction=asc&per_page=100'
    for page in range(1, 61):
        proc = subprocess.run(['gh', 'api', endpoint + '&page=' + str(page)], cwd=PKG.parents[1],
                              check=True, capture_output=True, text=True, timeout=45)
        values = json.loads(proc.stdout)
        for p in values:
            rows.append({k:p.get(k) for k in ('number','title','body','html_url','updated_at',
                'created_at','closed_at','merged_at','draft','state')} | dict(
                head=p['head']['sha'], author=p['user']['login'], base=p['base']['sha']))
        if len(values) < 100:
            complete = True
            break
    if len(rows) != len({row['number'] for row in rows}):
        raise ValueError('unexpected duplicate in created-order all-state pages')
    if not complete:
        raise ValueError('all-state reconciliation incomplete')
    def write(name, value):
        raw = (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()
        data = gzip.compress(raw, mtime=0)
        with (OUT/name).open('xb') as handle: handle.write(data)
        return dict(path=str((OUT/name).relative_to(PKG)),sha256=sha(data),
                    uncompressed_sha256=sha(raw),bytes=len(data))
    snapshot = write('all-prs-created-order.json.gz', rows)
    union = {}
    original = []
    for name in ('open-prs.json.gz','closed-prs.json.gz'):
        raw = (OUT/name).read_bytes()
        original.append(dict(path=str((OUT/name).relative_to(PKG)), sha256=sha(raw)))
        for row in json.loads(gzip.decompress(raw)):
            old = union.get(row['number'])
            if old is None or row['updated_at'] > old['updated_at']: union[row['number']] = row
    added = sorted(set(r['number'] for r in rows) - set(union))
    for row in rows:
        old = union.get(row['number'])
        if old is None or row['updated_at'] >= old['updated_at']: union[row['number']] = row
    combined = write('all-prs-reconciled.json.gz', [union[n] for n in sorted(union)])
    receipt = dict(schema_version=1,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),
        complete=True,pages=page,rows=len(rows),unique_numbers=len(rows),states={s:sum(r['state']==s for r in rows) for s in ('open','closed')},
        source_endpoint=endpoint,script_sha256=sha(Path(__file__).read_bytes()),files=[snapshot,combined],
        original_snapshots=original,added_numbers=added,union_count=len(union),
        reason='Updated-order closed pagination moved during archival activity and repeated28rows. All-state created-order pagination removes that ordering instability; original snapshots preserved.',
        limits='Created order is stable for existing PRs, but this is still a temporal metadata snapshot, not an atomic server transaction or a diff/unpublished-work census.')
    raw=(json.dumps(receipt,sort_keys=True,indent=2)+'\n').encode()
    with (OUT/'RECONCILIATION.json').open('xb') as handle: handle.write(raw)
    print(json.dumps({k:v for k,v in receipt.items() if k!='original_snapshots'},sort_keys=True))


if __name__ == '__main__':
    main()
