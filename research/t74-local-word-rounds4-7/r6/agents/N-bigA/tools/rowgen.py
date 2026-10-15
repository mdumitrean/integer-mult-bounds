"""rowgen.py SYSTEM_DIR OUT.json [TOTAL_S] [ITER_S] [MAX_ADD]: agent I-resolve (r6).
Row generation for the integer split-key model saved by lpcert.py (tensor-deduplicated, interaction ban dropped, i.e. a
relaxation of D-depth2's round-1 model): lambda_j integer in [-16,16] (quarter steps), z_j = [lambda_j != 0],
sum z <= 12, sum cost*z <= budget, equations restricted to a growing row set K (start: the target's nonzero rows).
Every restricted model is a relaxation of the full model, so INFEASIBLE on any K proves the full model infeasible.
A solution exact on ALL rows is an exact proposal (reported for pricing); otherwise its violated rows join K."""
import json, os, sys, time
import numpy as np
from ortools.sat.python import cp_model
sysdir, outp = sys.argv[1], sys.argv[2]
TOTAL = float(sys.argv[3]) if len(sys.argv) > 3 else 1800; ITER = float(sys.argv[4]) if len(sys.argv) > 4 else 120
MAXADD = int(sys.argv[5]) if len(sys.argv) > 5 else 400
t00 = time.time(); Z = np.load(os.path.join(sysdir, 'system.npz')); meta = json.load(open(os.path.join(sysdir, 'out.json')))['meta']
E, C, J, costs = Z['E'], Z['C'], Z['J'].astype(np.int64), Z['costs']
rhs = {int(e): int(v) for e, v in zip(Z['rhs_ids'].tolist(), Z['rhs_vals'].tolist())}
n = len(costs); bud = meta['bud']; lamr = meta['lamr']; maxterms = meta['maxterms']
CM = [tuple(r) for r in Z['candmeta'].tolist()]; BAN = os.environ.get('ROWGEN_BAN', '1') == '1'
excluded = set()
if len(sys.argv) > 6:
    ov = json.load(open(sys.argv[6])); costs = costs.copy()
    for j, c in ov.get('cost', {}).items(): costs[int(j)] = int(c)
    excluded = set(int(j) for j in ov.get('exclude', []))
    print('override: costs', len(ov.get('cost', {})), 'excluded', len(excluded), flush=True)
uE, st = np.unique(E, return_index=True); en = np.append(st[1:], len(E)); seg = {int(e): (int(a), int(b)) for e, a, b in zip(uE, st, en)}
for e in rhs:
    if e not in seg: print('rhs row unreachable -> INFEASIBLE (shape)', e); json.dump(dict(meta=meta, status='SHAPE_INFEASIBLE'), open(outp, 'w')); sys.exit()
oj = np.argsort(J, kind='stable'); Jo = J[oj]; Eo = E[oj]; Co = C[oj]
js, jstart = np.unique(Jo, return_index=True); jend = np.append(jstart[1:], len(Jo)); jseg = {int(j): (int(a), int(b)) for j, a, b in zip(js, jstart, jend)}
print('loaded', n, 'cand', len(E), 'terms', len(uE), 'rows', f'{time.time()-t00:.1f}s', flush=True)
K = set(rhs); log = []; proposals = []; status = None; it = 0; nogoods = []; finalK = None; finalC = None
while time.time() - t00 < TOTAL:
    it += 1; t0 = time.time()
    rowsK = sorted(K); cand = np.unique(np.concatenate([J[seg[e][0]:seg[e][1]] for e in rowsK]))
    if excluded: cand = np.array([j for j in cand.tolist() if j not in excluded], np.int64)
    m = cp_model.CpModel(); lam = {}; z = {}
    for j in cand.tolist():
        l = m.NewIntVar(-lamr, lamr, ''); b = m.NewBoolVar(''); m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b)
        lam[j] = l; z[j] = b
    for e in rowsK:
        a, b_ = seg[e]; jj = J[a:b_].tolist(); cc = C[a:b_].tolist()
        m.Add(sum(c * lam[j] for j, c in zip(jj, cc) if j in lam) == rhs.get(e, 0))
    zs = [z[j] for j in cand.tolist()]
    m.Add(sum(zs) <= maxterms)
    if BAN:   # D-depth2/sk2/PR2142 'direct' rule: no insert writing r at p1 with an insert reading r at p2 >= p1
        from collections import defaultdict
        import bisect
        wr = defaultdict(list); rd = defaultdict(list)
        for j in cand.tolist(): x_, y_, p_, _ = CM[j]; wr[x_].append((p_, j)); rd[y_].append((p_, j))
        for r_, writers in wr.items():
            readers = rd.get(r_)
            if not readers: continue
            ps = sorted({p_ for p_, _ in writers}); byp = defaultdict(list); W = {}; prev = None
            for p_, j in writers: byp[p_].append(j)
            for p_ in ps:
                w = m.NewBoolVar('')
                if prev is not None: m.AddImplication(prev, w)
                for j in byp[p_]: m.AddImplication(z[j], w)
                W[p_] = w; prev = w
            for p2, j2 in readers:
                k = bisect.bisect_right(ps, p2) - 1
                if k >= 0: m.AddImplication(z[j2], W[ps[k]].Not())
    m.Add(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) for j in cand.tolist()]) <= bud)
    for ng in nogoods:
        if all(j in z for j in ng): m.Add(sum(z[j] for j in ng) <= len(ng) - 1)
    m.Minimize(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) + 50 for j in cand.tolist()]))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = min(ITER, max(5.0, TOTAL - (time.time() - t00))); sv.parameters.num_workers = 1
    r = sv.Solve(m); sname = sv.StatusName(r)
    rec = dict(it=it, rows=len(rowsK), cand=int(len(cand)), status=sname, seconds=round(time.time() - t0, 1))
    if r == cp_model.INFEASIBLE:
        status = 'INFEASIBLE'; log.append(rec); print(rec, flush=True); finalK = rowsK; finalC = cand.tolist(); break
    if r not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        status = 'UNKNOWN'; log.append(rec); print(rec, flush=True); break
    sol = {j: sv.Value(lam[j]) for j in cand.tolist() if sv.Value(lam[j]) != 0}
    res = {}
    for j, l in sol.items():
        a, b_ = jseg[j]
        for e, c in zip(Eo[a:b_].tolist(), Co[a:b_].tolist()): res[e] = res.get(e, 0) + c * l
    for e, v in rhs.items(): res[e] = res.get(e, 0) - v
    bad = sorted((e for e, v in res.items() if v != 0), key=lambda e: -abs(res[e]))
    rec.update(support=len(sol), est=int(sum(costs[j] for j in sol)), violated=len(bad))
    log.append(rec); print(rec, flush=True)
    if not bad:
        proposals.append(dict(sol={str(j): l for j, l in sol.items()}, est=rec['est'])); nogoods.append(sorted(sol))
        if len(proposals) >= 20: status = 'PROPOSAL_LIMIT'; break
        continue
    K.update(bad[:MAXADD])
if status is None: status = 'TIME'
out = dict(meta=meta, ban=BAN, final_K=finalK, final_cand=finalC, excluded=sorted(excluded), status=status, iterations=it, final_rows=len(K), proposals=proposals, log=log, seconds=round(time.time() - t00, 1))
json.dump(out, open(outp, 'w'), indent=1); print('done', status, out['seconds'], flush=True)
