"""gen2.py: vectorised (NumPy) candidate generator for r3 B-interact's sk2.Round (agent D-depth2, r6).

Same model and semantics as sk2.Round.candidates (with the optional cone-aware admission test cone.LU.ok), but the
per-(x, y, position) work is replaced by per-position tables over all registers:
  FX[p, r]  interned oracle frame pair (Fr, Nr) = Orc.info(r, orcpos(p))      (piecewise constant between r's gates)
  NB[p, r]  interned chain-neighbour pair LU.nb(r, p)                          (cone test)
  CF[p, r]  interned final-row column of r at insertion point p                (sk2 backward sweep)
  CB[p, r]  interned port-row (V..2V-1) part of r's A.cut.B column, () for p >= NA+NC+NB
Costs (Orc.cost) and cone verdicts (LU.ok) are memoised on the interned arguments; the dedup keeps, per key
(x, coords, vf, vb), the entry minimising (cost, -p, holder order), and orders keys by first encounter (-p, holder order, x)
exactly as sk2's backward loop does.  Holder windows, basis and coordinates are sk2's own (exact rationals).
Builds on r3 B-interact's sk2.py/cone.py, PR2142 (Ian Libanio) skkernel.py and PR1957 (Rohan Arun) tools."""
import bisect, os, sys, time
from fractions import Fraction as Q
import numpy as np
TOOLS = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'r3', 'agents', 'B-interact', 'tools'))
sys.path.insert(0, TOOLS)
import sk2
from sk2 import V, Round, hist_values, coef
import akernel

def _intern(table, key):
    i = table.get(key)
    if i is None: i = table[key] = len(table)
    return i

def cost_frames(orc, Fx, Nx, Fy, Ny):
    U = akernel.span(tuple(Fx | Fy)); best = akernel.INF
    for T in {Fx, Fy, Nx, Ny, U}:
        if Fx <= T and Fy <= T: best = min(best, orc.zc(Fx, Nx, T) + orc.zc(Fy, Ny, T))
    return best

def ok_nodes(lu, a, b, c, d, pA, capx, capy):
    g = lu.g; L = tuple(g.lower[a]) + tuple(g.lower[c])
    if pA:
        for nbk in (b, d):
            if g.nodes[nbk][2] == 'cut': L = L + tuple(g.nodes[nbk][1])
    U = lu.S(g.upper[b]) & lu.S(g.upper[d])
    if capx >= 0: U = U & lu.S(g.caps[capx])
    if capy >= 0: U = U & lu.S(g.caps[capy])
    return sk2.F.span(sk2.F.basis(L)) <= U

