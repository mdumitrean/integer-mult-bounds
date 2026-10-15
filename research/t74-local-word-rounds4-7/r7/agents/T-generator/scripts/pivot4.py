"""pivot4.py (4-gate variant: r += c; r -= s; c -= r; c += r2, r2 = clean twin of r): search the 3-gate pivot construction that moves narrowable helper q's dirt off its carrier c into a
target-idle pivot r:  r += c ; r -= s ; c -= r   (s = clean twin of c: same clean part, no q dirt).
After it: r = r0 + (c - s) (pure dirt, carries q's dirt), c = s - r0 (clean twin minus r0).  Conditions at time t
(narrowed word's literal frames):  frame(r) == frame(c) >= frame(s);  clean(r) == 0;  r0 has no entering/ended dirt;
T_target(t)[:, r] == 0 (r's later value reaches no target);  T_ended(t)[:, r] == T_ended(t)[:, c] == 0;  and
q's whole leak flows through c at t:  T_target(t)[:, c] * (dirt_c[q] - dirt_s[q]) == L_q.  Then q's column is zero.
usage: pivot3.py WORD NARROW.jsonl TOOLKIT Q OUT.json"""
import json, gzip, sys, collections, copy
from fractions import Fraction as Fr
word_p, narrow_p, tk, qarg, out_p = sys.argv[1:6]
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
def fwd(gt, vec):
    x = gt[1]
    if gt[0] == 'add':
        s = gt[2]; c = coef(gt); dst = vec[x]
        for k, v in vec[s].items():
            yv = dst.get(k, 0) + c * v
            if yv: dst[k] = yv
            else: dst.pop(k, None)
    else:
        c = coef(gt); vec[x] = {k: c * v for k, v in vec[x].items()}
def bwd(gt, Tc):
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
# full leak
v2 = [{x: Fr(1)} for x in range(n)]
for (_, _, gt) in main: fwd(gt, v2)
L = {y: v2[y][q] for y in targets if v2[y].get(q, 0)}
# backward adjoints, keeping full snapshots only at A-section times where some register carries q's dirt
# first a forward pass to find times/carriers
start = [[p] for p in Wl['ports']] + [[] for _ in range(V + R)]
for k, U in Wl['start_extra'].items(): start[int(k)] = list(U)
fr = [F.span(tuple(s)) for s in start]; val = [{x: Fr(1)} for x in range(n)]
def ckey(x): return tuple(sorted((k, v) for k, v in val[x].items() if k < 2 * V))
D = collections.Counter(); probe = {}   # t -> (carriers info, frames snapshot, values snapshot of relevant regs)
for t, (sec, i, gt) in enumerate(main):
    fwd(gt, val); x = gt[1]
    if gt[-1] is not None: fr[x] = F.span(tuple(gt[-1]))
    car = [z for z in range(n) if z not in targets and val[z].get(q, 0)]
    if not car: continue
    ck = {z: ckey(z) for z in range(n) if z not in targets}
    twins = {}
    for c in car:
        tw = [s for s in ck if s != c and ck[s] == ck[c] and not val[s].get(q, 0) and fr[s] <= fr[c]]
        if tw: twins[c] = tw[:6]
    D['times_with_carriers'] += 1
    if not twins: continue
    D['times_with_twins'] += 1
    for c in twins:
        D['pivot_candidates_same_frame'] += sum(1 for z in range(n) if z not in targets and z != c and fr[z] == fr[c])
        D['pivot_candidates_same_frame_clean0'] += sum(1 for z in range(n) if z not in targets and z != c and fr[z] == fr[c] and not any(k < 2 * V for k in val[z]))
    pivots = {}
    for c in twins:
        pv = []
        for z in range(n):
            if z in targets or z in E or z in K or z == c or fr[z] != fr[c]: continue
            tw2 = [z2 for z2 in ck if z2 not in (z, c) and ck[z2] == ck[z] and fr[z2] <= fr[c] and z2 not in E and z2 not in K]
            for z2 in tw2:
                dd = {k: val[z].get(k, 0) - val[z2].get(k, 0) for k in set(val[z]) | set(val[z2]) if k >= 2 * V}
                if any(v and (k in E or k in K) for k, v in dd.items()) or dd.get(q): continue
                pv.append((z, z2)); break
        if pv: pivots[c] = pv
    if pivots:
        probe[t] = dict(twins={c: twins[c] for c in pivots}, pivots=pivots,
                        dq={c: {s: val[c].get(q, 0) - val[s].get(q, 0) for s in twins[c]} for c in pivots})
print('narrowed', q, basis, r['cost'], 'leak', len(L), 'probe times', len(probe), dict(D), flush=True)
need = collections.defaultdict(set)
for t, pr in probe.items():
    for c, pv in pr['pivots'].items(): need[t + 1].update([c] + [z for z, z2 in pv])
def adjoint(seq, rowset):
    Tc = [dict() for _ in range(n)]
    for rr in rowset: Tc[rr] = {rr: Fr(1)}
    snap = {}
    for t in range(len(seq) - 1, -1, -1):
        if t + 1 in need: snap[t + 1] = {a: dict(Tc[a]) for a in need[t + 1]}
        bwd(seq[t][2], Tc)
    return snap
sT = adjoint(main, targets); sK = adjoint(main + tail, K)
hits = []; stat = collections.Counter()
for t, pr in sorted(probe.items()):
    for c, pv in pr['pivots'].items():
        Tc_c = sT.get(t + 1, {}).get(c, {}); TK_c = sK.get(t + 1, {}).get(c, {})
        if TK_c: stat['c-reaches-ended'] += 1; continue
        for s, dq in pr['dq'][c].items():
            if not dq: continue
            w = {y: v * dq for y, v in Tc_c.items()}
            need_r = {y: w.get(y, 0) - L.get(y, 0) for y in set(w) | set(L)}
            need_r = {y: v for y, v in need_r.items() if v}       # pivot route must equal (T_c*dq - L)/dq
            good = []
            for (z, z2) in pv:
                if sK.get(t + 1, {}).get(z): continue
                Tr = {y: v * dq for y, v in sT.get(t + 1, {}).get(z, {}).items()}
                if Tr == need_r: good.append((z, z2))
            if not good: stat['no-matching-pivot'] += 1; continue
            stat['hit'] += 1
            hits.append(dict(t=t, at=list(main[t][:2]), c=c, s=s, dq=str(dq), pivots=good[:10]))
res = dict(q=q, basis=basis, narrowed_cost=r['cost'], leak=len(L), probe_times=len(probe), stats=dict(stat), hits=hits[:100], nhits=len(hits))
json.dump(res, open(out_p, 'w'), indent=1)
print(json.dumps({k: v for k, v in res.items() if k != 'hits'}), flush=True)
for h in hits[:8]: print('  HIT', h)
