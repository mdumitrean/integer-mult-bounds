"""lpcert.py WORD BINDEX DEPTH OUTDIR [TIME_LIMIT_S]: agent I-resolve (r6).

Rebuilds D-depth2's round-1 depth-k split-key model for one deleted B read (gen2.FastRound, cone-aware candidates,
per-insert cap = budget, quarter-step lambda |lambda| <= 4, at most 12 inserts), then
 1. the exact integer equation system of gen2.model_lean (same scaling), saved to OUTDIR/system.npz;
 2. its LP relaxation (interaction ban dropped; lambda real in [-16,16] quarter units; z in [0,1] with |lambda| <= 16 z;
    sum z <= 12; sum cost*z <= budget) as a phase-1 LP: minimise the l1 violation of the equations (GLOP);
 3. if the phase-1 optimum is positive, an exact rational certificate: dual vector y on the equations with
       y.b > B(mu, nu) = 192 nu + 16 bud mu + 16 sum_j max(0, |y.A_j| - nu - mu cost_j)   (mu, nu >= 0),
    which proves that no real lambda satisfies the relaxation, hence the integer model is infeasible
    (for feasible lambda: y.b = sum lambda_j y.A_j <= sum |lambda_j| a_j <= B(mu, nu) by weak duality).
Builds on D-depth2's gen2.py, r3 B-interact's sk2.py/cone.py, PR2142 (Ian Libanio) and PR1957 (Rohan Arun)."""
import json, math, os, sys, time
from fractions import Fraction as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
DSCR = os.path.abspath(os.path.join(HERE, '..', '..', 'D-depth2', 'scripts'))
sys.path.insert(0, DSCR)
import types
_src = open(os.path.join(DSCR, 'gen2.py')).read()
_old = 'if cap is not None: m &= cost <= cap'
assert _src.count(_old) == 1
gen2 = types.ModuleType('gen2'); gen2.__file__ = os.path.join(DSCR, 'gen2.py')
exec(compile(_src, gen2.__file__, 'exec'), gen2.__dict__)
gen2u = types.ModuleType('gen2u'); gen2u.__file__ = os.path.join(DSCR, 'gen2.py')
exec(compile(_src.replace(_old, 'if cap is not None: m &= (cost <= cap) | (cost >= 2.0 ** 59)'), gen2u.__file__, 'exec'), gen2u.__dict__)
gen2a = types.ModuleType('gen2a'); gen2a.__file__ = os.path.join(DSCR, 'gen2.py')
exec(compile(_src.replace(_old, 'pass  # variant A: no per-insert cost cap'), gen2a.__file__, 'exec'), gen2a.__dict__)
SENT = 2 ** 59
from sk2 import H, F, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, V
from cone import LU

def lcm(a, b): return a * b // math.gcd(a, b)

