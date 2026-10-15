"""qlife.py: full-program life of helper q: every vertex (main/tail/cleanup) with q's row class after the gate
(pure = only q_init and ordinary-helper dirt; data/target/residual columns flagged)."""
import json, sys, os
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traj as TJ
w = TJ.load(sys.argv[1]); QS = [int(x) for x in sys.argv[2:]]
v = w['report']['v']; R = w['report']['R']; n = 2 * v + R
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
seq = TJ.program(w)
def coef(g): return F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
rows = [{r: F(1)} for r in range(n)]
def cls(row, q):
    d = sum(1 for k in row if k < v); t = sum(1 for k in row if v <= k < 2 * v)
    res = sum(1 for k in row if k >= 2 * v and (k in ent or k in low)); h = sum(1 for k in row if k >= 2 * v and k != q and k not in ent and k not in low)
    return dict(qcoef=str(row.get(q, 0)), data=d, targets=t, residual=res, ordinary=h)
life = {q: [] for q in QS}
for pos, (sec, i, g, fr) in enumerate(seq):
    if g[0] == 'add':
        t, s = g[1], g[2]; c = coef(g); rt = rows[t]
        for k, x in list(rows[s].items()):
            a = rt.get(k, F(0)) + c * x
            if a: rt[k] = a
            else: rt.pop(k, None)
    else:
        t = g[1]; c = coef(g); rows[t] = {k: c * x for k, x in rows[t].items()}
    for q in QS:
        if q in TJ.regs(g):
            life[q].append(dict(pos=pos, sec=sec, i=i, gate=g[:-1] if sec in ('A', 'B') else g[:5], frame=fr, after=cls(rows[q], q)))
for q in QS:
    print('== q', q)
    for e in life[q]: print('  ', e['pos'], e['sec'], e['i'], e['gate'], 'frame', e['frame'], e['after'])
json.dump(life, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'out', 'QLIFE.json'), 'w'), indent=0)
