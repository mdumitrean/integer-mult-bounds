"""leaks.py: where each helper q's initial value goes in the base word (A+cut+B map, auditor semantics).
usage: leaks.py WORD.json.gz OUT.json q1 q2 ..."""
import gzip, json, sys
from fractions import Fraction as F
w = json.load(gzip.open(sys.argv[1])); OUT = sys.argv[2]; QS = [int(x) for x in sys.argv[3:]]
v = w['report']['v']; R = w['report']['R']; n = 2 * v + R
secs = [('A', g) for g in w['A']] + [('cut', g) for g in w['cut']] + [('B', g) for g in w['B']]
idx = {'A': 0, 'cut': 0, 'B': 0}; pos = []
for s, g in secs: pos.append((s, idx[s])); idx[s] += 1
def coef(g): return F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
res = {}
for q in QS:
    col = {q: F(1)}          # coefficient of q_init in each register's current value
    rowq = {q: F(1)}         # q's current value as a combination of initial registers (full row)
    rows = {}                # lazily tracked rows of registers that feed q
    touch = []; deliveries = []; pure = []   # pure: gate indices where q's row == e_q before the gate
    # full rows needed for rowq: track all rows lazily (only registers that ever flow into q matter; do full)
    allrows = [None] * n
    def row(r): 
        if allrows[r] is None: allrows[r] = {r: F(1)}
        return allrows[r]
    for k, (s, g) in enumerate(secs):
        sec, i = pos[k]
        if g[0] == 'add':
            t, src = g[1], g[2]; c = coef(g)
            rt, rs = row(t), row(src)
            for key, x in list(rs.items()):
                a = rt.get(key, F(0)) + c * x
                if a: rt[key] = a
                else: rt.pop(key, None)
            cs = col.get(src, F(0))
            if cs:
                a = col.get(t, F(0)) + c * cs
                if a: col[t] = a
                else: col.pop(t, None)
                if v <= t < 2 * v: deliveries.append(dict(sec=sec, i=i, t=t, src=src, c=str(c), dq=str(c * cs), frame=g[-1]))
        else:
            t = g[1]; c = coef(g); rt = row(t)
            for key in list(rt): rt[key] = rt[key] * c
            if t in col: col[t] = col[t] * c
        if q in (g[1:3] if g[0] == 'add' else g[1:2]):
            touch.append(dict(sec=sec, i=i, gate=g[:-1], frame=g[-1], role='write' if g[1] == q else 'read', q_pure_after=(row(q) == {q: F(1)})))
    leak = {y: str(a) for y, a in col.items() if v <= y < 2 * v}
    carriers = {r: str(a) for r, a in col.items() if not (v <= r < 2 * v)}
    res[q] = dict(leak_targets=leak, carriers_end_of_B=carriers, q_row_end_of_B={str(k): str(x) for k, x in row(q).items()},
                  touches=touch, target_deliveries=deliveries)
    print(q, 'leak', leak, '| carriers', carriers, '| q row at end of B', {k: str(x) for k, x in row(q).items()}, '| touches', len(touch), '| deliveries', len(deliveries))
json.dump(res, open(OUT, 'w'), indent=1)
