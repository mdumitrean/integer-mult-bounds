"""R1: narrowed-inventory owner map without moving any role between bins.
Narrow helper HSTAR (9 -> 8) in both providers. In each call, swap helper ids between two of its width-9 roles so that
the narrowed role sits where freed cells concentrate; CP-SAT picks one width-9 role per call, minimizing the idle cost
sum_b c[rem_b] (concave), over every bin holding width-9 roles (48-bins: four 9s, 32-bins: two or three, 16-bins: one).
usage: fill_r1.py OUTDIR [HSTAR_REGISTER=478]"""
import collections, json, sys, time
from pathlib import Path
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
from ortools.sat.python import cp_model
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=False); REG = int(sys.argv[2]) if len(sys.argv) > 2 else 478; HS = REG - 224
C = {1: 2116454, 2: 4227983, 3: 6337656, 4: 8446126, 5: 10553701, 8: 16872596, 9: 18977915, 16: 33705925, 32: 67333407, 48: 100931344}
t0 = time.time(); L = X.load(); roles = L['roles']; A = L['A']; ctx = L['ctx']
assert all(L['widths'][p][HS] == 9 for p in L['widths']), 'helper must be width 9 in both providers'
bins = collections.defaultdict(list)
for i, z in enumerate(roles): bins[z['owner_replica'], z['child'], z['port']].append(i)
cap = {k: ctx['rank'][k[1]] for k in bins}
pat = {k: tuple(sorted(roles[i]['width'] for i in v)) for k, v in bins.items()}
cand = [k for k in bins if 9 in pat[k]]                    # every bin holding a width-9 role (16/32/48)
calls = sorted({(z['stage'], z['replica']) for z in roles})
m = cp_model.CpModel(); s = {}; byc = collections.defaultdict(list); lev = {}
for k in cand:
    vs = []
    for i in bins[k]:
        z = roles[i]
        if z['width'] == 9: v = m.NewBoolVar(''); s[i] = v; byc[z['stage'], z['replica']].append(v); vs.append(v)
    ys = [m.NewBoolVar('') for _ in range(len(vs) + 1)]; m.AddExactlyOne(ys); m.Add(sum(vs) == sum(r * ys[r] for r in range(len(ys)))); lev[k] = ys
for c in calls: m.AddExactlyOne(byc[c])
m.Minimize(sum(C[r] * lev[k][r] for k in cand for r in range(1, len(lev[k]))))
sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = 420; sol.parameters.num_workers = 1; st = sol.Solve(m)
print('cp', sol.StatusName(st), sol.ObjectiveValue(), sol.BestObjectiveBound(), round(time.time() - t0, 1), flush=True)
assert st in (cp_model.OPTIMAL, cp_model.FEASIBLE)
chosen = {i for i, v in s.items() if sol.Value(v)}
new = [dict(z) for z in roles]; at = collections.defaultdict(dict)
for i, z in enumerate(new): at[z['stage'], z['replica']][z['helper']] = i
for i in chosen:
    z = new[i]; c = (z['stage'], z['replica']); j = at[c][HS]
    if j != i: new[i]['helper'], new[j]['helper'] = HS, z['helper']; at[c][new[j]['helper']] = j; at[c][HS] = i
    new[i]['width'] = 8
assert sum(1 for z in new if z['helper'] == HS and z['width'] == 8) == len(calls)
for k, v in bins.items():                                   # re-stack contiguous prefixes in the original slice order
    off = 0
    for i in sorted(v, key=lambda i: roles[i]['offset']): new[i]['offset'] = off; off += new[i]['width']
    assert off <= cap[k]
idle = collections.Counter()
for k, v in bins.items():
    rem = cap[k] - sum(new[i]['width'] for i in v)
    if rem: idle[rem] += 1
for k in ctx['windows']:                                    # empty bins (no roles)
    pass
X.dump(OUT / 'OWNERS.json.gz', new)
res = dict(helper_register=REG, helper_index=HS, chosen=len(chosen), rem_hist=dict(collections.Counter(sum(1 for i in bins[k] if i in chosen) for k in cand)),
           cp_status=sol.StatusName(st), idle_cost=sol.ObjectiveValue(), bound=sol.BestObjectiveBound(), seconds=round(time.time() - t0, 1))
json.dump(res, open(OUT / 'FILL.json', 'w'), indent=1); print(json.dumps(res))
