"""census.py: obstruction test for compensation-absorbed kernels that compensate a deleted port read g = (t += c s) at base
B index i with any number of inserts (t += lam y) inside t's port window on W = base - g (no gate between them reads or
scales t, so every such insert reaches the final ports through the same propagation as g).
Necessary condition: each insert is individually frame-feasible on W (exact single-insert test conelu.LU.ok = r3 agent B's
cone test, base caps; pdprice showed these compensation changes leave the caps unchanged).  Absorbed exactness needs
nonord(c * row_s(i)) = sum lam * nonord(row_y(p)).  If the left side is outside the span of the non-ordinary parts of all
feasible inserts, no such kernel exists.  usage: census.py WORD.json.gz OUT.json B_INDEX..."""
import json, os, sys, time
from fractions import Fraction as Fr
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); sys.path.insert(1, HERE)
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from conelu import LU
P = H.Pricer(sys.argv[1], check_literal=True, interval=False); w = P.base
V = w['report']['v']; n = 2 * V + w['report']['R']; NA, NC = len(w['A']), len(w['cut'])
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
ordinary = lambda k: k >= 2 * V and k not in ent and k not in low
nono = lambda row: {k: a for k, a in row.items() if not ordinary(k)}
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
def apply(e, rows):
    c = coef(e); t = e[1]
    if e[0] == 'scale': rows[t] = {k: a * c for k, a in rows[t].items()}; return
    d = dict(rows[t])
    for k, a in rows[e[2]].items():
        y = d.get(k, 0) + c * a
        if y: d[k] = y
        else: d.pop(k, None)
    rows[t] = d
class Basis:
    def __init__(self): self.piv = []
    def reduce(self, v):
        v = dict(v)
        for pk, pv in self.piv:
            if v.get(pk):
                f = v[pk] / pv[pk]
                for k, x in pv.items():
                    z = v.get(k, 0) - f * x
                    if z: v[k] = z
                    else: v.pop(k, None)
        return v
    def add(self, v):
        r = self.reduce(v)
        if r: self.piv.append((min(r), r)); return True
        return False
DUMP = os.environ.get('CENSUS_DUMP_ALL') == '1'
porto = lambda e, t: (e[0] == 'add' and e[2] == t) or (e[0] == 'scale' and e[1] == t)
pre = [{k: Fr(1)} for k in range(n)]
for e in w['A'] + w['cut']: apply(e, pre)
res = []
for i in map(int, sys.argv[3:]):
    t0 = time.time(); g = w['B'][i]; t, s = g[1], g[2]
    W = H.compile_edits(w, dict(delete=[i])); BW = W['B']
    try: lu = LU(P, W)
    except F.Infeasible: res.append(dict(B=i, status='deletion-infeasible')); print(res[-1], flush=True); continue
    lo = i
    while lo > 0 and not porto(BW[lo - 1], t): lo -= 1
    hi = i
    while hi < len(BW) and not porto(BW[hi], t): hi += 1
    rows = [dict(r) for r in pre]; tgt = None; span = Basis(); tested = feas = 0; last = {}; ins = []
    for p in range(0, hi + 1):            # insert before W's B index p; rows = values before p
        if p == i: tgt = {k: coef(g) * a for k, a in nono(rows[s]).items()}
        if p >= lo:
            for y in range(n):
                if y == t: continue
                nv = nono(rows[y])
                if not nv: continue
                if last.get(y) is rows[y]: continue            # same value object as at the last feasible test: no new vector
                tested += 1
                if lu.ok(t, y, NA + NC + p):
                    feas += 1; last[y] = rows[y]
                    if span.add(nv) or DUMP: ins.append((y, p, nv))
        if p < len(BW): apply(BW[p], rows)
    if tgt is None: tgt = {k: coef(g) * a for k, a in nono(rows[s]).items()}
    inside = not span.reduce(tgt)
    res.append(dict(B=i, t=t, s=s, window=[lo, hi], target=sorted((k, str(a)) for k, a in tgt.items()), tested=tested,
                    feasible=feas, span_rank=len(span.piv), target_in_span=inside, sec=round(time.time() - t0, 1),
                    inserts=[dict(y=y, p=p, nv=sorted((k, str(a)) for k, a in nv.items())) for y, p, nv in ins] if inside else []))
    print({k: res[-1][k] for k in ('B', 't', 's', 'window', 'tested', 'feasible', 'span_rank', 'target_in_span', 'sec')}, flush=True)
json.dump(res, open(sys.argv[2], 'w'), indent=1)
