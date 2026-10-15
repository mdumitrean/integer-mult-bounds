"""multiholder.py: for helper q with narrowed start vector u (= q's first frame), find copy holders c whose frame just before
q's first write is () or [u] and whose next frame contains u, compute the target-row transfer P_c of a unit placed in c at
that time, and list them with their first-frame dimension (a copy is free iff c's next frame is exactly [u] or c is at [u]).
usage: multiholder.py WORD q u OUT.json"""
import json, sys, os
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traj as TJ
w = TJ.load(sys.argv[1]); q = int(sys.argv[2]); u = int(sys.argv[3]); OUT = sys.argv[4]
v = w['report']['v']; R = w['report']['R']
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
main = [('A', i, g) for i, g in enumerate(w['A'])] + [('cut', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
t0 = next(k for k, (s, i, g) in enumerate(main) if g[1] == q)
def coef(g): return F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
def transfer(c, start):
    col = {c: F(1)}
    for k in range(start, len(main)):
        s, i, g = main[k]
        if g[0] == 'add':
            t, src = g[1], g[2]; x = col.get(src)
            if x:
                a = col.get(t, F(0)) + coef(g) * x
                if a: col[t] = a
                else: col.pop(t)
        elif g[1] in col: col[g[1]] = col[g[1]] * coef(g)
    return {y: a for y, a in col.items() if v <= y < 2 * v}
def bitspan(fr):
    span = {0}
    for b in fr: span |= {x ^ b for x in span}
    return span
Lq = transfer(q, 0)
cands = []
for c in range(2 * v, 2 * v + R):
    if c == q or c in ent or c in low: continue
    before = None; nxt = None
    for k, (s, i, g) in enumerate(main):
        if c in TJ.regs(g) and s != 'cut':
            if k < t0: before = g[-1]
            elif nxt is None: nxt = (s, i, g[-1])
    fb = before or []
    if fb and (len(fb) > 1 or fb[0] != u): continue          # frame at t0 must be () or [u]
    if nxt is None or u not in bitspan(nxt[2]): continue    # next frame must contain u
    P = transfer(c, t0)
    free = (fb == [u]) or (len(nxt[2]) == 1)
    cands.append(dict(c=c, frame_t0=fb, next=nxt, free=free, P={str(y): str(a) for y, a in sorted(P.items())}))
json.dump(dict(q=q, u=u, t0=t0, Lq={str(y): str(a) for y, a in sorted(Lq.items())}, cands=cands), open(OUT, 'w'), indent=0)
print('q', q, 'u', u, 't0', t0, 'Lq', {y: str(a) for y, a in sorted(Lq.items())}, '| candidates', len(cands), 'free', sum(c['free'] for c in cands))
tq = set(Lq)
for c in cands:
    if set(map(int, c['P'])) & tq: print('  c', c['c'], 'free' if c['free'] else 'split', 'next', c['next'][:2], 'dim', len(c['next'][2]), 'P', c['P'])
