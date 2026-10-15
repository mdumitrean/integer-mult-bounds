"""Extended pattern relaxation: allow K role conversions w -> w-1 (or w -> w') at a hypothetical local saving s per conversion.
Reports the optimum gain vs the current fill as a function of s (break-even analysis)."""
import json, sys
from ortools.sat.python import cp_model
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcore import pats, NB, W, UP, c
from pcore import CUR
def run(conv, s, tlim=90):
    m = cp_model.CpModel(); n = {}
    for cap in NB:
        for p, rem in pats(cap): n[cap, p] = m.NewIntVar(0, NB[cap], '')
        m.Add(sum(n[cap, p] for p, rem in pats(cap)) == NB[cap])
    ne = m.NewIntVar(0, 666, 'ne'); K = m.NewIntVar(0, 666 * 240, 'K')
    a, b = conv
    N = {4: 44 * 666 - 4 * ne, 5: 44 * 666 + 4 * ne, 7: 38 * 666, 8: 114 * 666, 9: 240 * 666}
    N[a] = N[a] - K; N[b] = N[b] + K
    for w in W: m.Add(sum(v * k[1].count(w) for k, v in n.items()) == N[w])
    m.Minimize(ne * UP - K * s + sum(v * c[k[0] - sum(k[1])] for k, v in n.items()))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tlim; sv.parameters.num_workers = 1
    st = sv.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return dict(status=sv.StatusName(st))
    return dict(status=sv.StatusName(st), ne=sv.Value(ne), K=sv.Value(K), gain=CUR - sv.ObjectiveValue(), bound_gain=CUR - sv.BestObjectiveBound())
res = {}
for conv in ((9, 8), (8, 7), (5, 4), (9, 7), (9, 5)):
    for s in (2102736, 2103500, 2105000, 2108000, 2111000):
        r = run(conv, s * (conv[0] - conv[1])); res[f'{conv[0]}->{conv[1]} s={s}/level'] = r
        print(conv, s, r)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
