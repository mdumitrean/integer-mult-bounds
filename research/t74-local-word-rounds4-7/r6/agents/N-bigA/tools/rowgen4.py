"""rowgen4.py (agent N-bigA, r6): row generation on G-ainsert's first-order A-window split-key model (sk4.PRound4), after
agent I-resolve's rowgen.py.  usage: rowgen4.py WORD SPEC.json OUT.json [TOTAL_S] [ITER_S] [MAX_ADD]
The model is built exactly as run4.py builds it for the spec's single job (same candidates, budget, per-insert cap,
oracle-sentinel clip, quarter-step lambda, <= maxterms inserts, no interaction ban).  Equations are restricted to a growing
row set K (start: rows with a nonzero right-hand side).  Every restriction is a relaxation of the full first-order model,
so INFEASIBLE on any K proves the full first-order model infeasible.  A solution exact on ALL rows is a first-order
proposal; it is then checked like run4.py (projected exactness on the true map, exact frame set test) and written out as a
base edit for exact pricing (price3.py); its support is cut and the search continues."""
import json, math, os, sys, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk4 import PRound4, to_base_edit_ab4
from sk3 import (H, F, Q, V, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, word_seq_insert,
                 absorbable, exact_proj)
from cone import LU, feasible
from ortools.sat.python import cp_model

