"""sk2: #2142's split-key compensation search (tools/skkernel.py, Ian Libanio; builds on #1957 abkernel.py, Rohan Arun),
refactored into build() and solve() so that the CP-SAT model of one deletion can be compared across two words.
build() is skkernel.run up to the model (same keys, holders, oracle, candidate filter, equations, budget).
The comparison argument: gates are identical in both words, so values, columns, holders, positions and equations are
identical; only oracle costs and the deletion price (budget) can differ.  If every extra-word candidate cost is >= the
base cost for the same candidate key, every extra candidate exists on base, and the extra budget is <= the base budget,
the extra model is a restriction of the base model, so a base infeasibility proof applies.
usage: sk2.py compare|solve ... (see main)"""
import os, sys, json, time, math
from fractions import Fraction as Q
from collections import defaultdict
WORK = os.environ['SK_WORK']   # copy of research/ with t74-k554-local-exhaustion and t74-split-key-kernel-search
sys.path.insert(0, os.path.join(WORK, 't74-k554-local-exhaustion', 'tools'))
import _paths  # noqa: F401  (vendored #1186 toolkit of #1957 on sys.path; IMB_ROOT from env)
import harness as H, frames as F
from word import inline
from writeback import write_back
from akernel import Orc, amap, norm, coef
from abkernel import compile_AB, fullseq, price
from ortools.sat.python import cp_model
V = 112
CANDCAP = float(os.environ.get('SK_CANDCAP', '1'))

def rowspace_basis(vecs):
    piv = []
    def reduce(v):
        v = dict(v); co = {}
        for bi, (pk, pv) in enumerate(piv):
            if v.get(pk):
                f = v[pk] / pv[pk]; co[bi] = co.get(bi, 0) + f
                for k, x in pv.items():
                    v[k] = v.get(k, 0) - f * x
                    if not v[k]: del v[k]
        return v, co
    for v in vecs:
        r, _ = reduce(v)
        if r: piv.append((min(r), r))
    def coords(v):
        r, co = reduce(v); assert not r, 'not in span'
        return co
    return piv, coords

