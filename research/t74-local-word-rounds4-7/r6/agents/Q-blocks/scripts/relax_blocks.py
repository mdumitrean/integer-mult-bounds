"""relax_blocks.py (agent Q-blocks, r6): exact joint deletion relaxations (no compensation) for block deletions, priced like
run5/run4's ddel: compile_AB(delete=...) then certified optimal frames under the base caps (tail-mutable, cut equality).
usage: relax_blocks.py WORD JOBS.json OUT.json   (JOBS: [[["A", 1303], ["A", 1304]], ...])"""
import json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))
from sk3 import H, F, compile_AB, inline
word, jobs_p, out_p = sys.argv[1:4]; jobs = json.load(open(jobs_p)); t00 = time.time()
P = H.Pricer(word); res = []
print('base cost', P.base_cost, f'{time.time()-t00:.1f}s', flush=True)
for dels in jobs:
    dels = [tuple(d) for d in dels]; t0 = time.time(); rec = dict(dels=dels)
    try:
        W1 = compile_AB(P.base, dict(delete=dels))
        g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g)
        rec.update(status='ok' if r['certified'] else 'uncertified', ddel=r['cost'] - P.base_cost, profile=dict(sorted(r['profile'].items())))
    except F.Infeasible as e: rec.update(status='infeasible')
    except Exception as e: rec.update(status='error:' + repr(e)[:100])
    rec['seconds'] = round(time.time() - t0, 2); res.append(rec)
    print(rec['dels'][:3], len(dels), rec.get('status'), rec.get('ddel'), rec['seconds'], flush=True)
    json.dump(res, open(out_p, 'w'))
print('done', len(res), f'{time.time()-t00:.1f}s', flush=True)
