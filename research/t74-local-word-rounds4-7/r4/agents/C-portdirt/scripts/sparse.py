"""sparse.py: for each read with target_in_span, find sparse absorbed compensations with CP-SAT:
sum_j lam_j * nonord(row_{y_j}(p_j)) = nonord(c * row_s(i)) over the census's frame-feasible inserts (t += lam_j y_j before
W index p_j), lam_j in quarter steps with |lam_j| <= 4, at most MAXT terms, minimum support first; up to K supports per read.
Writes pdprice candidates with an explicit multi-insert edit on BASE indices (W index p -> base index p if p <= i else p+1).
usage: sparse.py CENSUS.json OUT.json [MAXT] [K] [SECONDS]"""
import json, sys, math
from fractions import Fraction as Fr
from ortools.sat.python import cp_model
cen = json.load(open(sys.argv[1])); MAXT = int(sys.argv[3]) if len(sys.argv) > 3 else 12
K = int(sys.argv[4]) if len(sys.argv) > 4 else 3; TL = float(sys.argv[5]) if len(sys.argv) > 5 else 60
out = []; summary = []
for r in cen:
    if not r.get('target_in_span'): continue
    i, t = r['B'], r['t']; tgt = {int(k): Fr(a) for k, a in r['target']}
    ins = [(x['y'], x['p'], {int(k): Fr(a) for k, a in x['nv']}) for x in r['inserts']]
    cols = sorted(set(tgt) | {k for _, _, nv in ins for k in nv})
    lcm = 1
    for v in [tgt] + [nv for _, _, nv in ins]:
        for a in v.values(): lcm = lcm * a.denominator // math.gcd(lcm, a.denominator)
    D = 4; SC = lcm * D
    m = cp_model.CpModel(); lam = []; z = []
    for j in range(len(ins)):
        l = m.NewIntVar(-4 * D, 4 * D, ''); b = m.NewBoolVar('')
        m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b); lam.append(l); z.append(b)
    for k in cols:
        terms = [lam[j] * int(nv[k] * lcm) for j, (_, _, nv) in enumerate(ins) if k in nv]
        rhs = tgt.get(k, Fr(0)) * SC
        assert rhs.denominator == 1
        if terms: m.Add(sum(terms) == int(rhs))
        elif rhs: m.AddBoolOr([])
    m.Add(sum(z) <= MAXT); m.Minimize(sum(z))
    sols = []
    for _ in range(K):
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = TL; s.parameters.num_workers = 1
        st = s.Solve(m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): break
        supp = [j for j in range(len(ins)) if s.Value(z[j])]
        sol = [(ins[j][0], ins[j][1], Fr(s.Value(lam[j]), D)) for j in supp]; sols.append(sol)
        m.Add(sum(z[j] for j in supp) <= len(supp) - 1)
    summary.append(dict(B=i, t=t, inserts=len(ins), solutions=[len(x) for x in sols], status=s.StatusName(st) if not sols or len(sols) < K else 'K'))
    print(summary[-1], flush=True)
    g = None
    for sol in sols:
        insert = [(p if p <= i else p + 1, ['add', t, y, l.numerator, l.denominator, []]) for y, p, l in sol]
        out.append(dict(B=i, t=t, s=r['s'], y=-1, p=-len(out) - 1, c=[0, 1], ed=dict(delete=[i], insert=insert),
                        terms=[[y, p, str(l)] for y, p, l in sol]))
json.dump(dict(cands=out, summary=summary), open(sys.argv[2], 'w'), indent=1)
print('candidates', len(out))