def build(P, dels, store_factor=1.5):
    w = P.base; NA, NC, NB = len(w['A']), len(w['cut']), len(w['B'])
    seq = fullseq(w); L = len(seq); nreg = 2 * V + w['report']['R']
    nreg = max(nreg, 1 + max(max(g[1], g[2] if g[0] == 'add' else 0) for g in seq))
    gidx = lambda s, i: i if s == 'A' else (NA + NC + i if s == 'B' else NA + NC + NB + i)
    dg = {gidx(s, i) for s, i in dels}
    rows = {}; get = lambda x: rows.get(x, {x: Q(1)}); srcval = {}
    hist = defaultdict(list); addin = defaultdict(list)
    cur_key = {x: norm({x: Q(1)}) for x in range(nreg)}; cur_start = {x: 0 for x in range(nreg)}; wins = defaultdict(list)
    for x in range(nreg): hist[x].append((0, {x: Q(1)}))
    for i, g in enumerate(seq):
        if i in dg:
            srcval[i] = dict(get(g[2])); continue
        t = g[1]
        if g[0] == 'add':
            addin[t].append(dict(get(g[2])))
            a = dict(get(t)); c = coef(g)
            for k, v in get(g[2]).items():
                a[k] = a.get(k, 0) + c * v
                if not a[k]: del a[k]
        else: a = {k: v * coef(g) for k, v in get(t).items()}
        rows[t] = a; nk = norm(a); hist[t].append((i + 1, dict(a)))
        if nk != cur_key[t]:
            key, al = cur_key[t]
            if key is not None: wins[key].append((t, cur_start[t], i + 1, al))
            cur_key[t] = nk; cur_start[t] = i + 1
    for x in range(nreg):
        key, al = cur_key[x]
        if key is not None: wins[key].append((x, cur_start[x], L + 1, al))
    (i0,) = dg; g0 = seq[i0]; s0 = g0[2]; t0 = g0[1]
    v = srcval[i0]; vkey, alpha0 = norm(v)
    fam = [vkey]
    for r in (s0, t0):
        for val in [val for _, val in hist[r]] + addin[r]:
            k, _ = norm(val)
            if k is not None and k not in fam: fam.append(k)
    kv = [dict(k) for k in fam]; piv, coords = rowspace_basis(kv); kco = [coords(dict(k)) for k in fam]; vco = kco[0]
    holders = defaultdict(list)
    for ki, k in enumerate(fam):
        for y, a_, b_, al in wins[k]:
            for p in range(a_, min(b_, L + 1)): holders[p].append((y, al, ki))
    w1 = compile_AB(w, dict(delete=dels))
    gr = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
    r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=gr); ddel = r['cost'] - P.base_cost
    w2 = write_back(w1, gr, r['assign']); orc = Orc(w2, P.costs.c)
    dA = sorted(i for s, i in dels if s == 'A'); dB = sorted(i for s, i in dels if s == 'B')
    def orcpos(gi):
        if gi < NA: return gi - sum(1 for t in dA if t < gi)
        if gi < NA + NC: return None
        if gi < NA + NC + NB: return (NA - len(dA)) + (gi - NA - NC) - sum(1 for t in dB if t < gi - NA - NC)
        return (NA - len(dA)) + (NB - len(dB)) + (gi - NA - NC - NB)
    bud = -ddel - 1; store_cap = store_factor * CANDCAP * bud
    colsF, colsB = {}, {}; SF = lambda x: colsF.get(x, {x: Q(1)}); SB = lambda x: colsB.get(x, {x: Q(1)})
    d, dBt = {}, {}   # key (x, y, ki, vf, vb) -> (min cost over positions, first position at that cost, al, vf, vb): ALL candidates, no cap
    def step(cols, Sf, g):
        if g[0] == 'add':
            t, s = g[1], g[2]; c = coef(g); a = dict(Sf(s))
            for k, vv in Sf(t).items():
                a[k] = a.get(k, 0) + c * vv
                if not a[k]: del a[k]
            cols[s] = a
        else:
            x = g[1]; cols[x] = {k: vv * coef(g) for k, vv in Sf(x).items()}
    order = []
    for i in range(L, -1, -1):
        g = seq[i] if i < L else None
        inAB = i < NA + NC + NB
        if g is None: pass
        elif i in dg:
            t = g[1]; c = coef(g) * alpha0
            for k, vv in SF(t).items(): d[k] = d.get(k, 0) + c * vv
            if inAB:
                for k, vv in SB(t).items():
                    if V <= k < 2 * V: dBt[k] = dBt.get(k, 0) + c * vv
        else:
            step(colsF, SF, g)
            if inAB: step(colsB, SB, g)
        if i in holders:
            op = orcpos(i)
            if op is None: continue
            for y, al, ki in holders[i]:
                for x in range(nreg):
                    if x == y or (V <= y < 2 * V and not (V <= x < 2 * V)): continue
                    cst = orc.cost(x, y, op)
                    if cst > store_cap: continue
                    vf = SF(x); vb = {k: vv for k, vv in SB(x).items() if V <= k < 2 * V} if inAB else {}
                    order.append((x, y, i, al, dict(vf), dict(vb), cst, ki))
    d = {k: vv for k, vv in d.items() if vv}; dBt = {k: vv for k, vv in dBt.items() if vv}
    return dict(ddel=ddel, bud=bud, fam=fam, kco=kco, vco=vco, d=d, dBt=dBt, order=order, NA=NA, NC=NC, NB=NB, dels=dels)

def candidates(m, cap):
    """skkernel's filtered, deduplicated candidate list (cost <= cap; per key keep the first strictly cheaper)."""
    seen = {}; cand = []
    for (x, y, i, al, vf, vb, cst, ki) in m['order']:
        if cst > cap: continue
        kk = (x, y, ki, tuple(sorted(vf.items())), tuple(sorted(vb.items())))
        if kk in seen and seen[kk][0] <= cst: continue
        seen[kk] = (cst, len(cand)); cand.append((x, y, i, al, {k: vv * al for k, vv in vf.items()}, {k: vv * al for k, vv in vb.items()}, cst, ki))
    return cand

def signature(m):
    """per (x, y, ki, position, vf, vb): oracle cost.  Gates are identical across words, so these keys coincide."""
    return {(x, y, i, ki, tuple(sorted(vf.items())), tuple(sorted(vb.items()))): cst for (x, y, i, al, vf, vb, cst, ki) in m['order']}

