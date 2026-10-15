"""Per width-8 follower: for each of its first events k, hi(event_k) vs the best free lender retired before event_k.
Also the target-read window: max target hi before h's first modification."""
import sys, json
from collections import Counter
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
C = json.load(open(sys.argv[3]))
lend = {int(L): l for L, l in C['lend'].items()}
free = sorted((l['last'], l['lo'], L) for L, l in lend.items() if not l['hosts'])
def best_before(t):
    c = [(lo, last, L) for last, lo, L in free if last < t]
    return min(c) if c else None
fol = {int(h): r for h, r in C['helpers'].items() if r['status'] == 'follower' and r['width'] == 8}
rows = []; summ = Counter()
for h in sorted(fol):
    evs = [x for x in b.byreg[h] if x[1] == 'gate'][:8]
    ks = []
    for k, x in enumerate(evs):
        t = x[0]; bb = best_before(t)
        ks.append(dict(k=k, t=t, hi=len(b.hi[t]), lo=len(b.lo[t]), best=bb, gap=(bb[0] - len(b.hi[t])) if bb else None))
    first_ok = next((r['k'] for r in ks if r['gap'] is not None and r['gap'] <= 0), None)
    summ[first_ok] += 1
    rows.append(dict(h=h, events=ks, first_ok=first_ok))
print('first event index where a free lender fits (None = none in first 8):', dict(summ))
print('free lenders:', len(free), 'earliest retirements (last, lo, L):', free[:6])
for r in rows[:4]:
    print(r['h'], [(e['k'], e['t'], e['hi'], e['gap']) for e in r['events']])
json.dump(rows, open(sys.argv[4], 'w'))
