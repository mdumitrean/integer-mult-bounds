"""Pattern-level relaxation: minimal composition changes to revert 4E' upgrades (5->4) and empty x 48-bins (E' = 12x).
Ignores call identity, windows and families (a necessary condition only)."""
import itertools, json, sys
from ortools.sat.python import cp_model
WID = (4, 5, 7, 8, 9)
def pats(cap):
    out = []
    def rec(rem, start, cur):
        if rem == 0: out.append(tuple(cur)); return
        for i in range(start, len(WID)):
            w = WID[i]
            if w <= rem: rec(rem - w, i, cur + [w])
    rec(cap, 0, []); return out
cur = {8: {(8,): 41112, (4, 4): 8616}, 16: {(7, 9): 20948, (8, 8): 12204}, 32: {(5, 9, 9, 9): 30972, (7, 7, 9, 9): 2180},
       48: {(): 22748, (4, 8, 9, 9, 9, 9): 10404}}
if __name__ == '__main__':
    res = {}
    for x in (1, 2, 34):
        E = 12 * x; mdl = cp_model.CpModel(); D = {}; absd = []
        for cap in (8, 16, 32, 48):
            P = pats(cap) + ([()] if cap == 48 else [])
            for p in P:
                lo = -cur[cap].get(p, 0); D[cap, p] = mdl.NewIntVar(lo, 40000, f'd{cap}{p}')
                a = mdl.NewIntVar(0, 40000, ''); mdl.AddAbsEquality(a, D[cap, p]); absd.append(a)
            if cap == 48: mdl.Add(D[48, ()] == x); mdl.Add(sum(D[48, p] for p in P if p) == -x)
            else: mdl.Add(sum(D[cap, p] for p in P) == 0)
        for w in WID:
            target = 4 * E if w == 4 else (-4 * E if w == 5 else 0)
            mdl.Add(sum(D[k] * k[1].count(w) for k in D) == target)
        mdl.Minimize(sum(absd)); s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 60; s.parameters.num_workers = 1
        st = s.Solve(mdl)
        ch = {f'{k[0]}:{list(k[1])}': s.Value(v) for k, v in D.items() if s.Value(v)} if st in (cp_model.OPTIMAL, cp_model.FEASIBLE) else None
        res[x] = dict(status=s.StatusName(st), reverted_calls=E, bins_changed=s.ObjectiveValue() if ch else None, changes=ch)
        print(x, res[x]['status'], 'bins changed', res[x]['bins_changed'], ch)
    json.dump(res, open(sys.argv[1], 'w'), indent=1)
