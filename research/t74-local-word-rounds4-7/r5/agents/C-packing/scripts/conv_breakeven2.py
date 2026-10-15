"""Break-even for conversions that introduce a new width (7->6, 4->3, 8->6): patterns over widths incl. the new one."""
import json, sys
from ortools.sat.python import cp_model
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcore import pats, NB, UP, c, CUR
def run(conv, s, widths, tlim=150):
    m = cp_model.CpModel(); n = {}
    for cap in NB:
        P = pats(cap, widths)
        for p, rem in P: n[cap, p] = m.NewIntVar(0, NB[cap], '')
        m.Add(sum(n[cap, p] for p, rem in P) == NB[cap])
    ne = m.NewIntVar(0, 666, 'ne'); K = m.NewIntVar(0, 666 * 240, 'K'); a, b = conv
    N = {w: 0 for w in widths}; N.update({4: 44 * 666 - 4 * ne, 5: 44 * 666 + 4 * ne, 7: 38 * 666, 8: 114 * 666, 9: 240 * 666})
    N[a] = N[a] - K; N[b] = N[b] + K
    for w in widths: m.Add(sum(v * k[1].count(w) for k, v in n.items()) == N[w])
    m.Minimize(ne * UP - K * s + sum(v * c[k[0] - sum(k[1])] for k, v in n.items()))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = tlim; sv.parameters.num_workers = 1; st = sv.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return dict(status=sv.StatusName(st))
    return dict(status=sv.StatusName(st), ne=sv.Value(ne), K=sv.Value(K), gain=CUR - sv.ObjectiveValue(), bound_gain=CUR - sv.BestObjectiveBound(), npat=len(n))
res = {}
for conv, widths in (((7, 6), (4, 5, 6, 7, 8, 9)), ((4, 3), (3, 4, 5, 7, 8, 9)), ((8, 6), (4, 5, 6, 7, 8, 9))):
    for s in (2102736, 2105000, 2111000):
        r = run(conv, s * (conv[0] - conv[1]), widths); res[f'{conv[0]}->{conv[1]} s={s}/level'] = r; print(conv, s, r, flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
