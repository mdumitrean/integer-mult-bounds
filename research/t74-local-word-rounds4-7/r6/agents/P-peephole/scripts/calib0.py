"""Calibration 0: identity window substitutions price at delta 0 (base word)."""
import os, sys, json, time
S = os.environ['SCR']; sys.path.insert(0, S + '/r3/toolkit-rev3')
import harness as H
t0 = time.time()
P = H.Pricer(S + '/r3/inputs/gauge44-word-566-554.json.gz', b='0.001679754956125544', check_literal=True, interval=True)
print('init', round(time.time() - t0, 1), 's base', P.base_cost, P.base_profile, flush=True)
B = P.base['B']; out = []
for i, k in ((0, 2), (100, 3), (857, 2), (1000, 4)):
    ed = dict(delete=list(range(i, i + k)), insert=[[i, list(B[j][:-1]) + [[]]] for j in range(i, i + k)])
    t1 = time.time(); r = P.price(ed, timeout=90)
    out.append(dict(window=[i, k], status=r.get('status'), delta=r.get('delta'), gain_certified=r.get('gain_certified'), seconds=round(time.time() - t1, 2)))
    print(out[-1], flush=True)
json.dump(out, open(S + '/r6/agents/P-peephole/out/CALIB0.json', 'w'), indent=1)
