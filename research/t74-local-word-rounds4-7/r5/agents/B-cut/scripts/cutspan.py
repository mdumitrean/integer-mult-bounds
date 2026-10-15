"""cutspan.py: for every B gate t += a*s into a target t, is the value of s at that time in
span(centre values at the cut) + span(unit vectors of ordinary helpers)?  If so the delivery could be replaced by free cut
gates (target levels stay empty) plus the re-derived compensation.  Values are exact rationals over the initial state.
Also reports whether the delivery commutes back to the cut (no B gate before it reads or scales t).
usage: cutspan.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
from fractions import Fraction as Q
V = 112
w = json.load(gzip.open(sys.argv[1])); R = w['report']['R']; n = 2 * V + R
entering = set(map(int, w['start_extra'])); lowends = set(map(int, w['helper_final'])); cold = lowends - entering
ordinary = [k for k in range(2 * V, n) if k not in entering and k not in cold]
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
rows = [{k: Q(1)} for k in range(n)]
def apply(e):
    if e[0] == 'add':
        t, s, q = e[1], e[2], coef(e)
        d = rows[t]
        for k, x in rows[s].items():
            y = d.get(k, 0) + q * x
            if y: d[k] = y
            else: d.pop(k, None)
    else:
        t, q = e[1], coef(e); rows[t] = {k: q * x for k, x in rows[t].items()}
for e in w['A']: apply(e)
cent = {c: dict(rows[c]) for c in w['centers']}
# basis for span(centres) + span(ordinary unit vectors): reduce centre rows modulo ordinary helper coordinates
ordset = set(ordinary)
def strip(v): return {k: x for k, x in v.items() if k not in ordset}
basis = []   # list of (pivot, vector) in echelon form (exact Gaussian elimination)
def reduce(v):
    v = dict(v)
    for p, b in basis:
        if p in v:
            f = v[p] / b[p]
            for k, x in b.items():
                y = v.get(k, 0) - f * x
                if y: v[k] = y
                else: v.pop(k, None)
    return v
for c in w['centers']:
    v = reduce(strip(cent[c]))
    if v: basis.append((min(v), v))
print('centre span rank (mod ordinary helpers):', len(basis))
out = []; cnt = collections.Counter()
for j, e in enumerate(w['B']):
    if e[0] == 'add' and V <= e[1] < 2 * V:
        s = e[2]; val = strip(rows[s]); r = reduce(val)
        inspan = not r
        back = not any((h[0] == 'scale' and h[1] == e[1]) or (h[0] == 'add' and h[2] == e[1]) for h in w['B'][:j])
        kind = 'data' if s < V else 'target' if s < 2 * V else 'helper'
        cnt[(kind, inspan, back)] += 1
        if inspan: out.append(dict(j=j, gate=e, source_kind=kind, commutes_back_to_cut=back))
    apply(e)
print('B deliveries into targets (source kind, in centre span, commutes back to cut):', dict(cnt))
json.dump(dict(word=sys.argv[1].split('/')[-1], centre_span_rank=len(basis), counts={str(k): v for k, v in cnt.items()}, in_span=out), open(sys.argv[2], 'w'), indent=1)
print('in-span deliveries:', len(out), out[:5])