def solve(P, m, maxterms, K, tl, lamr=8, workers=3, base_full=None, nobud=False):
    cap = CANDCAP * m['bud']; cand = candidates(m, cap); kco, vco, d, dBt = m['kco'], m['vco'], m['d'], m['dBt']
    NA, NC, NB = m['NA'], m['NC'], m['NB']; dels = m['dels']
    eqs = defaultdict(list)
    for j, c_ in enumerate(cand):
        co = kco[c_[7]]
        for b, cb in co.items():
            if not cb: continue
            for rr, val in c_[4].items(): eqs[(b, 'F', rr)].append((j, cb * val))
            for rr, val in c_[5].items(): eqs[(b, 'B', rr)].append((j, cb * val))
    if m.get('rhs') is not None: rhs = dict(m['rhs'])
    else:
        rhs = {}
        for b, cb in vco.items():
            for rr, val in d.items(): rhs[(b, 'F', rr)] = cb * val
            for rr, val in dBt.items(): rhs[(b, 'B', rr)] = cb * val
    allkeys = set(eqs) | set(rhs); shape = all(k in eqs for k, val in rhs.items() if val)
    lcm = 1
    for k in allkeys:
        for _, val in eqs.get(k, []): lcm = lcm * Q(val).denominator // math.gcd(lcm, Q(val).denominator)
        q = Q(rhs.get(k, 0)).denominator; lcm = lcm * q // math.gcd(lcm, q)
    SC = 2 * lcm
    mm = cp_model.CpModel(); lam = []; z = []
    for j in range(len(cand)):
        l = mm.NewIntVar(-lamr, lamr, ''); b = mm.NewBoolVar(''); mm.Add(l == 0).OnlyEnforceIf(b.Not()); mm.Add(l != 0).OnlyEnforceIf(b); lam.append(l); z.append(b)
    for k in allkeys:
        terms = [lam[j] * int(Q(val) * SC) for j, val in eqs.get(k, [])]
        r_ = Q(rhs.get(k, 0)) * 2 * SC; assert r_.denominator == 1
        if not terms: continue
        mm.Add(sum(terms) == int(r_))
    byx = defaultdict(list)
    for j, c_ in enumerate(cand): byx[c_[0]].append(j)
    for j2, c2 in enumerate(cand):
        ws = [z[j1] for j1 in byx.get(c2[1], []) if cand[j1][2] <= c2[2]]
        if ws: mm.Add(sum(ws) == 0).OnlyEnforceIf(z[j2])
    mm.Add(sum(z) <= maxterms)
    if not nobud: mm.Add(sum(z[j] * cand[j][6] for j in range(len(cand))) <= m['bud'])
    mm.Minimize(sum(z[j] * (cand[j][6] + 50) for j in range(len(cand))))
    res = []; status = 'SHAPE_INFEASIBLE' if not shape else ('NO_DELETION_GAIN' if m['ddel'] >= 0 else 'NOT_RUN')
    if shape and m['ddel'] < 0 and cand:
        status = 'SOLUTION_LIMIT'; seq = fullseq(P.base); base_full = base_full or amap(seq)
        for it in range(K):
            s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_workers = workers
            st = s.Solve(mm)
            if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): status = s.StatusName(st); break
            supp = [j for j in range(len(cand)) if s.Value(z[j])]
            terms = [(cand[j][0], cand[j][1], cand[j][2], Q(s.Value(lam[j]), 2), cand[j][7]) for j in supp]; est = sum(cand[j][6] for j in supp)
            mm.Add(sum(z[j] for j in supp) <= len(supp) - 1)
            ed = dict(delete=list(dels), insert=[], tail=[])
            for x, y, gi, l, ki in terms:
                gate = ['add', x, y, l.numerator, l.denominator, []]
                if gi <= NA: ed['insert'].append(('A', gi, gate)) if gi < NA else ed['insert'].append(('B', 0, gate))
                elif gi < NA + NC + NB: ed['insert'].append(('B', gi - NA - NC, gate))
                else: ed['tail'].append((gi - NA - NC - NB, gate))
            rr = price(P, ed, base_full)
            res.append(dict(terms=[(x, y, gi, str(l), ki) for x, y, gi, l, ki in terms], est=est, status=rr.get('status'), delta=rr.get('delta'), profile=rr.get('profile'), ed=ed))
    return dict(ddel=m['ddel'], bud=m['bud'], shape=shape, ncand=len(cand), cp_status=status, res=res)
