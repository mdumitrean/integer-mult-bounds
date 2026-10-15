"""asummary.py: aggregate out/PRICED.jsonl into out/SUMMARY.json (counts by group/k/priority/status/delta)."""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(HERE, '..', 'out')
rows = [json.loads(l) for l in open(os.path.join(O, 'PRICED.jsonl')) if l.strip()]
plan = sum(1 for l in open(os.path.join(O, 'PLAN.jsonl')) if l.strip())
def grp(r):
    L, k = len(r['alt']), r['k']
    return 'reduce' if L < k else ('same' if (L == k and not r['perm']) else ('perm' if r['perm'] else 'longer'))
by = collections.defaultdict(collections.Counter); neg = []; secs = []
for r in rows:
    g = f"{grp(r)}/k{r['k']}/{'big' if r['big'] else ('nz' if r['nz'] else 'zero')}"
    d = r.get('delta'); st = r.get('status')
    by[g][f'{st}:{d}' if st in ('ok', 'uncertified') else st] += 1
    if isinstance(d, (int, float)) and d < 0: neg.append(r)
    secs.append(r.get('seconds') or 0)
tot = collections.Counter()
for v in by.values(): tot.update(v)
ok_d = collections.Counter(r.get('delta') for r in rows if r.get('status') in ('ok', 'uncertified'))
out = dict(agent='R-apeep', round='r6', b='0.001679754956125544', word='r3/inputs/gauge44-word-566-554.json.gz',
           planned=plan, priced=len(rows), totals=dict(tot), ok_delta_histogram={str(k): v for k, v in sorted(ok_d.items(), key=lambda x: (x[0] is None, x[0] or 0))},
           by_group={g: dict(v) for g, v in sorted(by.items())}, negatives=neg, mean_seconds=round(sum(secs) / max(1, len(secs)), 2),
           max_rss_gib=max((r.get('rss') or 0) for r in rows) if rows else None)
json.dump(out, open(os.path.join(O, 'SUMMARY.json'), 'w'), indent=1, default=str)
print(json.dumps({k: out[k] for k in ('planned', 'priced', 'totals', 'ok_delta_histogram', 'mean_seconds', 'max_rss_gib')}, default=str))
print('negatives:', len(neg))
