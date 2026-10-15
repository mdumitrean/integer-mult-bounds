"""pairs.py: joint feasibility of every pair of port-source inserts (t += y, t += y', y != y' ports) on W = base - g.
For each insert j: LU of W + j (exact Graph), then the exact single-insert test of every other insert j' with a different
port source (position shifted past j).  If no pair is jointly feasible, every compensation of g that needs two distinct port
sources is frame-infeasible (inserts only add constraints).  usage: pairs.py WORD.json.gz CENSUS.json OUT.json B_INDEX"""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); sys.path.insert(1, HERE)
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from conelu import LU
P = H.Pricer(sys.argv[1], check_literal=True, interval=False); w = P.base; V = 112; NA, NC = len(w['A']), len(w['cut'])
i = int(sys.argv[4]); r = [x for x in json.load(open(sys.argv[2])) if x['B'] == i][0]; t, s = r['t'], r['s']
ins = [x for x in r['inserts'] if V <= x['y'] < 2 * V and x['y'] != s]
base_ed = lambda extra: dict(delete=[i], insert=[((q if q <= i else q + 1), ['add', t, y, 1, 1, []]) for y, q in extra])
t0 = time.time(); feasible_pairs = []; tested = 0; lu_fail = 0
for j, xj in enumerate(ins):
    Wj = H.compile_edits(w, base_ed([(xj['y'], xj['p'])]))
    try: lu = LU(P, Wj)
    except F.Infeasible: lu_fail += 1; continue
    for k in range(j + 1, len(ins)):
        xk = ins[k]
        if xk['y'] == xj['y']: continue
        q = xk['p']; q2 = q if q <= xj['p'] else q + 1       # W_j coordinates (j inserted before W index p_j)
        tested += 1
        if lu.ok(t, xk['y'], NA + NC + q2): feasible_pairs.append([xj['y'], xj['p'], xk['y'], xk['p']])
res = dict(B=i, t=t, s=s, port_inserts=len(ins), lu_fail=lu_fail, pairs_tested=tested, jointly_feasible_pairs=len(feasible_pairs),
           sample=feasible_pairs[:20], sec=round(time.time() - t0, 1))
json.dump(res, open(sys.argv[3], 'w'), indent=1); print({k: v for k, v in res.items() if k != 'sample'}, res['sample'][:5])
