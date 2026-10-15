"""Screen 'entering hostee -> cold host' hostings: the hostee's anticipatory first read (tgt += h) becomes an initial
correction tgt += c*K(x_c) (frame-free); hosting starts at the hostee's first modifying gate k1.
Needs: host c cold (helper_final, restored), not in restore, not a warp lender, last event < k1, dim U_c <= dim hi(k1)."""
import sys, json
from collections import Counter
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
entering = {int(q) for q in w['start_extra']}; restored = {int(q) for q in w['helper_final']}
lenders_now = {rec[1] for rec in w['warps']}
touch = {}
for t, (sec, e) in enumerate(ev):
    for q in ([e[1]] if e[0] == 'warp' else regs(e)):
        touch.setdefault(q, []).append((t, sec))
hosts = {}
why = Counter()
for c in restored:
    T = touch.get(c, [])
    if any(sec == 'restore' for t, sec in T): why['in-restore'] += 1; continue
    if c in lenders_now: why['already-lender'] += 1; continue
    if c in entering: why['entering'] += 1; continue
    hosts[c] = dict(last=T[-1][0] if T else -1, U=len(Wd.end[c]), first=T[0][0] if T else None)
print('cold hosts eligible', len(hosts), dict(why), 'U dims', dict(Counter(h['U'] for h in hosts.values())))
rows = []; stat = Counter()
for h in sorted(entering):
    if h in restored: continue
    G = [x[0] for x in b.byreg.get(h, []) if x[1] == 'gate']
    if len(G) < 2: continue
    t0 = G[0]; sec0, e0 = ev[t0]
    if not (sec0 == 'B' and e0[0] == 'add' and e0[2] == h and v <= e0[1] < 2 * v): stat['first-not-target-read'] += 1; continue
    # all h events before k1 must be target reads (anticipatory), k1 = first gate that writes h
    reads = [t for t in G if ev[t][1][0] == 'add' and ev[t][1][2] == h and v <= ev[t][1][1] < 2 * v]
    k1 = next(t for t in G if not (ev[t][1][0] == 'add' and ev[t][1][2] == h and v <= ev[t][1][1] < 2 * v))
    pre = [t for t in G if t < k1]
    hik1 = len(b.hi[k1]); lok1 = len(b.lo[k1])
    cand = sorted((hs['U'], c) for c, hs in hosts.items() if hs['last'] < k1 and hs['U'] <= hik1)
    stat['ok' if cand else 'no-host'] += 1
    rows.append(dict(h=h, width=len(Wd.end[h]) - len(Wd.start[h]), pre_reads=pre, k1=k1, k1_lo=lok1, k1_hi=hik1, hosts=cand[:40], nhosts=len(cand)))
print(dict(stat))
for r in rows[:6]: print(r['h'], r['width'], 'pre', r['pre_reads'], 'k1', r['k1'], r['k1_lo'], r['k1_hi'], 'nhosts', r['nhosts'], r['hosts'][:4])
print('hosts-per-hostee hist', dict(Counter(r['nhosts'] for r in rows)))
json.dump(dict(hosts=hosts, rows=rows), open(sys.argv[3], 'w'))
