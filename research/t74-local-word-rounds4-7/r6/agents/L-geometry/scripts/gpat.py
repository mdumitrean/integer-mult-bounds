"""Pattern-level relaxation of the T74 packing for an ALTERNATIVE child-rank geometry (r6 L-geometry).
Like r5 C's pattern_opt.py (necessary conditions only: ignores windows, families, call identity, prefix stacking), but each
of the 18 idle children per (replica, port) may have any rank; bins of equal rank are pooled (8,288 bins per child).
Partial bins allowed (leftover priced c[leftover]); leftover <= LMAX (halving reserve: 73^2 > 2*max^2 => max jump <= 51).
Objective = ne * UP + sum(c[leftover]) over bins, as r5 C (base local costs are constant).
usage: gpat.py COSTS.json GEOMS.json OUT.json [tlim]   GEOMS = {name: [rank of child 0..17]}"""
import json, sys, time, collections
from ortools.sat.python import cp_model
W = (4, 5, 7, 8, 9); PER = 74 * 112; UP = 8458352; LMAX = 51
c = {int(k): v for k, v in json.load(open(sys.argv[1]))['c'].items()}; c[0] = 0
geoms = json.load(open(sys.argv[2])); tlim = float(sys.argv[4]) if len(sys.argv) > 4 else 120
def pats(cap):
    out = []
    def rec(rem, start, cur):
        if rem <= LMAX: out.append((tuple(cur), rem))
        for i in range(start, len(W)):
            if W[i] <= rem: rec(rem - W[i], i, cur + [W[i]])
    rec(cap, 0, []); return out
def solve(ranks, hint=None):
    NB = collections.Counter()
    for k in ranks:
        if k > 0: NB[k] += PER
    m = cp_model.CpModel(); n = {}
    for cap in NB:
        P = pats(cap)
        if not P: return dict(status='NO_PATTERN', cap=cap)
        for p, rem in P: n[cap, p] = m.NewIntVar(0, NB[cap], '')
        m.Add(sum(n[cap, p] for p, rem in P) == NB[cap])
    ne = m.NewIntVar(0, 666, 'ne')
    N = {4: 44 * 666 - 4 * ne, 5: 44 * 666 + 4 * ne, 7: 38 * 666, 8: 114 * 666, 9: 240 * 666}
    for w in W: m.Add(sum(v * k[1].count(w) for k, v in n.items()) == N[w])
    m.Minimize(ne * UP + sum(v * c[k[0] - sum(k[1])] for k, v in n.items()))
    if hint:
        for k, v in n.items(): m.AddHint(v, hint.get(k, 0))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tlim; s.parameters.num_workers = 1
    t = time.time(); st = s.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return dict(status=s.StatusName(st), seconds=round(time.time() - t, 1))
    used = {f'{k[0]}:{"+".join(map(str, k[1])) or "empty"}': s.Value(v) for k, v in n.items() if s.Value(v)}
    idle = collections.Counter()
    for k, v in n.items():
        if s.Value(v) and k[0] - sum(k[1]): idle[k[0] - sum(k[1])] += s.Value(v)
    return dict(status=s.StatusName(st), ne=s.Value(ne), objective=int(s.ObjectiveValue()), bound=int(s.BestObjectiveBound()),
                idle={str(r): v for r, v in sorted(idle.items())}, patterns=used, capacity=sum(r * v for r, v in NB.items()),
                seconds=round(time.time() - t, 1))
base = 417 * UP + 22748 * c[48]
res = {}
for name, ranks in geoms.items():
    r = solve(ranks); r['ranks'] = ranks; r['gain_units'] = (base - r['objective']) if 'objective' in r else None; res[name] = r
    print(name, r['status'], 'obj', r.get('objective'), 'bound', r.get('bound'), 'gain', r.get('gain_units'), 'ne', r.get('ne'), 'idle', r.get('idle'), r.get('seconds'), 's', flush=True)
json.dump(dict(base_objective=base, results=res), open(sys.argv[3], 'w'), indent=1)
