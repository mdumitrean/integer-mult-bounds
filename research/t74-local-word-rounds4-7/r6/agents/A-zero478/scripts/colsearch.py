"""colsearch.py: for helper q, try every copy holder c with  [c += q] inserted before q's first write (A) and
[q -= c] inserted right after B-index T1; simulate the q_init column through A+cut+B exactly and report holders for
which no target row keeps a q_init coefficient.  usage: colsearch.py WORD q T1 OUT.json"""
import json, sys, os
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traj as TJ
w = TJ.load(sys.argv[1]); q = int(sys.argv[2]); T1 = int(sys.argv[3]); OUT = sys.argv[4]
v = w['report']['v']; R = w['report']['R']
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
main = [('A', i, g) for i, g in enumerate(w['A'])] + [('cut', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
first = next(k for k, (s, i, g) in enumerate(main) if g[0] == 'add' and g[1] == q or g[0] == 'scale' and g[1] == q)
tpos = next(k for k, (s, i, g) in enumerate(main) if s == 'B' and i == T1)
def coef(g): return F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
def run(c):
    col = {q: F(1)}
    for k, (s, i, g) in enumerate(main):
        if k == first: col[c] = col.get(c, F(0)) + col.get(q, F(0))
        if g[0] == 'add':
            t, src = g[1], g[2]; x = col.get(src)
            if x:
                a = col.get(t, F(0)) + coef(g) * x
                if a: col[t] = a
                else: col.pop(t)
        elif g[1] in col: col[g[1]] = col[g[1]] * coef(g)
        if k == tpos:
            x = col.get(c)
            if x:
                a = col.get(q, F(0)) - x
                if a: col[q] = a
                else: col.pop(q)
    tg = {y: str(a) for y, a in col.items() if v <= y < 2 * v}
    return tg, {y: str(a) for y, a in col.items() if not (v <= y < 2 * v)}
res = []
for c in range(2 * v, 2 * v + R):
    if c == q or c in ent or c in low: continue
    tg, other = run(c)
    res.append(dict(c=c, leak_targets=len(tg), targets=tg, other=other))
res.sort(key=lambda r: (r['leak_targets'], len(r['other'])))
json.dump(dict(q=q, first=first, T1=T1, results=res), open(OUT, 'w'), indent=0)
print('q', q, 'baseline leak targets', len(run(q + 0 if False else 2 * v + R - 1)[0]) if False else '', 'best:')
for r in res[:12]: print('  c', r['c'], 'leak targets', r['leak_targets'], r['targets'], '| q_init left in', r['other'])