def build_system(word, bi, depth, unpriced=True):
    t0 = time.time(); P = H.Pricer(word); base_maps = maps(P.base); dels = [('B', bi)]
    W1 = compile_AB(P.base, dict(delete=dels))
    g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
    r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
    orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
    NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); gg = seq0[NA + NC + bi]; regs = {gg[1], gg[2]}
    nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
    fam, famregs = family_values(fullseq(W1), regs, nreg, depth)
    mod = gen2a if os.environ.get('LPCERT_VARIANT') == 'A' else (gen2u if unpriced else gen2)
    R = mod.FastRound(P, W1, base_maps, orc, lambda i: i, fam, 1.0, bud, orc_secs=sec_sizes(W1)); R.lu = LU(P, W1)
    cand = R.candidates(); tg = time.time() - t0
    n_unpriced = sum(1 for c_ in cand if c_[5] >= SENT)
    D = 4; rhs = {}
    for tag, T in (('F', R.TF), ('B', R.TB)):
        for rr, row in T.items():
            co = R.basis.coords(row); assert co is not None
            for b, cb in co.items(): rhs[(b, tag, rr)] = Q(cb)
    coid, colid, cos_list, cols_list = {}, {}, [], []
    cj = np.empty(len(cand), np.int64); fj = np.empty(len(cand), np.int64); bj = np.empty(len(cand), np.int64)
    for j, (x, y, i, co, (vf, vb), cst) in enumerate(cand):
        k = tuple(sorted(co.items())); c = coid.get(k)
        if c is None: c = coid[k] = len(cos_list); cos_list.append(k)
        kf = ('F',) + tuple(sorted(vf.items())); f = colid.get(kf)
        if f is None: f = colid[kf] = len(cols_list); cols_list.append(kf)
        kb = ('B',) + tuple(sorted(vb.items())); h = colid.get(kb)
        if h is None: h = colid[kb] = len(cols_list); cols_list.append(kb)
        cj[j], fj[j], bj[j] = c, f, h
    keyj = {}
    for j in range(len(cand)):
        k = (int(cj[j]), int(fj[j]), int(bj[j])); c0 = 0 if cand[j][5] >= SENT else int(cand[j][5])
        if k not in keyj or c0 < keyj[k][1]: keyj[k] = (j, c0)
    keep = sorted(j for j, _ in keyj.values()); n_raw = len(cand)
    if os.environ.get('LPCERT_NODEDUP'): keep = list(range(len(cand)))
    cand = [cand[j] for j in keep]; cj, fj, bj = cj[keep], fj[keep], bj[keep]
    Dco = 1
    for k in cos_list:
        for _, v in k: Dco = lcm(Dco, Q(v).denominator)
    for v in rhs.values(): Dco = lcm(Dco, v.denominator)
    Dcol = 1
    for k in cols_list:
        for _, v in k[1:]: Dcol = lcm(Dcol, Q(v).denominator)
    nreg = R.nreg
    def eqid(b, tag, rr): return (b * 2 + (0 if tag == 'F' else 1)) * nreg + rr
    co_b = [np.array([b for b, _ in k], np.int64) for k in cos_list]
    co_n = [[int(Q(v) * Dco) for _, v in k] for k in cos_list]
    col_r = [np.array([rr for rr, _ in k[1:]], np.int64) for k in cols_list]
    col_t = [0 if k[0] == 'F' else 1 for k in cols_list]
    col_n = [[int(Q(v) * Dcol) for _, v in k[1:]] for k in cols_list]
    mco = max((abs(v) for k in co_n for v in k), default=1); mcol = max((abs(v) for k in col_n for v in k), default=1)
    assert mco * mcol * D < 2 ** 62, ('int64 overflow risk', mco, mcol)
    co_n = [np.array(k, np.int64) for k in co_n]; col_n = [np.array(k, np.int64) for k in col_n]
    Js, Es, Cs = [], [], []
    for j in range(len(cand)):
        c = cj[j]; bvec, nvec = co_b[c], co_n[c]
        for f in (fj[j], bj[j]):
            rr, nn = col_r[f], col_n[f]
            if not len(rr): continue
            e = ((bvec[:, None] * 2 + col_t[f]) * nreg + rr[None, :]).ravel()
            Cs.append((nvec[:, None] * nn[None, :]).ravel() * D); Es.append(e); Js.append(np.full(len(e), j, np.int64))
    E = np.concatenate(Es); C = np.concatenate(Cs); J = np.concatenate(Js); del Es, Cs, Js
    order = np.lexsort((J, E)); E, C, J = E[order], C[order], J[order]
    rhs_e = {}
    for (b, t, rr), v in rhs.items():
        r_ = v * D * D * Dco * Dcol; assert r_.denominator == 1
        if r_: rhs_e[eqid(b, t, rr)] = int(r_)
    costs = np.array([0 if c_[5] >= SENT else int(c_[5]) for c_ in cand], np.int64)
    if os.environ.get('LPCERT_VARIANT') == 'A': costs = np.zeros(len(cand), np.int64)   # no cost information at all
    unp = np.array([c_[5] >= SENT for c_ in cand], bool)
    meta = dict(word=os.path.basename(word), bindex=bi, depth=depth, ddel=int(ddel), bud=int(bud), ncand=len(cand),
                basis=len(R.basis.piv), residual_rank=R.nT, nterms=int(len(E)), Dco=Dco, Dcol=Dcol, lam_den=D, lamr=16,
                maxterms=12, gen_seconds=round(tg, 1), max_abs_coef=int(np.abs(C).max()) if len(C) else 0,
                rhs_rows=len(rhs_e), rows=int(len(np.unique(E))), cone_rejected=R.cone_rejected,
                variant='U (sentinel candidates kept, cost 0)' if unpriced else 'D (cap filter as D-depth2)',
                n_raw=n_raw, n_unpriced_raw=n_unpriced, n_unpriced_dedup=int(unp.sum()))
    candmeta = [(int(c_[0]), int(c_[1]), int(c_[2]), min(int(c_[5]), 2 ** 62)) for c_ in cand]
    return meta, E, C, J, rhs_e, costs, candmeta

