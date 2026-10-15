"""cutrank.py: can any SET of B deliveries be replaced by free cut gates?  Each B delivery g = (t += a*s), s a non-target,
contributes a rank-one tensor m_g (x) [v_g] to the final target rows, where v_g = value of s at that time (row over the
initial state), [.] = class modulo span(centre values at the cut) + ordinary-helper coordinates (absorbed by the derived
compensation), and m_g = e_t pushed through every later target-only gate of B and the early tail.  Cut gates can add any
element of R^targets (x) span(centres) for free, so a set S is replaceable iff sum_S a_g m_g (x) [v_g] = 0.  We compute the
rank of the delivery tensors modulo a large prime; full rank (= #deliveries) proves no subset is replaceable (a rational
dependency would survive reduction mod p after clearing denominators... we report the mod-p rank, which lower-bounds the
rational rank, so full mod-p rank is a proof).  usage: cutrank.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections, time
from fractions import Fraction as Q
V = 112; P = (1 << 61) - 1
t0 = time.time()
w = json.load(gzip.open(sys.argv[1])); R = w['report']['R']; n = 2 * V + R
entering = set(map(int, w['start_extra'])); cold = set(map(int, w['helper_final'])) - entering
ordset = {k for k in range(2 * V, n) if k not in entering and k not in cold}
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
rows = [{k: Q(1)} for k in range(n)]
def apply(e, rows):
    if e[0] == 'add':
        t, s, q = e[1], e[2], coef(e); d = rows[t]
        for k, x in rows[s].items():
            y = d.get(k, 0) + q * x
            if y: d[k] = y
            else: d.pop(k, None)
    else:
        t, q = e[1], coef(e); rows[t] = {k: q * x for k, x in rows[t].items()}
for e in w['A']: apply(e, rows)
strip = lambda v: {k: x for k, x in v.items() if k not in ordset}
cb = []
def red(v, basis):
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
    v = red(strip(rows[c]), cb)
    if v: cb.append((min(v), v))
# collect deliveries with their source values
dels = []
B = w['B']
for j, e in enumerate(B):
    if e[0] == 'add' and V <= e[1] < 2 * V and not (V <= e[2] < 2 * V):
        dels.append(dict(j=j, t=e[1], a=coef(e), v=red(strip(rows[e[2]]), cb)))
    apply(e, rows)
# push e_t through later target-only gates (B target-target and target scales, then early-tail gates on targets)
tail = [w['cleanup'][i][:-1] + [U] for i, U in w['early_cleanup']]
later = [(j, e) for j, e in enumerate(B) if (e[0] == 'scale' and V <= e[1] < 2 * V) or (e[0] == 'add' and V <= e[1] < 2 * V and V <= e[2] < 2 * V)]
tailT = [e for e in tail if V <= e[1] < 2 * V and (e[0] == 'scale' or V <= e[2] < 2 * V)]
tail_nontarget_into_target = sum(1 for e in tail if e[0] == 'add' and V <= e[1] < 2 * V and not (V <= e[2] < 2 * V))
def push(t, j):
    # column vector over targets: how a unit placed in t at time j reaches the final target rows (transpose action)
    m = {t: Q(1)}
    for jj, e in later:
        if jj <= j: continue
        m = act(e, m)
    for e in tailT: m = act(e, m)
    return m
def act(e, m):
    # value-vector propagation: target registers hold values; vector m[r] = multiplicity of the unit in register r
    m = dict(m)
    if e[0] == 'scale':
        if e[1] in m: m[e[1]] = m[e[1]] * coef(e)
    else:
        t, s, q = e[1], e[2], coef(e)
        if s in m:
            y = m.get(t, 0) + q * m[s]
            if y: m[t] = y
            else: m.pop(t, None)
    return m
def modp(x): return x.numerator % P * pow(x.denominator % P, P - 2, P) % P
vecs = []
for d in dels:
    m = push(d['t'], d['j'])
    tensor = {}
    for tt, x in m.items():
        for k, y in d['v'].items():
            z = modp(d['a'] * x * y)
            if z: tensor[(tt, k)] = z
    vecs.append(tensor)
# incremental elimination mod P
piv = {}; rank = 0; dependent = []
for i, v in enumerate(vecs):
    v = dict(v)
    while v:
        key = min(v)
        if key in piv:
            b = piv[key]; f = v[key]
            for k, x in b.items():
                y = (v.get(k, 0) - f * x) % P
                if y: v[k] = y
                else: v.pop(k, None)
        else:
            inv = pow(v[key], P - 2, P); piv[key] = {k: x * inv % P for k, x in v.items()}; rank += 1; break
    else:
        dependent.append(i)
res = dict(word=sys.argv[1].split('/')[-1], deliveries=len(dels), rank_mod_p=rank, dependent_indices=[dels[i]['j'] for i in dependent],
           zero_quotient=sum(1 for d in dels if not d['v']), early_tail_nontarget_into_target=tail_nontarget_into_target,
           centre_span_rank=len(cb), seconds=round(time.time() - t0, 1))
json.dump(res, open(sys.argv[2], 'w'), indent=1); print(res)
