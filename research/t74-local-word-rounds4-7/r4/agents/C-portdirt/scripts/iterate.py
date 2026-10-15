"""iterate.py: conflict-cut loop for compensation-absorbed kernels of one deleted port read g (B index i).
CP-SAT: sum_j lam_j nonord(y_j@p_j) = nonord(c s@i) over the census's individually feasible inserts into t (no re-read of s),
|lam| <= 4 in quarter steps, <= MAXT terms, minimum support.  Each solution is set-tested exactly (Graph, base caps: these
compensation changes leave the caps unchanged); an infeasible set adds its minimal conflicting subset as a cut; a feasible
set is priced with the relaxed pricer checks (absorbed screen, compensation residual rules, recomputed caps, exact frames,
interval) and its support is cut.  usage: iterate.py WORD.json.gz CENSUS.json OUT.json B_INDEX [ITERS] [MAXT]"""
import json, os, sys, time, math
from fractions import Fraction as Fr
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); sys.path.insert(1, HERE)
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from conelu import feasible, minimal_conflict
from ortools.sat.python import cp_model
P = H.Pricer(sys.argv[1], check_literal=True, interval=True); w = P.base; V = 112
i = int(sys.argv[4]); ITERS = int(sys.argv[5]) if len(sys.argv) > 5 else 40; MAXT = int(sys.argv[6]) if len(sys.argv) > 6 else 10
r = [x for x in json.load(open(sys.argv[2])) if x['B'] == i][0]; t, s = r['t'], r['s']
ins = [(x['y'], x['p'], {int(k): Fr(a) for k, a in x['nv']}) for x in r['inserts'] if x['y'] != s]
tgt = {int(k): Fr(a) for k, a in r['target']}
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final'])); cold = low - ent
cols = sorted(set(tgt) | {k for _, _, nv in ins for k in nv}); lcm = 1
for v in [tgt] + [nv for _, _, nv in ins]:
    for a in v.values(): lcm = lcm * a.denominator // math.gcd(lcm, a.denominator)
Dd = 4; SC = lcm * Dd; m = cp_model.CpModel(); lam = []; z = []
for j in range(len(ins)):
    l = m.NewIntVar(-4 * Dd, 4 * Dd, ''); b = m.NewBoolVar('')
    m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b); lam.append(l); z.append(b)
for k in cols:
    terms = [lam[j] * int(nv[k] * lcm) for j, (_, _, nv) in enumerate(ins) if k in nv]
    rhs = tgt.get(k, Fr(0)) * SC
    if terms: m.Add(sum(terms) == int(rhs))
    elif rhs: m.AddBoolOr([])
m.Add(sum(z) <= MAXT); m.Minimize(sum(z))
def edit(sol): return dict(delete=[i], insert=[((p if p <= i else p + 1), ['add', t, y, l.numerator, l.denominator, []]) for y, p, l in sol])
def build(W0, extra): return H.compile_edits(W0, dict(delete=[i], insert=list(extra)))
log = []; t0 = time.time()
for it in range(ITERS):
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = 60; sv.parameters.num_workers = 1
    st = sv.Solve(m)
    if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): log.append(dict(it=it, stop=sv.StatusName(st))); break
    supp = [j for j in range(len(ins)) if sv.Value(z[j])]
    sol = [(ins[j][0], ins[j][1], Fr(sv.Value(lam[j]), Dd)) for j in supp]
    ed = edit(sol); W1 = H.compile_edits(w, ed); ok, why = feasible(P, W1)
    rec = dict(it=it, terms=[[y, p, str(l)] for y, p, l in sol], feasible=ok)
    if not ok:
        js = minimal_conflict(P, w, ed['insert'], build)
        cut = [supp[j] for j in js]; m.Add(sum(z[j] for j in cut) <= len(cut) - 1); rec['conflict'] = [rec['terms'][j] for j in js]
    else:
        m.Add(sum(z[j] for j in supp) <= len(supp) - 1)
        caps, comp = cone_caps(W1)
        rec['comp_changed'] = comp != P.compensation; rec['caps_changed'] = caps != P.caps
        rec['comp_residual_violation'] = any(e[2] in ent for e in comp) or any(e[1] in ent | cold or e[2] in ent | cold for e in comp)
        try:
            g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            res = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g, interval=True)
            rec.update(delta=res['cost'] - P.base_cost, certified=res['certified'], profile=dict(sorted(res['profile'].items())))
            cmp = P.compare(res['profile'], res['interval']); rec['gain_certified'] = cmp.get('gain_certified')
        except F.Infeasible as e: rec['priced'] = 'infeasible-with-new-caps'
    log.append(rec); print(json.dumps(rec)[:300], f'{time.time()-t0:.0f}s', flush=True)
json.dump(dict(B=i, t=t, s=s, inserts=len(ins), log=log), open(sys.argv[3], 'w'), indent=1)