class Tables:
    def __init__(self, R):
        seq, L, nreg = R.seq, R.L, R.nreg; NA, NC, NB = R.NA, R.NC, R.NB; NAB = NA + NC + NB; orc = R.orc
        self.L, self.nreg, self.NA, self.NC, self.NAB = L, nreg, NA, NC, NAB
        ops = np.full(L + 1, -1, np.int64)
        for p in range(L + 1):
            o = R.orcpos(p); ops[p] = -1 if o is None else o
        self.ops = ops
        # oracle frame pairs
        self.fp = {}; self.fpl = []
        def fid(r, op):
            Fr, N = orc.info(r, op); k = (Fr, N); i = self.fp.get(k)
            if i is None: i = self.fp[k] = len(self.fpl); self.fpl.append(k)
            return i
        part = {}
        for r, ps in orc.pos.items():
            for j in ps: part.setdefault(j, set()).add(r)
        FX = np.full((L + 1, nreg), -1, np.int32); row = None; prev_op = None
        for p in range(L + 1):
            op = int(ops[p])
            if op < 0: continue
            if row is None: row = np.array([fid(r, op) for r in range(nreg)], np.int32)
            else:
                for j in range(prev_op, op):
                    for r in part.get(j, ()):
                        if r < nreg: row[r] = fid(r, op)
            FX[p] = row; prev_op = op
        self.FX = FX
        # chain neighbours (cone test)
        self.lu = lu = getattr(R, 'lu', None)
        if lu is not None:
            g = lu.g; self.NN = NN = len(g.nodes)
            self.is_te = np.array([g.nodes[k][2] in ('tail', 'end') for k in range(NN)], bool)
            self.has_cap = np.array([r in g.caps for r in range(nreg)], bool)
            at = {}
            for r in range(nreg):
                for q in lu.cpos[r]: at.setdefault(q, []).append(r)
            NBt = np.empty((L + 1, nreg), np.int64)
            rowb = np.array([(lambda ab: ab[0] * NN + ab[1])(lu.nb(r, 0)) for r in range(nreg)], np.int64)
            NBt[0] = rowb
            for p in range(1, L + 1):
                for r in at.get(p - 1, ()):
                    a, b = lu.nb(r, p); rowb[r] = a * NN + b
                NBt[p] = rowb
            self.NB = NBt
        # columns (sk2 backward sweep), interned
        self.cf = {}; self.cfl = []; self.cb = {}; self.cbl = []
        def cfid(t):
            i = self.cf.get(t)
            if i is None: i = self.cf[t] = len(self.cfl); self.cfl.append(t)
            return i
        def cbid(t):
            i = self.cb.get(t)
            if i is None: i = self.cb[t] = len(self.cbl); self.cbl.append(t)
            return i
        colsF, colsB = {}, {}; SF = lambda x: colsF.get(x, {x: Q(1)}); SB = lambda x: colsB.get(x, {x: Q(1)})
        def step(cols, Sf, gt):
            if gt[0] == 'add':
                t, s = gt[1], gt[2]; c = coef(gt); a = dict(Sf(s))
                for k, vv in Sf(t).items():
                    a[k] = a.get(k, 0) + c * vv
                    if not a[k]: del a[k]
                cols[s] = a; return s
            x = gt[1]; cols[x] = {k: vv * coef(gt) for k, vv in Sf(x).items()}; return x
        portf = lambda d: tuple(sorted((k, v) for k, v in d.items() if V <= k < 2 * V))
        CF = np.empty((L + 1, nreg), np.int32); CB = np.empty((L + 1, nreg), np.int32)
        rowf = np.array([cfid(((r, Q(1)),)) for r in range(nreg)], np.int32)
        rowB = np.array([cbid(((r, Q(1)),) if V <= r < 2 * V else ()) for r in range(nreg)], np.int32)
        empty = cbid(())
        CF[L] = rowf; CB[L] = empty if L >= NAB else rowB
        for i in range(L - 1, -1, -1):
            gt = seq[i]; r = step(colsF, SF, gt)
            if r < nreg: rowf[r] = cfid(tuple(sorted(SF(r).items())))
            if i < NAB:
                r2 = step(colsB, SB, gt)
                if r2 < nreg: rowB[r2] = cbid(portf(SB(r2)))
            CF[i] = rowf; CB[i] = rowB if i < NAB else empty
        self.CF, self.CB = CF, CB