def solve_phase1(E, C, J, rhs_e, costs, bud, ncand, tlim, maxterms=12, lamr=16):
    from ortools.linear_solver import pywraplp
    from ortools.linear_solver import linear_solver_pb2 as pb
    uE, starts = np.unique(E, return_index=True); ends = list(starts[1:]) + [len(E)]
    rows = list(uE.tolist()); allrows = sorted(set(rows) | set(rhs_e))
    rowpos = {e: k for k, e in enumerate(allrows)}
    m = pb.MPModelProto(); m.maximize = False
    for j in range(ncand):
        v = m.variable.add(); v.lower_bound = -lamr; v.upper_bound = lamr; v.objective_coefficient = 0
    for j in range(ncand):
        v = m.variable.add(); v.lower_bound = 0; v.upper_bound = 1; v.objective_coefficient = 0
    nr = len(allrows); sp0 = 2 * ncand
    for k in range(nr):
        v = m.variable.add(); v.lower_bound = 0; v.upper_bound = math.inf; v.objective_coefficient = 1
        v = m.variable.add(); v.lower_bound = 0; v.upper_bound = math.inf; v.objective_coefficient = 1
    scale = {}
    seg = {e: (s, t) for e, s, t in zip(rows, starts.tolist(), ends)}
    for k, e in enumerate(allrows):
        s, t = seg.get(e, (0, 0)); cc = C[s:t]; mx = float(max(np.abs(cc).max() if t > s else 0, abs(rhs_e.get(e, 0)), 1))
        scale[e] = mx; ct = m.constraint.add()
        ct.var_index.extend(J[s:t].tolist() + [sp0 + 2 * k, sp0 + 2 * k + 1])
        ct.coefficient.extend((cc / mx).tolist() + [1.0, -1.0])
        r = rhs_e.get(e, 0) / mx; ct.lower_bound = r; ct.upper_bound = r
    for j in range(ncand):
        ct = m.constraint.add(); ct.var_index.extend([j, ncand + j]); ct.coefficient.extend([1.0, -float(lamr)]); ct.lower_bound = -math.inf; ct.upper_bound = 0
        ct = m.constraint.add(); ct.var_index.extend([j, ncand + j]); ct.coefficient.extend([-1.0, -float(lamr)]); ct.lower_bound = -math.inf; ct.upper_bound = 0
    ct = m.constraint.add(); ct.var_index.extend(range(ncand, 2 * ncand)); ct.coefficient.extend([1.0] * ncand); ct.lower_bound = -math.inf; ct.upper_bound = maxterms
    kcard = len(m.constraint) - 1
    ct = m.constraint.add(); ct.var_index.extend(range(ncand, 2 * ncand)); ct.coefficient.extend([float(c) for c in costs.tolist()]); ct.lower_bound = -math.inf; ct.upper_bound = float(bud)
    kbud = len(m.constraint) - 1
    solver = pywraplp.Solver.CreateSolver('GLOP'); ok = solver.LoadModelFromProto(m); assert ok == '', ok
    solver.SetTimeLimit(int(tlim * 1000)); t0 = time.time(); st = solver.Solve(); dt = time.time() - t0
    names = {pywraplp.Solver.OPTIMAL: 'OPTIMAL', pywraplp.Solver.INFEASIBLE: 'INFEASIBLE', pywraplp.Solver.NOT_SOLVED: 'NOT_SOLVED',
             pywraplp.Solver.ABNORMAL: 'ABNORMAL', pywraplp.Solver.FEASIBLE: 'FEASIBLE', pywraplp.Solver.UNBOUNDED: 'UNBOUNDED'}
    res = dict(status=names.get(st, str(st)), seconds=round(dt, 1), rows=nr)
    if st != pywraplp.Solver.OPTIMAL: return res, None
    cons = solver.constraints(); vars_ = solver.variables()
    res['objective'] = solver.Objective().Value()
    y = {e: cons[k].dual_value() / scale[e] for k, e in enumerate(allrows)}
    res['mu_lp'] = cons[kbud].dual_value(); res['nu_lp'] = cons[kcard].dual_value()
    lam = np.array([vars_[j].solution_value() for j in range(ncand)]); zz = np.array([vars_[ncand + j].solution_value() for j in range(ncand)])
    res['lp_support'] = int((np.abs(lam) > 1e-7).sum()); res['lp_sum_z'] = float(zz.sum()); res['lp_cost'] = float((zz * costs).sum())
    return res, dict(y=y, lam=lam, z=zz)

