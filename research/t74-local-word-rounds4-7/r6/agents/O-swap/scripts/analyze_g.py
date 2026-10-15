"""analyze_g: summarize a gswap jsonl: status counts, joint minus additive, best joint delta."""
import json, sys, collections
rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
st = collections.Counter(r['status'] for r in rows); dev = collections.Counter(); best = None; nonadd = []
for r in rows:
    if r.get('delta') is None: continue
    if best is None or r['delta'] < best['delta']: best = r
    if r.get('additive') is not None:
        d = r['delta'] - r['additive']; dev[d] += 1
        if d != 0: nonadd.append(r)
print('rows', len(rows), dict(st))
print('joint - additive histogram (top):', sorted(dev.items(), key=lambda x: -x[1])[:12])
print('min joint delta:', best['delta'] if best else None, best and (best['narrow'], best['widen'], best['widen_basis'], best['additive']))
neg = [r for r in rows if r.get('delta') is not None and r['delta'] < 0]; print('negative joint deltas:', len(neg))
zero = [r for r in rows if r.get('delta') == 0]; print('zero joint deltas:', len(zero))
print('non-additive pairs:', len(nonadd)); [print('   ', r['narrow'], r['widen'], r['widen_basis'], 'joint', r['delta'], 'add', r['additive']) for r in sorted(nonadd, key=lambda r: r['delta'] - r['additive'])[:15]]
