"""mirror.py: exact single-partner pre-cancel ("mirror") screen.
A recipe-planned entering pair (e, p) works because one pure copy p += c*e0 (before e's first write) makes e's total
leak into the target rows zero: L_e + c * col_p(t) = 0, where col_r(t) is register r's downstream influence on the
target rows of the A+cut+B map at program time t (backward pass, exact Fractions).  For every helper q this screens all
(r, t) with t <= first_write(q) for col_r(t) proportional to L_q.  Targets may not be written in A.
usage: mirror.py WORD OUT.json [--drop-gate SEC:IDX ...] [--helpers all|w9]   (word is data; nothing imported from it)"""
import gzip, json, sys, argparse
from fractions import Fraction as Q
from collections import defaultdict
ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('out'); ap.add_argument('--drop-gate', nargs='*', default=[])
ap.add_argument('--helpers', default='w9'); a = ap.parse_args()
w = json.loads(gzip.decompress(open(a.word, 'rb').read())); V = 112
drop = {(s.split(':')[0], int(s.split(':')[1])) for s in a.drop_gate}
seq = [('A', i, g) for i, g in enumerate(w['A'])] + [('C', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
seq = [(s, i, g) for s, i, g in seq if (s, i) not in drop]
coef = lambda g: Q(g[3], g[4]) if g[0] == 'add' else Q(g[2], g[3])
ent = {int(k) for k in w['start_extra']}; cold = {int(k) for k in w['helper_final']}
first_write = {}
for t, (s, i, g) in enumerate(seq): first_write.setdefault(g[1], t)
n = len(seq)
# backward pass: col[r] = {target y: coef} influence of register r (value at the current time) on final target rows
col = {y: {y: Q(1)} for y in range(V, 2 * V)}
versions = []   # (r, t_lo, t_hi, normalized-key, scale) : col_r valid for forward times in [t_lo, t_hi)
last_change = {}   # r -> time (forward index) at which its current (newer) version starts being valid going backward
def norm(d):
    if not d: return None, None
    y0 = min(d); s = d[y0]; return tuple(sorted((y, x / s) for y, x in d.items())), s
cur_hi = {}   # r -> exclusive upper time of its current version
for t in range(n - 1, -1, -1):
    s_, i_, g = seq[t]; tr = g[1]
    if g[0] == 'add':
        src = g[2]
        if col.get(tr):
            # src's version valid at times > t ends here; record it before changing
            hi = cur_hi.get(src, n + 1)
            if col.get(src): versions.append((src, t + 1, hi) + norm(col[src]))
            cur_hi[src] = t + 1
            d = dict(col.get(src, {})); c = coef(g)
            for y, x in col[tr].items():
                v = d.get(y, 0) + c * x
                if v: d[y] = v
                else: d.pop(y, None)
            col[src] = d
    else:
        if col.get(tr):
            hi = cur_hi.get(tr, n + 1); versions.append((tr, t + 1, hi) + norm(col[tr])); cur_hi[tr] = t + 1
            c = coef(g); col[tr] = {y: x * c for y, x in col[tr].items()}
for r, d in col.items():
    if d: versions.append((r, 0, cur_hi.get(r, n + 1)) + norm(d))
index = defaultdict(list)
for r, lo, hi, key, sc in versions:
    if key is not None: index[key].append((r, lo, hi, sc))
# leaks of helpers = their column at time 0 (initial value influence), raw (before precondition transform)
H = [k for k in range(2 * V, 2 * V + w['report']['R'])] if 'R' in w['report'] else sorted(k for k in col if k >= 2 * V)
leak = {k: col.get(k, {}) for k in H}
w9 = [k for k in H if k not in ent and k not in cold and leak[k]]
targets = H if a.helpers == 'all' else w9
res = {}; hits_total = 0
for q in targets:
    L = leak[q]
    if not L: continue
    key, sc = norm(L); fw = first_write.get(q, n)
    hits = []
    for r, lo, hi, s2 in index.get(key, []):
        if r == q: continue
        # need some time t in [lo, hi) with t <= fw (insert before q's first write) and, if t is in A, r not a target
        t_hi = min(hi, fw + 1)
        if lo >= t_hi: continue
        tA_end = len(w['A'])
        if V <= r < 2 * V and t_hi <= tA_end: continue
        c = -sc / s2
        hits.append(dict(r=r, t_lo=lo, t_hi=t_hi, c=str(c), r_kind=('target' if V <= r < 2 * V else 'data' if r < V else 'entering' if r in ent else 'cold' if r in cold else 'ordinary')))
    res[q] = dict(first_write=fw, leak_rows=len(L), hits=hits)
    hits_total += bool(hits)
json.dump(dict(word=a.word.split('scratchpad/')[-1], dropped=sorted(map(list, drop)), n_helpers_screened=len(res), helpers_with_hit=hits_total,
               versions=len(versions), results={str(k): v for k, v in res.items()}), open(a.out, 'w'), indent=1)
print('screened', len(res), 'helpers; with a single-partner mirror:', hits_total, '| column versions', len(versions))
for q, v in res.items():
    if v['hits']: print('  ', q, 'leak rows', v['leak_rows'], 'first_write', v['first_write'], v['hits'][:3])
