"""qdiag.py: where does helper q's dirt live, and why no transvection partner? usage: qdiag.py WORD Q"""
import json, gzip, sys, collections
from fractions import Fraction as Fr
W = json.load(gzip.open(sys.argv[1])); q = int(sys.argv[2]); V = 112; R = W['report']['R']; n = 2 * V + R
E = set(map(int, W['start_extra'])); K = set(map(int, W['helper_final'])); targets = set(range(V, 2 * V))
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
main = [('A', i, x) for i, x in enumerate(W['A'])] + [('cut', i, x) for i, x in enumerate(W['cut'])] + [('B', i, x) for i, x in enumerate(W['B'])]
val = [{x: Fr(1)} for x in range(n)]
carriers_hist = collections.Counter(); diag = collections.Counter(); examples = []
for t, (sec, i, gt) in enumerate(main):
    x = gt[1]
    if gt[0] == 'add':
        s = gt[2]; c = coef(gt); dst = val[x]
        for k, v in val[s].items():
            yv = dst.get(k, 0) + c * v
            if yv: dst[k] = yv
            else: dst.pop(k, None)
    else:
        c = coef(gt); val[x] = {k: c * v for k, v in val[x].items()}
    if t % 25: continue
    car = [z for z in range(n) if z not in targets and z != q and val[z].get(q, 0)]
    carriers_hist[len(car)] += 1
    for a in car:
        ca = tuple(sorted((k, v) for k, v in val[a].items() if k < 2 * V))
        partners = [b for b in range(n) if b != a and b not in targets and tuple(sorted((k, v) for k, v in val[b].items() if k < 2 * V)) == ca]
        if not partners: diag['carrier-no-equal-clean-partner'] += 1; continue
        for b in partners:
            d = {k: val[a].get(k, 0) - val[b].get(k, 0) for k in set(val[a]) | set(val[b]) if k >= 2 * V}
            d = {k: v for k, v in d.items() if v}
            if not d.get(q): diag['partner-same-q-dirt'] += 1; continue
            bad = [k for k in d if (k in E and k != q) or k in K]
            if bad: diag['partner-delta-hits-entering/ended'] += 1
            else:
                diag['partner-ok-before-frames'] += 1
                if len(examples) < 5: examples.append((sec, i, a, b, len(d)))
print('q', q, 'carriers per sampled time', sorted(carriers_hist.items())[:12], '...')
print(dict(diag)); print('examples', examples)