def certify(E, C, J, rhs_e, costs, bud, ncand, ydict, mu0, nu0, maxterms=12, lamr=16, den=2 ** 24):
    """Exact check. y rationalised to multiples of 1/den. Returns dict with verdict."""
    Y = {e: int(round(v * den)) for e, v in ydict.items() if round(v * den) != 0}
    if not Y: return dict(valid=False, reason='zero y')
    yb = sum(Y.get(e, 0) * v for e, v in rhs_e.items())          # = den * (y.b)
    if yb < 0: Y = {e: -v for e, v in Y.items()}; yb = -yb
    if yb == 0: return dict(valid=False, reason='y.b == 0')
    a = [0] * ncand
    El, Cl, Jl = E.tolist(), C.tolist(), J.tolist()
    for e, c, j in zip(El, Cl, Jl):
        ye = Y.get(e)
        if ye: a[j] += ye * c
    a = [abs(v) for v in a]                                          # = den * |y.A_j| exactly (integers)
    cl = costs.tolist()
    def B(mu, nu):   # all scaled by den: mu, nu are Fractions in units of den
        s = 0
        for aj, cj in zip(a, cl):
            t = aj - nu - mu * cj
            if t > 0: s += t
        return lamr * maxterms * nu + lamr * bud * mu + lamr * s
    best = None
    cands = []
    mu_s = Q(abs(mu0)).limit_denominator(10 ** 6) * den if mu0 is not None else Q(0)
    nu_s = Q(abs(nu0)).limit_denominator(10 ** 6) * den if nu0 is not None else Q(0)
    for fm in (0, Q(1, 2), 1, 2):
        for fn in (0, Q(1, 2), 1, 2):
            cands.append((mu_s * fm, nu_s * fn))
    # pure-budget and pure-cardinality choices from the data (breakpoints)
    amax = max(a)
    cands += [(Q(0), Q(amax)), (Q(0), Q(0))]
    rat = sorted(((Q(aj, cj) if cj > 0 else None) for aj, cj in zip(a, cl) if aj > 0 and cj > 0), reverse=True)[:50]
    cands += [(r_, Q(0)) for r_ in rat if r_ is not None]
    for mu, nu in cands:
        val = B(mu, nu)
        if best is None or val < best[0]: best = (val, mu, nu)
    val, mu, nu = best
    return dict(valid=yb > val, yb_scaled=str(yb), bound_scaled=str(val), margin=float((Q(yb) - val) / max(abs(Q(yb)), 1)),
                mu=str(mu / den), nu=str(nu / den), den=den, ysupport=len(Y))

if __name__ == '__main__':
    word, bi, depth, outdir = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    tlim = float(sys.argv[5]) if len(sys.argv) > 5 else 1800
    os.makedirs(outdir, exist_ok=True); t00 = time.time()
    unpriced = os.environ.get('LPCERT_VARIANT', 'U') == 'U'
    meta, E, C, J, rhs_e, costs, candmeta = build_system(word, bi, depth, unpriced)
    print('system', json.dumps(meta), f'{time.time()-t00:.1f}s', flush=True)
    np.savez_compressed(os.path.join(outdir, 'system.npz'), E=E, C=C, J=J.astype(np.int32), costs=costs,
                        rhs_ids=np.array(list(rhs_e.keys()), np.int64), rhs_vals=np.array([str(v) for v in rhs_e.values()]),
                        candmeta=np.array(candmeta, np.int64))
    if os.environ.get('LPCERT_NOLP'):
        json.dump(dict(meta=meta, phase1='skipped'), open(os.path.join(outdir, 'out.json'), 'w'), indent=1); print('saved'); sys.exit()
    res, sol = solve_phase1(E, C, J, rhs_e, costs, meta['bud'], meta['ncand'], tlim)
    print('phase1', json.dumps(res), flush=True)
    out = dict(meta=meta, phase1=res)
    if sol is not None and res.get('objective', 0) > 1e-7:
        cert = certify(E, C, J, rhs_e, costs, meta['bud'], meta['ncand'], sol['y'], res.get('mu_lp'), res.get('nu_lp'))
        out['certificate'] = cert; print('certificate', json.dumps(cert), flush=True)
        if cert.get('valid'):
            json.dump({str(k): v for k, v in sol['y'].items() if abs(v) > 0}, open(os.path.join(outdir, 'y.json'), 'w'))
    elif sol is not None:
        np.savez_compressed(os.path.join(outdir, 'lp_solution.npz'), lam=sol['lam'], z=sol['z'])
    out['seconds'] = round(time.time() - t00, 1)
    json.dump(out, open(os.path.join(outdir, 'out.json'), 'w'), indent=1, default=str)
    print('done', out['seconds'], flush=True)
