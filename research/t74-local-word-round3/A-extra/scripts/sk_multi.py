"""Multi-deletion split-key compensation (extends #2142 skkernel.py to several deleted reads with distinct source keys).
Key family: the deleted reads' source values plus, for each deleted read, every value held by its source or target over
the whole deleted word and every value added into them (one level, as skkernel).  Equations per basis element b:
sum_j lam_j coord_{key_j}[b] col_j = sum_k coord_{v_k}[b] d_k, where d_k accumulates the deleted contributions of key k.
Model, oracle, caps, budget, no-interaction rule and exact re-pricing are skkernel's (via sk2.solve).
usage: sk_multi.py WORD JOBS.json OUTDIR [--tl 300] [--K 3] [--workers 1]"""
import argparse, json, os, sys, time
from fractions import Fraction as Q
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2
from sk2 import H, F, inline, write_back, Orc, norm, coef, compile_AB, fullseq, amap, V, rowspace_basis
def build_multi(P, dels, store_factor=1.0):
    w = P.base; NA, NC, NB = len(w['A']), len(w['cut']), len(w['B'])
    seq = fullseq(w); L = len(seq); nreg = max(2 * V + w['report']['R'], 1 + max(max(g[1], g[2] if g[0] == 'add' else 0) for g in seq))
    gidx = lambda s, i: i if s == 'A' else (NA + NC + i if s == 'B' else NA + NC + NB + i)
    dg = {gidx(s, i) for s, i in dels}
    rows = {}; get = lambda x: rows.get(x, {x: Q(1)}); srcval = {}; hist = defaultdict(list); addin = defaultdict(list)
    cur_key = {x: norm({x: Q(1)}) for x in range(nreg)}; cur_start = {x: 0 for x in range(nreg)}; wins = defaultdict(list)
    for x in range(nreg): hist[x].append((0, {x: Q(1)}))
    for i, g in enumerate(seq):
        if i in dg: srcval[i] = dict(get(g[2])); continue
        t = g[1]
        if g[0] == 'add':
            addin[t].append(dict(get(g[2]))); a = dict(get(t)); c = coef(g)
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
    fam = []; alpha = {}; dkey = {}
    for gi in sorted(dg):
        k, al = norm(srcval[gi]); alpha[gi] = al
        if k not in fam: fam.append(k)
        dkey[gi] = fam.index(k)
    for gi in sorted(dg):
        g0 = seq[gi]
        for r_ in (g0[2], g0[1]):
            for val in [val for _, val in hist[r_]] + addin[r_]:
                k, _ = norm(val)
                if k is not None and k not in fam: fam.append(k)
    piv, coords = rowspace_basis([dict(k) for k in fam]); kco = [coords(dict(k)) for k in fam]
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
    bud = -ddel - 1; store_cap = store_factor * sk2.CANDCAP * bud
    colsF, colsB = {}, {}; SF = lambda x: colsF.get(x, {x: Q(1)}); SB = lambda x: colsB.get(x, {x: Q(1)})
    dk = defaultdict(dict); dkB = defaultdict(dict); order = []; seen = {}
    def step(cols, Sf, g):
        if g[0] == 'add':
            t, s = g[1], g[2]; c = coef(g); a = dict(Sf(s))
            for k, vv in Sf(t).items():
                a[k] = a.get(k, 0) + c * vv
                if not a[k]: del a[k]
            cols[s] = a
        else:
            x = g[1]; cols[x] = {k: vv * coef(g) for k, vv in Sf(x).items()}
    for i in range(L, -1, -1):
        g = seq[i] if i < L else None; inAB = i < NA + NC + NB
        if g is None: pass
        elif i in dg:
            t = g[1]; c = coef(g) * alpha[i]; kk = dkey[i]
            for k, vv in SF(t).items(): dk[kk][k] = dk[kk].get(k, 0) + c * vv
            if inAB:
                for k, vv in SB(t).items():
                    if V <= k < 2 * V: dkB[kk][k] = dkB[kk].get(k, 0) + c * vv
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
                    kk2 = (x, y, ki, tuple(sorted(vf.items())), tuple(sorted(vb.items())))
                    if kk2 in seen and seen[kk2] <= cst: continue
                    seen[kk2] = cst; order.append((x, y, i, al, dict(vf), dict(vb), cst, ki))
    rhs = defaultdict(Q)
    for kk in set(dk) | set(dkB):
        for b, cb in kco[kk].items():
            if not cb: continue
            for rr, val in dk[kk].items():
                if val: rhs[(b, 'F', rr)] += cb * val
            for rr, val in dkB[kk].items():
                if val: rhs[(b, 'B', rr)] += cb * val
    rhs = {k: v for k, v in rhs.items() if v}
    return dict(ddel=ddel, bud=bud, fam=fam, kco=kco, vco=None, d={}, dBt={}, rhs=rhs, order=order, NA=NA, NC=NC, NB=NB, dels=dels)
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('jobs'); ap.add_argument('outdir')
    ap.add_argument('--tl', type=float, default=300); ap.add_argument('--K', type=int, default=3); ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--maxterms', type=int, default=12); a = ap.parse_args()
    P = H.Pricer(a.word); base_full = amap(fullseq(P.base)); os.makedirs(a.outdir, exist_ok=True)
    for job in json.load(open(a.jobs)):
        dels = [tuple(x) for x in job['dels']]; name = job['name']; t0 = time.time()
        m = build_multi(P, dels); tb = time.time() - t0
        print('BUILT', name, 'ddel', m['ddel'], 'keys', len(m['fam']), 'stored', len(m['order']), 'rhs', len(m['rhs']), f'{tb:.0f}s', flush=True)
        r = sk2.solve(P, m, a.maxterms, a.K, a.tl, workers=a.workers, base_full=base_full)
        r.update(name=name, dels=job['dels'], keys=len(m['fam']), build_sec=round(tb, 1), sec=round(time.time() - t0, 1))
        json.dump(r, open(os.path.join(a.outdir, 'skm-%s.json' % name), 'w'), separators=(',', ':'))
        best = min([x['delta'] for x in r['res'] if x.get('delta') is not None], default=None)
        print('SUMMARY', name, 'ddel', r['ddel'], 'keys', r['keys'], 'cand', r['ncand'], 'shape', r['shape'], 'cp', r['cp_status'], 'nsol', len(r['res']), 'best', best, f"{r['sec']}s", flush=True)
