"""verify_small.py SYSTEM_DIR ROWGEN.json [OVERRIDE.json]: agent I-resolve (r6). Independent check of a row-generation
INFEASIBLE verdict: rebuild the final restricted model (rows final_K, candidates final_cand) as a MIP in pywraplp and solve
it with SCIP and HiGHS, with the interaction ban (should be INFEASIBLE) and without it (diagnostic)."""
import bisect, json, os, sys, time
from collections import defaultdict
import numpy as np
from ortools.linear_solver import pywraplp
sd, rgp = sys.argv[1], sys.argv[2]
Z = np.load(os.path.join(sd, 'system.npz')); rg = json.load(open(rgp)); meta = rg['meta']
E, C, J = Z['E'], Z['C'], Z['J'].astype(np.int64); costs = Z['costs'].copy(); CM = [tuple(r) for r in Z['candmeta'].tolist()]
rhs = {int(e): int(v) for e, v in zip(Z['rhs_ids'].tolist(), Z['rhs_vals'].tolist())}
if len(sys.argv) > 3:
    ov = json.load(open(sys.argv[3]))
    for j, c in ov.get('cost', {}).items(): costs[int(j)] = int(c)
K, cand = rg['final_K'], rg['final_cand']; cset = set(cand)
uE, st = np.unique(E, return_index=True); en = np.append(st[1:], len(E)); seg = {int(e): (int(a), int(b)) for e, a, b in zip(uE, st, en)}
def solve(name, ban):
    s = pywraplp.Solver.CreateSolver(name); s.SetTimeLimit(int(float(os.environ.get('VERIFY_TL', '600')) * 1000))
    lam = {j: s.IntVar(-meta['lamr'], meta['lamr'], '') for j in cand}; z = {j: s.BoolVar('') for j in cand}
    for j in cand: s.Add(lam[j] <= meta['lamr'] * z[j]); s.Add(-lam[j] <= meta['lamr'] * z[j])
    for e in K:
        a, b = seg[e]; s.Add(sum(int(c) * lam[int(j)] for j, c in zip(J[a:b].tolist(), C[a:b].tolist()) if int(j) in cset) == rhs.get(e, 0))
    s.Add(sum(z.values()) <= meta['maxterms']); s.Add(sum(int(costs[j]) * z[j] for j in cand) <= meta['bud'])
    if ban:
        wr = defaultdict(list); rd = defaultdict(list)
        for j in cand: x, y, p, _ = CM[j]; wr[x].append((p, j)); rd[y].append((p, j))
        for r, writers in wr.items():
            readers = rd.get(r)
            if not readers: continue
            ps = sorted({p for p, _ in writers}); W = {p: s.NumVar(0, 1, '') for p in ps}
            for k in range(1, len(ps)): s.Add(W[ps[k - 1]] <= W[ps[k]])
            for p, j in writers: s.Add(z[j] <= W[p])
            for p2, j2 in readers:
                k = bisect.bisect_right(ps, p2) - 1
                if k >= 0: s.Add(z[j2] + W[ps[k]] <= 1)
    t0 = time.time(); r = s.Solve()
    nm = {pywraplp.Solver.OPTIMAL: 'FEASIBLE(optimal)', pywraplp.Solver.FEASIBLE: 'FEASIBLE', pywraplp.Solver.INFEASIBLE: 'INFEASIBLE',
          pywraplp.Solver.NOT_SOLVED: 'NOT_SOLVED', pywraplp.Solver.ABNORMAL: 'ABNORMAL'}.get(r, str(r))
    return dict(solver=name, ban=ban, status=nm, seconds=round(time.time() - t0, 1))
SOLV = os.environ.get('VERIFY_SOLVERS', 'SCIP,HIGHS').split(','); BANS = (True, False) if os.environ.get('VERIFY_NOBAN', '1') == '1' else (True,)
out = dict(system=sd, rowgen=rgp, rows=len(K), cand=len(cand), checks=[solve(n, b) for b in BANS for n in SOLV])
print(json.dumps(out)); json.dump(out, open(rgp.replace('ROWGEN.json', 'VERIFY.json'), 'w'), indent=1)
