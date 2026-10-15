import sys
from ortools.sat.python import cp_model
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from patterns import pats, cur, WID
def solve(x, E, drop=()):
    mdl = cp_model.CpModel(); D = {}
    for cap in (8, 16, 32, 48):
        P = pats(cap) + ([()] if cap == 48 else [])
        for p in P: D[cap, p] = mdl.NewIntVar(-cur[cap].get(p, 0), 60000, '')
        if cap == 48: mdl.Add(D[48, ()] == x); mdl.Add(sum(D[48, p] for p in P if p) == -x)
        else: mdl.Add(sum(D[cap, p] for p in P) == 0)
    for w in WID:
        if w in drop: continue
        target = 4 * E if w == 4 else (-4 * E if w == 5 else 0)
        mdl.Add(sum(D[k] * k[1].count(w) for k in D) == target)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 20; s.parameters.num_workers = 1
    st = s.Solve(mdl); return s.StatusName(st), ({f'{k[0]}:{k[1]}': s.Value(v) for k, v in D.items() if s.Value(v)} if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None)
print('x=0,E=0', solve(0, 0)[0])
print('x=1,E=12', solve(1, 12)[0])
for d in WID: print('x=1,E=12 drop', d, solve(1, 12, (d,))[0])
print('x=0,E=12 (revert only, no emptied bin; width must drop 48 -> infeasible expected)', solve(0, 12)[0])
for E in (12, 13, 24): print('x=1 E', E, solve(1, E)[0])
print('pattern counts', {c: len(pats(c)) for c in (8, 16, 32, 48)})