def candidates_fast(R, verbose=False):
    t0 = time.time(); T = Tables(R); seq, L, nreg = R.seq, R.L, R.nreg; NA, NC, NAB = T.NA, T.NC, T.NAB
    if verbose: print('  tables', round(time.time() - t0, 1), 's: frame pairs', len(T.fpl), 'cols', len(T.cfl), len(T.cbl), flush=True)
    win = hist_values(seq, nreg); yorder = {y: k for k, y in enumerate(win.keys())}
    cap = None if R.bud is None else R.cap_mult * R.bud
    cmemo = {}; okmemo = {}; coi = {}; col = []
    best = {}   # key -> [cost, p, yr, y, pfirst, yrfirst]
    xs = np.arange(nreg); cone_rej = 0; lu = T.lu
    for y, ws in win.items():
        yr = yorder[y]
        for a, b, val in ws:
            if not val: continue
            co = R.basis.coords(val)
            if not co: continue
            ct = tuple(sorted(co.items())); ci = coi.get(ct)
            if ci is None: ci = coi[ct] = len(col); col.append(co)
            ps = np.arange(a, min(b, L + 1)); ps = ps[T.ops[ps] >= 0]
            if not len(ps): continue
            FXb = T.FX[ps]; fy = FXb[:, y].astype(np.int64)
            pk = FXb.astype(np.int64) * len(T.fpl) + fy[:, None]
            u, inv = np.unique(pk, return_inverse=True); cu = np.empty(len(u), np.float64)
            for k, key in enumerate(u.tolist()):
                c_ = cmemo.get(key)
                if c_ is None:
                    fxk, fyk = divmod(key, len(T.fpl)); (Fx, Nx), (Fy, Ny) = T.fpl[fxk], T.fpl[fyk]
                    c_ = cmemo[key] = cost_frames(R.orc, Fx, Nx, Fy, Ny)
                cu[k] = c_
            cost = cu[inv.reshape(pk.shape)]
            m = np.ones(pk.shape, bool); m[:, y] = False
            if V <= y < 2 * V: m[:, :V] = False; m[:, 2 * V:] = False
            if cap is not None: m &= cost <= cap
            if not m.any(): continue
            pi, xi = np.nonzero(m)
            if lu is not None:
                nbx = T.NB[ps[pi], xi]; nby = T.NB[ps[pi], y]
                bx = nbx % T.NN; by = nby % T.NN
                capx = np.where(T.has_cap[xi] & T.is_te[bx], xi, -1); capy = np.where(T.has_cap[y] & T.is_te[by], y, -1)
                pA = (ps[pi] < NA).astype(np.int64)
                ck = np.stack([nbx, nby, pA, capx, capy], 1)
                uk, kinv = np.unique(ck, axis=0, return_inverse=True); okv = np.empty(len(uk), bool)
                for k, row in enumerate(uk.tolist()):
                    kk = tuple(row); o = okmemo.get(kk)
                    if o is None:
                        a_, b_ = divmod(row[0], T.NN); c_, d_ = divmod(row[1], T.NN)
                        o = okmemo[kk] = ok_nodes(lu, a_, b_, c_, d_, bool(row[2]), int(row[3]), int(row[4]))
                    okv[k] = o
                okm = okv[kinv.reshape(-1)]; cone_rej += int((~okm).sum()); pi, xi = pi[okm], xi[okm]
            if not len(pi): continue
            pp = ps[pi]; cc = cost[pi, xi]; cfv = T.CF[pp, xi]; cbv = T.CB[pp, xi]
            # within this window: per key, best = (min cost, max p); first = max p
            order = np.lexsort((-pp, cc, cbv, cfv, xi))
            xs_, cf_, cb_, cc_, pp_ = xi[order], cfv[order], cbv[order], cc[order], pp[order]
            newk = np.ones(len(order), bool); newk[1:] = (xs_[1:] != xs_[:-1]) | (cf_[1:] != cf_[:-1]) | (cb_[1:] != cb_[:-1])
            idx = np.nonzero(newk)[0]
            # max p per key (first encounter)
            grp = np.cumsum(newk) - 1; pmax = np.full(len(idx), -1, np.int64); np.maximum.at(pmax, grp, pp_)
            for j, k0 in enumerate(idx.tolist()):
                key = (int(xs_[k0]), ci, int(cf_[k0]), int(cb_[k0])); c0 = float(cc_[k0]); p0 = int(pp_[k0]); pf = int(pmax[j])
                e = best.get(key)
                if e is None: best[key] = [c0, p0, yr, y, pf, yr]
                else:
                    if (c0, -p0, yr) < (e[0], -e[1], e[2]): e[0], e[1], e[2], e[3] = c0, p0, yr, y
                    if (-pf, yr) < (-e[4], e[5]): e[4], e[5] = pf, yr
    keys = sorted(best, key=lambda k: (-best[k][4], best[k][5], k[0]))
    cand = []
    for k in keys:
        x, ci, cfi, cbi = k; c0, p0, yr, y, _, _ = best[k]
        vf = dict(T.cfl[cfi]); vb = dict(T.cbl[cbi])
        cst = int(c0) if c0 == int(c0) else c0
        cand.append((x, y, p0, col[ci], (vf, vb), cst))
    R.cand = cand; R.cone_rejected = cone_rej
    if verbose: print('  candidates', len(cand), 'cone-rejected entries', cone_rej, round(time.time() - t0, 1), 's', flush=True)
    return cand

class FastRound(Round):
    def candidates(self): return candidates_fast(self, verbose=bool(os.environ.get('GEN2_VERBOSE')))

# ---------------------------------------------------------------------------------------------------------------------
# Memory-lean model builder: same variables, equations (up to a common positive scale), budget, objective and bans as
# sk2.Round.model, built from interned integer arrays straight into the CP-SAT proto.
import math
from collections import defaultdict
from ortools.sat.python import cp_model

def _lcm(a, b): return a * b // math.gcd(a, b)

