"""r10 F-lenders: extended retired-lender census (pairs.py rules) with per-helper status, lender table, chain edges
(follower -> follower on the same lender) and current hosted segments (warps) so that every existing alias can be
treated as movable.  usage: python3 -I census_r10.py CODE_DIR WORD.json.gz OUT.json"""
import sys, json
from collections import Counter, defaultdict
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
restored = {int(q) for q in w.get('helper_final', {})}
lenders_now = {rec[1] for rec in w['warps']}
touch = defaultdict(list)
for t, (sec, e) in enumerate(ev):
    if e[0] == 'warp':
        touch[e[1]].append((t, sec))
    else:
        for q in regs(e):
            touch[q].append((t, sec))
B0 = min(t for t, (sec, e) in enumerate(ev) if sec in ('B', 'Bwarp'))
wt = {}   # warp op -> time
for t, (sec, e) in enumerate(ev):
    if sec == 'Bwarp':
        wt[e[2]] = t
helpers = {}
for h in Wd.helpers:
    T = touch.get(h, [])
    width = len(Wd.end[h]) - len(Wd.start[h])
    st = None
    if h in restored: st = 'restored-cold'
    elif any(sec not in ('B', 'restore', 'Bwarp') for t, sec in T): st = 'touched-before-B'
    elif h in lenders_now: st = 'already-a-lender'
    gs = [t for t, sec in T if sec in ('B', 'restore')]
    if st is None and not gs: st = 'untouched'
    rec = dict(width=width, S=len(Wd.start[h]), status=st or 'follower', last=T[-1][0] if T else -1)
    if gs:
        rec.update(first=gs[0], F1=len(Wd.gateframe[gs[0]]), hi=len(b.hi[gs[0]]), lo1=len(b.lo[gs[0]]))
    helpers[h] = rec
lend = {}
for L in Wd.live:
    if v <= L < 2 * v or L in restored:
        continue
    T = touch.get(L, [])
    if any(sec == 'restore' for t, sec in T):
        continue
    last = T[-1][0] if T else -1
    lastf = b.byreg.get(L, [])
    if lastf and lastf[-1][1] == 'warp':
        U = len(lastf[-1][3]); lo = U; kind = 'warpE'
    elif lastf:
        g = lastf[-1][0]; U = len(Wd.gateframe[g]); lo = len(b.lo[g]); kind = 'gate'
    else:
        U = len(Wd.start[L]); lo = U; kind = 'start'
    lend[L] = dict(last=last, U=U, lo=lo, kind=kind, src=L < v, hosts=L in lenders_now)
fol = {h: r for h, r in helpers.items() if r['status'] == 'follower'}
pairs = []
for h, f in fol.items():
    for L, l in lend.items():
        if L != h and l['last'] < f['first'] and l['lo'] <= f['hi']:
            pairs.append((h, L, 'fixed' if l['U'] <= f['F1'] else 'refit'))
# chain edges among followers: i's last gate lo <= j's first hi and i.last < j.first (i retires as a lender after its own last)
chain = []
for i, fi in fol.items():
    li = lend.get(i)
    if li is None: continue
    for j, fj in fol.items():
        if i != j and li['last'] < fj['first'] and li['lo'] <= fj['hi']:
            chain.append((j, i))
# near misses for followers with hi >= 4
near = {}
for h, f in fol.items():
    if f['hi'] < 4: continue
    dimok = [(l['last'] - f['first'], L) for L, l in lend.items() if l['lo'] <= f['hi'] and L != h]
    timeok = [(l['lo'] - f['hi'], L) for L, l in lend.items() if l['last'] < f['first'] and L != h]
    near[h] = dict(f, best_time_gap_among_dim_ok=min(dimok) if dimok else None, best_dim_gap_among_time_ok=min(timeok) if timeok else None)
# current hosted segments: for each B warp, the lender's own last gate before the warp and the hosted segment after it
seg = []
for op, rec in enumerate(w['warps'], 1):
    if op not in wt: continue
    t0 = wt[op]; L = rec[1]
    own = [t for t, sec in touch[L] if t < t0]
    after = [t for t, sec in touch[L] if t > t0 and sec in ('B', 'restore')]
    seg.append(dict(op=op, lender=L, warp_time=t0, U=len(rec[3]), own_last=own[-1] if own else -1,
                    own_lo=len(b.lo[own[-1]]) if own and own[-1] in b.lo else None,
                    hosted_first=after[0] if after else None, hosted_F1=len(Wd.gateframe[after[0]]) if after else None,
                    hosted_hi=len(b.hi[after[0]]) if after else None, hosted_last=touch[L][-1][0]))
out = dict(word=sys.argv[2], B0=B0, helper_status=dict(Counter(r['status'] for r in helpers.values())),
           follower_hist={str(k): c for k, c in Counter((f['F1'], f['hi'], f['width']) for f in fol.values()).items()},
           width_by_status={st: dict(Counter(r['width'] for r in helpers.values() if r['status'] == st)) for st in set(r['status'] for r in helpers.values())},
           lenders=len(lend), lender_lo_hist={str(k): c for k, c in Counter((l['lo'], l['kind'], l['hosts']) for l in lend.values()).items()},
           pairs=pairs, chain_edges=chain, near=near, segments=seg, helpers=helpers, lend=lend)
json.dump(out, open(sys.argv[3], 'w'), indent=0, default=str)
print(json.dumps(dict((k, out[k]) for k in ('B0', 'helper_status', 'follower_hist', 'width_by_status', 'lenders', 'lender_lo_hist'))))
print('pairs', len(pairs), Counter(k for _, _, k in pairs), sorted(set(h for h, _, _ in pairs)))
print('chain edges', chain[:20])
for h, r in near.items():
    print('near', h, {k: r[k] for k in ('width', 'first', 'F1', 'hi', 'best_time_gap_among_dim_ok', 'best_dim_gap_among_time_ok')})