def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    TOTAL = float(sys.argv[4]) if len(sys.argv) > 4 else 1800; ITER = float(sys.argv[5]) if len(sys.argv) > 5 else 300
    MAXADD = int(sys.argv[6]) if len(sys.argv) > 6 else 400
    o = dict(maxterms=12, lamr=16, lam_den=4, cap=1.0, depth=1); o.update({k: v for k, v in spec.items() if k not in ('jobs', 'known')})
    P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base)
    dels = [tuple(d) for d in spec['jobs'][0]]
    W1 = compile_AB(P.base, dict(delete=dels))
    g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
    r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
    orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
    if o.get('inf_clip'):
        class _Clip:
            def __init__(s_, orc, clip): s_.orc, s_.clip = orc, clip
            def cost(s_, x, y, p): c = s_.orc.cost(x, y, p); return s_.clip if c >= 2 ** 59 else c
        orc = _Clip(orc, int(o['inf_clip']))
    NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
    for s, i in dels: gg = seq0[i if s == 'A' else NA + NC + i]; regs |= {gg[1], gg[2]}
    nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
    fam, famregs = family_values(fullseq(W1), regs, nreg, o['depth'])
    Rd = PRound4(P, W1, base_maps, orc, lambda i: i, fam, o['cap'], bud, orc_secs=sec_sizes(W1), ab=ab)
    nAd = lambda b: sum(1 for s_, i_ in dels if s_ == 'A' and i_ < b)
    Rd.a_windows = [(max(0, a - nAd(a)), min(len(W1['A']), b - nAd(b))) for a, b in spec.get('a_windows', [])]
    Rd.lu = LU(P, W1); cand = Rd.candidates()
    # equations exactly as sk3.PRound.model builds them
    eqs = defaultdict(list); rhs = {}; Dn = o['lam_den']
    for j, (x, y, i, (coN, coP), (vN, vP), cst) in enumerate(cand):
        if coN:
            for b, cb in coN.items():
                for rr, val in vN.items(): eqs[(b, 'N', rr)].append((j, cb * val))
        if coP:
            for b, cb in coP.items():
                for rr, val in vP.items(): eqs[(b, 'P', rr)].append((j, cb * val))
    for tag, T, B_ in (('N', Rd.TN, Rd.bN), ('P', Rd.TP, Rd.bP)):
        for rr, row in T.items():
            co = B_.coords(row); assert co is not None
            for b, cb in co.items(): rhs[(b, tag, rr)] = cb
    keys = sorted(set(eqs) | set(rhs), key=str)
    shape = all(k in eqs for k, v in rhs.items() if v)
    lcm = 1
    for k in keys:
        for _, val in eqs.get(k, []): lcm = lcm * Q(val).denominator // math.gcd(lcm, Q(val).denominator)
        q = Q(rhs.get(k, 0)).denominator; lcm = lcm * q // math.gcd(lcm, q)
    SC = Dn * lcm
    E = {k: [(j, int(Q(val) * SC)) for j, val in eqs.get(k, [])] for k in keys}
    R = {k: int(Q(rhs.get(k, 0)) * Dn * SC) for k in keys}
    byrow_c = {k: {j for j, _ in E[k]} for k in keys}
    costs = [c[5] for c in cand]; lamr = o['lamr']; maxterms = o['maxterms']
    print('job', dels, 'ddel', ddel, 'cand', len(cand), 'rows', len(keys), 'nonzero rhs', sum(1 for v in R.values() if v), 'shape', shape, f'{time.time()-t00:.1f}s', flush=True)
    out = dict(dels=dels, ddel=ddel, ncand=len(cand), rows=len(keys), shape=shape, log=[], proposals=[], status=None)
    if not shape:
        out['status'] = 'SHAPE_INFEASIBLE'; json.dump(out, open(out_p, 'w'), indent=1, default=str); print('done SHAPE_INFEASIBLE'); return
    K = {k for k, v in R.items() if v}; nogoods = []; it = 0
    while time.time() - t00 < TOTAL:
        it += 1; t0 = time.time(); rowsK = sorted(K, key=str)
        cj = sorted(set().union(*(byrow_c[k] for k in rowsK)))
        m = cp_model.CpModel(); lam = {}; z = {}
        for j in cj:
            l = m.NewIntVar(-lamr, lamr, ''); b = m.NewBoolVar(''); m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b)
            lam[j] = l; z[j] = b
        for k in rowsK:
            terms = [c * lam[j] for j, c in E[k] if j in lam]
            if not terms:
                if R[k]: m.AddBoolOr([])
                continue
            m.Add(sum(terms) == R[k])
        zs = [z[j] for j in cj]; m.Add(sum(zs) <= maxterms)
        m.Add(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) for j in cj]) <= bud)
        for ng in nogoods:
            if all(j in z for j in ng): m.Add(sum(z[j] for j in ng) <= len(ng) - 1)
        m.Minimize(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) + 50 for j in cj]))
        sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = min(ITER, max(5.0, TOTAL - (time.time() - t00))); sv.parameters.num_workers = 1
        st = sv.Solve(m); sname = sv.StatusName(st)
        rec = dict(it=it, rows=len(rowsK), cand=len(cj), status=sname, seconds=round(time.time() - t0, 1))
        if st == cp_model.INFEASIBLE: out['status'] = 'INFEASIBLE'; out['log'].append(rec); print(rec, flush=True); break
        if st not in (cp_model.FEASIBLE, cp_model.OPTIMAL): out['status'] = 'UNKNOWN'; out['log'].append(rec); print(rec, flush=True); break
        sol = {j: sv.Value(lam[j]) for j in cj if sv.Value(lam[j]) != 0}
        bad = []
        for k in keys:
            v = sum(c * sol.get(j, 0) for j, c in E[k]) - R[k]
            if v: bad.append((abs(v), k))
        rec.update(support=len(sol), est=int(sum(costs[j] for j in sol)), violated=len(bad)); out['log'].append(rec); print(rec, flush=True)
        if bad:
            for _, k in sorted(bad, key=lambda t: -t[0])[:MAXADD]: K.add(k)
            continue
        # first-order exact on all rows: check like run4 (true map, frames), record, cut the support, continue
        solq = [(j, Q(l, Dn)) for j, l in sol.items()]; W2, ins = Rd.apply(solq)
        terms = [(cand[j][0], cand[j][1], cand[j][2], str(Q(l, Dn))) for j, l in sol.items()]
        ex = exact_proj(base_maps, W2, ab); ok, why = feasible(P, W2) if ex else (None, None)
        e = dict(terms=terms, est=rec['est'], exact=ex, frames_ok=ok, why=str(why)[:200] if why else None)
        if ex and ok:
            try: e['edit_ab'] = to_base_edit_ab4(P.base, dels, W1, ins)
            except ValueError as err: e['edit_error'] = str(err)
        out['proposals'].append(e); nogoods.append(sorted(sol)); print('  proposal', e['terms'], 'exact', ex, 'frames', ok, flush=True)
        if len(out['proposals']) >= 12: out['status'] = 'PROPOSAL_LIMIT'; break
    if out['status'] is None: out['status'] = 'TIME'
    out['iterations'] = it; out['seconds'] = round(time.time() - t00, 1)
    json.dump([dict(dels=dels, ddel=ddel, proposals=[p for p in out['proposals'] if p.get('edit_ab')], rowgen=out)], open(out_p, 'w'), indent=1, default=str)
    print('done', out['status'], out['seconds'], flush=True)

if __name__ == '__main__':
    main()