def model_lean(R, maxterms, lamr=8, ban='none', extra_cuts=(), lam_den=2):
    cand = R.cand; D = R.lam_den = lam_den; nb = len(R.basis.piv)
    rhs = {}
    for tag, T in (('F', R.TF), ('B', R.TB)):
        for rr, row in T.items():
            co = R.basis.coords(row); assert co is not None
            for b, cb in co.items(): rhs[(b, tag, rr)] = Q(cb)
    # intern columns and coordinate vectors of the candidates
    coid, colid, cols_list, cos_list = {}, {}, [], []
    cj = np.empty(len(cand), np.int64); fj = np.empty(len(cand), np.int64); bj = np.empty(len(cand), np.int64)
    for j, (x, y, i, co, (vf, vb), cst) in enumerate(cand):
        k = tuple(sorted(co.items())); c = coid.get(k)
        if c is None: c = coid[k] = len(cos_list); cos_list.append(k)
        kf = ('F',) + tuple(sorted(vf.items())); f = colid.get(kf)
        if f is None: f = colid[kf] = len(cols_list); cols_list.append(kf)
        kb = ('B',) + tuple(sorted(vb.items())); g = colid.get(kb)
        if g is None: g = colid[kb] = len(cols_list); cols_list.append(kb)
        cj[j], fj[j], bj[j] = c, f, g
    Dco = 1
    for k in cos_list:
        for _, v in k: Dco = _lcm(Dco, Q(v).denominator)
    for v in rhs.values(): Dco = _lcm(Dco, v.denominator)
    Dcol = 1
    for k in cols_list:
        for _, v in k[1:]: Dcol = _lcm(Dcol, Q(v).denominator)
    nreg = R.nreg
    def eqid(b, tag, rr): return (b * 2 + (0 if tag == 'F' else 1)) * nreg + rr
    co_b = [np.array([b for b, _ in k], np.int64) for k in cos_list]
    co_n = [np.array([int(Q(v) * Dco) for _, v in k], np.int64) for k in cos_list]
    col_r = [np.array([rr for rr, _ in k[1:]], np.int64) for k in cols_list]
    col_t = [0 if k[0] == 'F' else 1 for k in cols_list]
    col_n = [np.array([int(Q(v) * Dcol) for _, v in k[1:]], np.int64) for k in cols_list]
    Js, Es, Cs = [], [], []
    for j in range(len(cand)):
        c = cj[j]; bvec, nvec = co_b[c], co_n[c]
        for f in (fj[j], bj[j]):
            rr, nn = col_r[f], col_n[f]
            if not len(rr): continue
            e = ((bvec[:, None] * 2 + col_t[f]) * nreg + rr[None, :]).ravel()
            Cs.append((nvec[:, None] * nn[None, :]).ravel() * D); Es.append(e); Js.append(np.full(len(e), j, np.int64))
    E = np.concatenate(Es) if Es else np.empty(0, np.int64); C = np.concatenate(Cs) if Cs else np.empty(0, np.int64)
    J = np.concatenate(Js) if Js else np.empty(0, np.int64); del Es, Cs, Js
    order = np.argsort(E, kind='stable'); E, C, J = E[order], C[order], J[order]
    rhs_e = {eqid(b, t, rr): v for (b, t, rr), v in rhs.items()}
    R.presolve_removed = 0
    if os.environ.get('GEN2_PRESOLVE'):
        # sound singleton elimination: a row with exactly one live candidate and zero rhs forces that lambda to 0
        uE0, Ed = np.unique(E, return_inverse=True); rz = np.array([not rhs_e.get(int(e)) for e in uE0.tolist()], bool)
        Jd = J.astype(np.int32); live = np.ones(len(cand), bool)
        while True:
            lt = live[Jd]; cnt = np.bincount(Ed[lt], minlength=len(uE0))
            kill = np.unique(Jd[lt & (cnt[Ed] == 1) & rz[Ed]])
            if not len(kill): break
            live[kill] = False
        keep = live[Jd]; E, C, J = E[keep], C[keep], J[keep]; R.presolve_removed = int((~live).sum()); R.presolve_live = live
        del Ed, Jd, keep
    eq_present = set(np.unique(E).tolist())
    R.shape = all(e in eq_present for e, v in rhs_e.items() if v)
    R.n_terms = int(len(E))
    m = cp_model.CpModel(); lam, z = [], []
    for j in range(len(cand)):
        l = m.NewIntVar(-lamr, lamr, ''); bz = m.NewBoolVar('')
        m.Add(l == 0).OnlyEnforceIf(bz.Not()); m.Add(l != 0).OnlyEnforceIf(bz); lam.append(l); z.append(bz)
    lam_idx = np.array([l.Index() for l in lam], np.int64); proto = m.Proto()
    if getattr(R, 'presolve_live', None) is not None:
        for j in np.nonzero(~R.presolve_live)[0].tolist(): m.Add(z[j] == 0)
    bounds = np.searchsorted(E, np.unique(E), 'left').tolist() + [len(E)]
    uE = np.unique(E).tolist()
    for k, e in enumerate(uE):
        s, t = bounds[k], bounds[k + 1]
        r_ = rhs_e.get(e, Q(0)) * D * D * Dco * Dcol
        assert r_.denominator == 1
        ct = proto.constraints.add(); ct.linear.vars.extend(lam_idx[J[s:t]].tolist()); ct.linear.coeffs.extend(C[s:t].tolist())
        ct.linear.domain.extend([int(r_), int(r_)])
    for e, v in rhs_e.items():
        if v and e not in eq_present: m.AddBoolOr([])      # rhs row no candidate can reach
    if ban == 'direct':
        # forbid an insert writing r at position p1 together with an insert reading r at p2 >= p1 (sk2/PR2142 rule),
        # via per-register prefix-OR literals (linear size)
        wr = defaultdict(list); rd = defaultdict(list)
        for j, c_ in enumerate(cand): wr[c_[0]].append((c_[2], j)); rd[c_[1]].append((c_[2], j))
        for r, writers in wr.items():
            readers = rd.get(r)
            if not readers: continue
            writers.sort(); ps = sorted({p for p, _ in writers}); W = {}; prev = None
            byp = defaultdict(list)
            for p, j in writers: byp[p].append(j)
            for p in ps:
                w = m.NewBoolVar('')
                if prev is not None: m.AddImplication(prev, w)
                for j in byp[p]: m.AddImplication(z[j], w)
                W[p] = w; prev = w
            for p2, j2 in readers:
                k = bisect.bisect_right(ps, p2) - 1
                if k >= 0: m.AddImplication(z[j2], W[ps[k]].Not())
    for cut in extra_cuts: m.Add(sum(z[j] for j in cut) <= len(cut) - 1)
    m.Add(sum(z) <= maxterms)
    costs = [int(c_[5]) for c_ in cand]
    if R.bud is not None and not getattr(R, 'nobud', False): m.Add(cp_model.LinearExpr.WeightedSum(z, costs) <= R.bud)
    m.Minimize(cp_model.LinearExpr.WeightedSum(z, [c + 50 for c in costs]))
    R.m, R.lam, R.z = m, lam, z
    return m

