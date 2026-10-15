"""pairscreen.py: zero a narrowable helper q's target dirt response with clean-cancelling pair deliveries.
Op (t, y, a, b, lam): insert into B after gate t:  y += lam*b ; y += -lam*a   where a, b are non-target registers with
equal clean (X,Y) parts at t, so only lam*(dirt_b - dirt_a) reaches target y.  Frames stay feasible (no change) when
frame_a, frame_b are inside y's frame at t in the NARROWED word's optimal literal frames.  Required: the op's dirt
difference vanishes on entering and ended helpers (their responses / identities unchanged), and y's later value reaches
no non-target final row (so the cleanup is unaffected).  The op changes q's column of the A+cut+B target response by
lam*delta_q*T(t)[:, y]; we look for ops whose combination cancels L_q exactly.
usage: pairscreen.py WORD NARROW.jsonl TOOLKIT Q OUT.json"""
import json, gzip, sys, collections, copy, os
from fractions import Fraction as Fr
word_p, narrow_p, tk, qarg, out_p = sys.argv[1:6]
sys.path.insert(0, tk)
import frames as F
from word import inline
from model import cone_caps
from writeback import write_back
B = "0.001679754956125544"
q = int(qarg)
W = json.load(gzip.open(word_p)); V = 112; R = W['report']['R']; n = 2 * V + R
rows = [json.loads(l) for l in open(narrow_p) if l.strip()]
basis = next(r['basis'] for r in rows if r['q'] == q and r.get('status') == 'ok' and r.get('delta') == -2116454)
Wn = copy.deepcopy(W); Wn['start_extra'][str(q)] = basis
caps, comp = cone_caps(Wn)
g = F.Graph(inline(Wn, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
r = F.optimal_frames(inline(Wn, True), F.Costs(B), check_literal=False, graph=g)
Wl = write_back(Wn, g, r['assign'])
print('narrowed', q, basis, 'cost', r['cost'], 'certified', r['certified'], 'profile', dict(sorted(r['profile'].items())), flush=True)
E = set(map(int, Wn['start_extra'])); K = set(map(int, Wn['helper_final']))
targets = set(range(V, 2 * V))
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
A_, C_, B_ = Wl['A'], Wl['cut'], Wl['B']
main = [('A', i, x) for i, x in enumerate(A_)] + [('cut', i, x) for i, x in enumerate(C_)] + [('B', i, x) for i, x in enumerate(B_)]
nA, nC = len(A_), len(C_)
start = [[p] for p in Wl['ports']] + [[] for _ in range(V + R)]
for k, U in Wl.get('start_extra', {}).items(): start[int(k)] = list(U)
fr = [F.span(tuple(s)) for s in start]
val = [{x: Fr(1)} for x in range(n)]
# backward pass first: target adjoint T(t)[:, y] for targets y, and whether y(t) reaches a non-target final row.
Tc = [dict() for _ in range(n)]
for y in targets: Tc[y] = {y: Fr(1)}
NT = [False] * n           # does register value now reach some non-target final row?  (forward-closure flag via reads)
for x in range(n): NT[x] = x not in targets
snapT = {}
reachNT = {}
for t in range(len(main) - 1, nA + nC - 1, -1):     # B section only (insertion points after gate t, t in B)
    snapT[t] = {y: dict(Tc[y]) for y in targets}
    reachNT[t] = {y: NT[y] for y in targets}
    gt = main[t][2]; x = gt[1]
    if gt[0] == 'add':
        s = gt[2]; c = coef(gt)
        if Tc[x]:
            dst = Tc[s]
            for k, v in Tc[x].items():
                yv = dst.get(k, 0) + c * v
                if yv: dst[k] = yv
                else: dst.pop(k, None)
        if NT[x]: NT[s] = True
    else:
        c = coef(gt); Tc[x] = {k: c * v for k, v in Tc[x].items()}
# forward pass to B, collecting admissible (t, y) with pairs
def clean_key(x): return tuple(sorted((k, v) for k, v in val[x].items() if k < 2 * V))
vecs = []; ops = []; diag = collections.Counter()
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
    if gt[-1] is not None: fr[x] = F.span(tuple(gt[-1]))
    if t < nA + nC or t % 3: continue           # B insertion points (every 3rd gate to bound work)
    groups = collections.defaultdict(list)
    for z in range(n):
        if z in targets: continue
        if val[z].get(q, 0) == 0 and all(val[z].get(k, 0) == 0 for k in ()): pass
        groups[clean_key(z)].append(z)
    pairs = []
    for key, mem in groups.items():
        if len(mem) < 2: continue
        hold = [z for z in mem if val[z].get(q, 0)]
        for a in hold:
            for b in mem:
                if b == a: continue
                d = {}
                for k in set(val[a]) | set(val[b]):
                    if k < 2 * V: continue
                    w_ = val[b].get(k, 0) - val[a].get(k, 0)
                    if w_: d[k] = w_
                if not d.get(q) or any(k in E and k != q or k in K for k in d): continue
                pairs.append((a, b, d[q], fr[a] | fr[b]))
    diag['times'] += 1; diag['pairs'] += len(pairs)
    if not pairs: continue
    diag['times_with_pairs'] += 1
    for y in targets:
        if reachNT[t][y]: diag['y_reach_nontarget'] += 1; continue
        u = snapT[t][y]
        if not u: diag['y_no_effect'] += 1; continue
        hit = False
        for (a, b, dq, fab) in pairs:
            if fab <= fr[y]:
                vecs.append(u); ops.append((t, y, a, b, str(dq))); hit = True; break
        if not hit: diag['y_frame_fail'] += 1
        else: diag['y_ok'] += 1
Lq = {y: val[y].get(q, 0) for y in targets if val[y].get(q, 0)}
print('leak rows', len(Lq), 'admissible (t,y) vectors', len(vecs), dict(diag), flush=True)
# exact span test and a sparse solution by greedy elimination
piv = {}; owner = {}
def reduce(v):
    v = dict(v); comb = {}
    while v:
        k = min(v)
        if k in piv:
            pv, pc = piv[k]; f = v[k] / pv[k]
            for kk, xx in pv.items():
                yv = v.get(kk, 0) - f * xx
                if yv: v[kk] = yv
                else: v.pop(kk, None)
            for kk, xx in pc.items():
                comb[kk] = comb.get(kk, 0) - f * xx
        else: return v, comb
    return v, comb
for idx, v in enumerate(vecs):
    rv, comb = reduce(v)
    if rv:
        comb = {kk: xx for kk, xx in comb.items() if xx}; comb[idx] = comb.get(idx, 0) + 1
        piv[min(rv)] = (rv, comb)
rest, comb = reduce(Lq)
ok = not rest
sol = {}
if ok:
    # Lq = sum over pivots used: Lq - sum f*pv = 0  => Lq = sum (-comb) * vecs
    sol = {idx: -c for idx, c in comb.items() if c}
res = dict(q=q, basis=basis, narrowed_cost=r['cost'], certified=r['certified'], leak_rows=len(Lq), vectors=len(vecs),
           rank=len(piv), in_span=ok, solution=[dict(op=ops[i], coef=str(c)) for i, c in sorted(sol.items())])
json.dump(res, open(out_p, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'solution'}), 'solution_ops', len(sol), flush=True)
for s_ in res['solution'][:12]: print('  ', s_)
