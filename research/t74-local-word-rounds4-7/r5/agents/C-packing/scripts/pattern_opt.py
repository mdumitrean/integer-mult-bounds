"""Pattern-level relaxation of the T74 packing with partial bins allowed: minimize local extra-word cost + idle cost.
Necessary conditions only (ignores call identity, windows, families, prefix stacking). Costs c[r] at b (COSTS.json)."""
import json, sys
from ortools.sat.python import cp_model
W = (4, 5, 7, 8, 9); NB = {8: 49728, 16: 33152, 32: 33152, 48: 33152}
c = {int(k): v for k, v in json.load(open(sys.argv[1]))['c'].items()}; c[0] = 0
UP = 8458352   # local cost of the extra word over the base word, per call (4 upgrades), r4 D-widths
def pats(cap):
    out = []
    def rec(rem, start, cur):
        out.append((tuple(cur), rem))
        for i in range(start, len(W)):
            if W[i] <= rem: rec(rem - W[i], i, cur + [W[i]])
    rec(cap, 0, []); return out
cur = {(8, (8,)): 41112, (8, (4, 4)): 8616, (16, (7, 9)): 20948, (16, (8, 8)): 12204, (32, (5, 9, 9, 9)): 30972,
       (32, (7, 7, 9, 9)): 2180, (48, ()): 22748, (48, (4, 8, 9, 9, 9, 9)): 10404}
def run(fix_ne=None, hint=True, tlim=120):
    m = cp_model.CpModel(); n = {}
    for cap in NB:
        for p, rem in pats(cap):
            n[cap, p] = m.NewIntVar(0, NB[cap], '')
        m.Add(sum(n[cap, p] for p, rem in pats(cap)) == NB[cap])
    ne = m.NewIntVar(0, 666, 'ne')
    if fix_ne is not None: m.Add(ne == fix_ne)
    N = {4: 44 * 666 - 4 * ne, 5: 44 * 666 + 4 * ne, 7: 38 * 666, 8: 114 * 666, 9: 240 * 666}
    for w in W: m.Add(sum(v * k[1].count(w) for k, v in n.items()) == N[w])
    obj = ne * UP + sum(v * c[k[0] - sum(k[1])] for k, v in n.items())
    m.Minimize(obj)
    if hint:
        for k, v in n.items(): m.AddHint(v, cur.get(k, 0))
        m.AddHint(ne, 417)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tlim; s.parameters.num_workers = 1
    st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return dict(status=s.StatusName(st))
    used = {f'{k[0]}:{list(k[1])}+{k[0]-sum(k[1])}': s.Value(v) for k, v in n.items() if s.Value(v)}
    return dict(status=s.StatusName(st), ne=s.Value(ne), objective=s.ObjectiveValue(), bound=s.BestObjectiveBound(), patterns=used)
base_obj = 417 * UP + 22748 * c[48]
print('current objective', base_obj)
res = dict(current_objective=base_obj, runs={})
for fix in (None, 417, 0, 200, 405):
    r = run(fix); res['runs'][str(fix)] = r
    print('fix_ne', fix, r.get('status'), 'ne', r.get('ne'), 'obj', r.get('objective'), 'gap_to_current', (r.get('objective') - base_obj) if r.get('objective') is not None else None, 'bound', r.get('bound'))
    if r.get('patterns') and fix is None: print('  patterns', r['patterns'])
json.dump(res, open(sys.argv[2], 'w'), indent=1)