FastRound.model = lambda self, maxterms, lamr=8, ban='none', extra_cuts=(), lam_den=2: model_lean(self, maxterms, lamr, ban, extra_cuts, lam_den)

# ---------------------------------------------------------------------------------------------------------------------
# Aggregated relaxation: for every basis block b, replace its row equations (F rows and B rows) by K random integer
# combinations.  Every solution of the full per-basis system satisfies the aggregated one, so INFEASIBLE is a proof for
# the full model; a (rare) spurious solution is caught by the exact map check of every proposal and cut by run2.
def model_agg(R, maxterms, lamr=8, ban='none', extra_cuts=(), lam_den=2, K=6, seed=1, wbits=20):
    cand = R.cand; D = R.lam_den = lam_den; rng = np.random.default_rng(seed); nreg = R.nreg
    rhs = defaultdict(dict)
    for tag, T in (('F', R.TF), ('B', R.TB)):
        for rr, row in T.items():
            co = R.basis.coords(row); assert co is not None
            for b, cb in co.items(): rhs[b][(tag, rr)] = Q(cb)
    W = rng.integers(1, 1 << wbits, size=(K, 2 * nreg), dtype=np.int64) * rng.choice([-1, 1], size=(K, 2 * nreg))
    widx = lambda tag, rr: (0 if tag == 'F' else nreg) + rr
    colw = {}
    def wcol(tag, col):
        key = (tag, tuple(sorted(col.items())))
        v = colw.get(key)
        if v is None:
            den = 1
            for _, x in col.items(): den = _lcm(den, Q(x).denominator)
            v = [0] * K
            for rr, x in col.items():
                n = int(Q(x) * den); i = widx(tag, rr)
                for k in range(K): v[k] += int(W[k, i]) * n
            v = colw[key] = (tuple(v), den)
        return v
    # per candidate: aggregated column value per k as an exact rational (numerator, denominator)
    agg = []
    Dall = 1
    for j, (x, y, i, co, (vf, vb), cst) in enumerate(cand):
        (af, df), (ab, db) = wcol('F', vf), wcol('B', vb)
        den = _lcm(df, db); a = [Q(af[k] * (den // df) + ab[k] * (den // db), den) for k in range(K)]
        agg.append(a)
        for b, cb in co.items(): Dall = _lcm(Dall, (Q(cb) * 1).denominator)
        for k in range(K): Dall = _lcm(Dall, a[k].denominator)
    rk = {}
    for b, rows in rhs.items():
        v = [Q(0)] * K
        for (tag, rr), x in rows.items():
            i = widx(tag, rr)
            for k in range(K): v[k] += x * int(W[k, i])
        rk[b] = v
        for k in range(K): Dall = _lcm(Dall, v[k].denominator)
    m = cp_model.CpModel(); lam, z = [], []
    for j in range(len(cand)):
        l = m.NewIntVar(-lamr, lamr, ''); bz = m.NewBoolVar('')
        m.Add(l == 0).OnlyEnforceIf(bz.Not()); m.Add(l != 0).OnlyEnforceIf(bz); lam.append(l); z.append(bz)
    terms = defaultdict(list)
    for j, (x, y, i, co, _, _) in enumerate(cand):
        a = agg[j]
        for b, cb in co.items():
            for k in range(K):
                c = Q(cb) * a[k] * Dall * Dall
                if c: terms[(b, k)].append((j, c))
    nterms = 0
    keys = set(terms) | {(b, k) for b in rk for k in range(K)}
    R.shape = True
    for key in keys:
        b, k = key; r_ = rk.get(b, [Q(0)] * K)[k] * D * Dall * Dall
        ts = terms.get(key, [])
        if not ts:
            if r_: m.AddBoolOr([]); R.shape = False
            continue
        assert all(c.denominator == 1 for _, c in ts) and r_.denominator == 1
        m.Add(cp_model.LinearExpr.WeightedSum([lam[j] for j, _ in ts], [int(c) for _, c in ts]) == int(r_)); nterms += len(ts)
    R.n_terms = nterms
    if ban == 'direct':
        wr = defaultdict(list); rd = defaultdict(list)
        for j, c_ in enumerate(cand): wr[c_[0]].append((c_[2], j)); rd[c_[1]].append((c_[2], j))
        for r, writers in wr.items():
            readers = rd.get(r)
            if not readers: continue
            ps = sorted({p for p, _ in writers}); byp = defaultdict(list); Wl = {}; prev = None
            for p, j in writers: byp[p].append(j)
            for p in ps:
                w = m.NewBoolVar('')
                if prev is not None: m.AddImplication(prev, w)
                for j in byp[p]: m.AddImplication(z[j], w)
                Wl[p] = w; prev = w
            for p2, j2 in readers:
                kk = bisect.bisect_right(ps, p2) - 1
                if kk >= 0: m.AddImplication(z[j2], Wl[ps[kk]].Not())
    for cut in extra_cuts: m.Add(sum(z[j] for j in cut) <= len(cut) - 1)
    m.Add(sum(z) <= maxterms)
    costs = [int(c_[5]) for c_ in cand]
    if R.bud is not None and not getattr(R, 'nobud', False): m.Add(cp_model.LinearExpr.WeightedSum(z, costs) <= R.bud)
    m.Minimize(cp_model.LinearExpr.WeightedSum(z, [c + 50 for c in costs]))
    R.m, R.lam, R.z = m, lam, z
    return m

_MODEL = os.environ.get('GEN2_MODEL', 'lean')
if _MODEL == 'agg':
    _K = int(os.environ.get('GEN2_AGG_K', '6'))
    FastRound.model = lambda self, maxterms, lamr=8, ban='none', extra_cuts=(), lam_den=2: model_agg(self, maxterms, lamr, ban, extra_cuts, lam_den, K=_K)

# Optional CP-SAT strengthening for reruns (single worker kept): GEN2_LIN = linearization_level (0..2).
def _solve(self, tl, workers=None):
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl
    s.parameters.num_workers = workers or int(os.environ.get('SK2_WORKERS', '1'))
    lin = os.environ.get('GEN2_LIN')
    if lin is not None: s.parameters.linearization_level = int(lin)
    st = s.Solve(self.m); self.last_status = s.StatusName(st); self.last_wall = s.WallTime()
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return s.StatusName(st), None
    supp = [j for j in range(len(self.cand)) if s.Value(self.z[j])]
    sol = [(j, Q(s.Value(self.lam[j]), self.lam_den)) for j in supp]
    self.m.Add(sum(self.z[j] for j in supp) <= len(supp) - 1)
    return s.StatusName(st), sol
FastRound.solve = _solve
