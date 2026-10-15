"""tscreen.py: dirt transvections a <- a + mu*(b - a) (a, b non-target, equal clean (X,Y) parts and frame(b) inside frame(a) at t
in the NARROWED word's optimal literal frames; 2 gates at that frame, no climb, any dyadic mu != 1).  Effect: helper dirt
column changes by -mu * T(t)[:, a] (x) delta, delta = dirt_a - dirt_b.  Kept: delta vanishes on entering and ended helpers
(except q), and a(t) reaches no ended helper's final row (A+cut+B+tail adjoint), so ended identities hold; non-target FULL
rows change and must be corrected in the frame-free cleanup (reported, not built here).
Goal: L_q (q's target dirt column) = sum mu_i * T_i * delta_i[q] with a sparse exact solution.
usage: tscreen.py WORD NARROW.jsonl TOOLKIT Q OUT.json [stride]"""
import json, gzip, sys, collections, copy
from fractions import Fraction as Fr
word_p, narrow_p, tk, qarg, out_p = sys.argv[1:6]; stride = int(sys.argv[6]) if len(sys.argv) > 6 else 1
sys.path.insert(0, tk)
import frames as F
from word import inline
from model import cone_caps
from writeback import write_back
B = "0.001679754956125544"; q = int(qarg)
W = json.load(gzip.open(word_p)); V = 112; R = W['report']['R']; n = 2 * V + R
rows = [json.loads(l) for l in open(narrow_p) if l.strip()]
basis = next(r['basis'] for r in rows if r['q'] == q and r.get('status') == 'ok' and r.get('delta') == -2116454)
Wn = copy.deepcopy(W); Wn['start_extra'][str(q)] = basis
caps, comp = cone_caps(Wn)
g = F.Graph(inline(Wn, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
r = F.optimal_frames(inline(Wn, True), F.Costs(B), check_literal=False, graph=g)
Wl = write_back(Wn, g, r['assign'])
E = set(map(int, Wl['start_extra'])); K = set(map(int, Wl['helper_final'])); targets = set(range(V, 2 * V))
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
main = [('A', i, x) for i, x in enumerate(Wl['A'])] + [('cut', i, x) for i, x in enumerate(Wl['cut'])] + [('B', i, x) for i, x in enumerate(Wl['B'])]
tail = [('T', j, Wl['cleanup'][ci]) for j, (ci, U) in enumerate(Wl['early_cleanup'])]
def apply_(gt, vec):
    x = gt[1]
    if gt[0] == 'add':
        s = gt[2]; c = coef(gt); dst = vec[x]
        for k, v in vec[s].items():
            yv = dst.get(k, 0) + c * v
            if yv: dst[k] = yv
            else: dst.pop(k, None)
    else:
        c = coef(gt); vec[x] = {k: c * v for k, v in vec[x].items()}
def back_(gt, Tc):
    x = gt[1]
    if gt[0] == 'add':
        s = gt[2]; c = coef(gt)
        if Tc[x]:
            dst = Tc[s]
            for k, v in Tc[x].items():
                yv = dst.get(k, 0) + c * v
                if yv: dst[k] = yv
                else: dst.pop(k, None)
    else:
        c = coef(gt); Tc[x] = {k: c * v for k, v in Tc[x].items()}
# forward: collect candidates (t, a, b, delta_q)
start = [[p] for p in Wl['ports']] + [[] for _ in range(V + R)]
for k, U in Wl['start_extra'].items(): start[int(k)] = list(U)
fr = [F.span(tuple(s)) for s in start]; val = [{x: Fr(1)} for x in range(n)]
def ckey(x): return tuple(sorted((k, v) for k, v in val[x].items() if k < 2 * V))
cands = []; frames_at = {}
for t, (sec, i, gt) in enumerate(main):
    apply_(gt, val); x = gt[1]
    if gt[-1] is not None: fr[x] = F.span(tuple(gt[-1]))
    if t % stride: continue
    groups = collections.defaultdict(list)
    for z in range(n):
        if z not in targets: groups[ckey(z)].append(z)
    for key, mem in groups.items():
        if len(mem) < 2: continue
        for a in mem:
            for b in mem:
                if a == b or a == q or not (fr[b] <= fr[a]): continue
                if not (val[a].get(q, 0) - val[b].get(q, 0)): continue
                bad = False; dq = None
                for k in set(val[a]) | set(val[b]):
                    if k < 2 * V: continue
                    d = val[a].get(k, 0) - val[b].get(k, 0)
                    if not d: continue
                    if k == q: dq = d
                    elif k in E or k in K: bad = True; break
                if not bad and dq: cands.append((t, a, b, dq))
    frames_at[t] = None
print('narrowed', q, basis, r['cost'], r['certified'], 'candidates', len(cands), flush=True)
need = collections.defaultdict(set)
for (t, a, b, dq) in cands: need[t + 1].add(a)
def adjoint(seq, rowset):
    Tc = [dict() for _ in range(n)]
    for rr in rowset: Tc[rr] = {rr: Fr(1)}
    snap = {}
    for t in range(len(seq) - 1, -1, -1):
        if t + 1 in need: snap[t + 1] = {a: dict(Tc[a]) for a in need[t + 1]}
        back_(seq[t][2], Tc)
    return snap, Tc
snapT, _ = adjoint(main, targets)
snapK, _ = adjoint(main + tail, K)
endT = lambda a: ({a: Fr(1)} if a in targets else {}); endK = lambda a: ({a: Fr(1)} if a in K else {})
vecs, ops, stat = [], [], collections.Counter()
seen = set()
for (t, a, b, dq) in cands:
    uK = snapK.get(t + 1, {}).get(a, endK(a)) if (t + 1) in snapK else endK(a)
    if uK: stat['reaches-ended'] += 1; continue
    uT = snapT.get(t + 1, {}).get(a, endT(a)) if (t + 1) in snapT else endT(a)
    if not uT: stat['no-target'] += 1; continue
    key = (tuple(sorted((k, v * dq) for k, v in uT.items())))
    if key in seen: stat['dup'] += 1; continue
    seen.add(key); stat['admissible'] += 1
    vecs.append({k: v * dq for k, v in uT.items()}); ops.append((t, list(main[t][:2]), a, b, str(dq)))
# exact current leak of q (A+cut+B target rows)
val2 = [{x: Fr(1)} for x in range(n)]
for (sec, i, gt) in main: apply_(gt, val2)
L = {y: val2[y][q] for y in targets if val2[y].get(q, 0)}
# sparse solve L = sum mu_i vecs_i  (greedy pivoting, exact)
piv = {}
def red(v, track):
    v = dict(v); comb = dict(track)
    while v:
        k = min(v)
        if k not in piv: return v, comb
        pv, pc = piv[k]; f = v[k] / pv[k]
        for kk, xx in pv.items():
            yv = v.get(kk, 0) - f * xx
            if yv: v[kk] = yv
            else: v.pop(kk, None)
        for kk, xx in pc.items():
            yv = comb.get(kk, 0) - f * xx
            if yv: comb[kk] = yv
            else: comb.pop(kk, None)
    return v, comb
# prefer vectors with support inside supp(L) first (sparser solutions)
order = sorted(range(len(vecs)), key=lambda i: (not set(vecs[i]) <= set(L), len(vecs[i])))
for i in order:
    rv, comb = red(vecs[i], {i: Fr(1)})
    if rv: piv[min(rv)] = (rv, comb)
rest, comb = red(L, {})
ok = not rest
sol = {i: -c for i, c in comb.items()} if ok else {}
dyadic = all((c.denominator & (c.denominator - 1)) == 0 for c in sol.values())
res = dict(q=q, basis=basis, narrowed_cost=r['cost'], certified=r['certified'], leak=len(L), candidates=len(cands),
           stats=dict(stat), rank=len(piv), in_span=ok, nops=len(sol), dyadic=dyadic,
           solution=[dict(op=ops[i], mu=str(c)) for i, c in sorted(sol.items(), key=lambda kv: ops[kv[0]][0])])
json.dump(res, open(out_p, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'solution'}), flush=True)
for s_ in res['solution'][:16]: print('  ', s_)
