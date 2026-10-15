"""classify.py: which B gates writing a port read a source whose current A+cut+B prefix row is pure helper dirt.
usage: classify.py WORD.json.gz OUT.json
A pure-dirt read (t a port, source row supported only on helper columns k >= 2v) changes the A+cut+B map only in port-row
helper columns, which the derived compensation cancels.  Exact rationals throughout."""
import gzip, json, sys, collections
from fractions import Fraction as F
w = json.load(gzip.open(sys.argv[1])); r = w['report']; V = r['v']; R = r['R']; n = 2 * V + R
entering = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final'])); cold = low - entering
rows = [{k: F(1)} for k in range(n)]
def coef(e): return F(e[3], e[4]) if e[0] == 'add' else F(e[2], e[3])
def apply(e):
    c = coef(e); t = e[1]
    if e[0] == 'scale':
        rows[t] = {k: a * c for k, a in rows[t].items()}; return
    d = rows[t]
    for k, a in rows[e[2]].items():
        y = d.get(k, 0) + c * a
        if y: d[k] = y
        else: d.pop(k, None)
for e in w['A'] + w['cut']: apply(e)
out = []; cls = collections.Counter()
for i, e in enumerate(w['B']):
    if e[0] == 'add' and V <= e[1] < 2 * V:
        src = rows[e[2]]
        nonh = {k for k in src if k < 2 * V}
        res = {k for k in src if k in entering or k in cold}
        kind = 'D' if e[2] < V else 'P' if e[2] < 2 * V else 'H'
        pure = not nonh
        tag = ('pure' if pure else 'mixed') + ('-residual' if pure and res else '')
        cls[(kind, tag)] += 1
        if pure:
            out.append(dict(B=i, t=e[1], s=e[2], c=[e[3], e[4]], frame=e[-1], dirt_support=len(src),
                            residual_helpers=sorted(res), src_is_fresh=(src == {e[2]: F(1)})))
    apply(e)
json.dump(dict(word=sys.argv[1].split('/')[-1], classes={f'{a}:{b}': c for (a, b), c in sorted(cls.items())}, pure=out),
          open(sys.argv[2], 'w'), indent=1)
print(sys.argv[1].split('/')[-1], {f'{a}:{b}': c for (a, b), c in sorted(cls.items())})
print('pure-dirt port reads:', len(out), '| fresh-source', sum(o['src_is_fresh'] for o in out), '| touching residual helpers', sum(bool(o['residual_helpers']) for o in out))
for o in out[:12]: print('  ', o)
