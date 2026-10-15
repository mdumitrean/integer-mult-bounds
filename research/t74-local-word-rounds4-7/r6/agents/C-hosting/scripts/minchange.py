"""Pattern level: the fewest bins that must change composition to reach a target gain with one width-9 helper narrowed
per word (base-n1 / extra-n1, free dispatch). Reuses r5 C-packing's pattern core (costs at b, bin counts).
usage: minchange.py OUT.json GAIN1 [GAIN2 ...]"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "r5/agents/C-packing/scripts"))
from pcore import pats, NB, W, c, CUR
from ortools.sat.python import cp_model
cur = {(8, (8,)): 41112, (8, (4, 4)): 8616, (16, (7, 9)): 20948, (16, (8, 8)): 12204, (32, (5, 9, 9, 9)): 30972,
       (32, (7, 7, 9, 9)): 2180, (48, (4, 8, 9, 9, 9, 9)): 10404, (48, ()): 22748}
words = {'base-n1': ({4: 44, 5: 44, 7: 38, 8: 115, 9: 239}, -2116454), 'extra-n1': ({4: 40, 5: 48, 7: 38, 8: 115, 9: 239}, 8458352 - 2116454)}
out = {}
for target in map(int, sys.argv[2:]):
    m = cp_model.CpModel(); n = {}; dpos = []
    for cap in NB:
        for p, rem in pats(cap):
            n[cap, p] = m.NewIntVar(0, NB[cap], ''); d = m.NewIntVar(0, NB[cap], ''); m.Add(d >= n[cap, p] - cur.get((cap, p), 0)); dpos.append(d)
        m.Add(sum(n[cap, p] for p, rem in pats(cap)) == NB[cap])
    k = {w: m.NewIntVar(0, 666, w) for w in words}; m.Add(sum(k.values()) == 666)
    for w in W: m.Add(sum(v * kk[1].count(w) for kk, v in n.items()) == sum(k[nm] * words[nm][0].get(w, 0) for nm in words))
    cost = sum(k[nm] * words[nm][1] for nm in words) + sum(v * c[kk[0] - sum(kk[1])] for kk, v in n.items())
    m.Add(cost <= CUR - target); m.Minimize(sum(dpos))
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 120; s.parameters.num_workers = 1; st = s.Solve(m)
    r = dict(status=s.StatusName(st))
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        r.update(changed_bins=int(s.ObjectiveValue()), bound=s.BestObjectiveBound(), gain=CUR - s.Value(cost), calls={nm: s.Value(v) for nm, v in k.items()},
                 delta={f'{kk[0]}:{list(kk[1])}': s.Value(v) - cur.get(kk, 0) for kk, v in n.items() if s.Value(v) != cur.get(kk, 0)})
    out[target] = r; print(target, json.dumps(r), flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
