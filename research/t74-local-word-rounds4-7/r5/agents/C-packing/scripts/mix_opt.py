"""Pattern relaxation with a menu of provider words: each word has a width inventory and a local cost relative to base.
Chooses the number of calls per word (sum 666) and bin patterns; minimizes local + idle cost.
usage: mix_opt.py WORDS.json OUT.json   (WORDS: {name: {"inv": {w: n}, "dcost": units/call vs base}})"""
import json, sys
from ortools.sat.python import cp_model
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from pcore import pats, NB, W, c, CUR
words = json.load(open(sys.argv[1]))
m = cp_model.CpModel(); n = {}
for cap in NB:
    for p, rem in pats(cap): n[cap, p] = m.NewIntVar(0, NB[cap], '')
    m.Add(sum(n[cap, p] for p, rem in pats(cap)) == NB[cap])
k = {nm: m.NewIntVar(0, 666, nm) for nm in words}; m.Add(sum(k.values()) == 666)
for w in W: m.Add(sum(v * kk[1].count(w) for kk, v in n.items()) == sum(k[nm] * words[nm]['inv'].get(str(w), 0) for nm in words))
m.Minimize(sum(k[nm] * words[nm]['dcost'] for nm in words) + sum(v * c[kk[0] - sum(kk[1])] for kk, v in n.items()))
s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 180; s.parameters.num_workers = 1; st = s.Solve(m)
out = dict(status=s.StatusName(st))
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    base_cost_rel = 0  # all dcost are relative to the base word
    out.update(calls={nm: s.Value(v) for nm, v in k.items()}, objective=s.ObjectiveValue(), bound=s.BestObjectiveBound(),
               gain_vs_current=CUR - s.ObjectiveValue(), kappa_estimate=(CUR - s.ObjectiveValue()) * 4.1e-8 / (1850 * 666),
               patterns={f'{kk[0]}:{list(kk[1])}+{kk[0]-sum(kk[1])}': s.Value(v) for kk, v in n.items() if s.Value(v)})
print(json.dumps({x: out[x] for x in out if x != 'patterns'}, indent=1)); json.dump(out, open(sys.argv[2], 'w'), indent=1)
