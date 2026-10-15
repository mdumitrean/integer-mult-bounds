"""override.py SYSTEM_DIR SENTINEL.json OUT.json: map sentinel candidates (by x, y, p) in a U-variant system to their exact
standalone lower-bound costs; exclude those provably over budget (or frame-infeasible), as D-depth2's per-insert cap would.
Also writes SYSTEM_DIR/out.json from the run log if it is missing."""
import json, os, re, sys
import numpy as np
sd, sp, outp = sys.argv[1:4]
if not os.path.exists(os.path.join(sd, 'out.json')):
    line = [l for l in open(os.path.join(sd, 'log.txt')) if l.startswith('system ')][0]
    meta = json.loads(line[len('system '):line.rindex('}') + 1]); json.dump(dict(meta=meta), open(os.path.join(sd, 'out.json'), 'w'))
Z = np.load(os.path.join(sd, 'system.npz')); cm = Z['candmeta'].tolist(); sent = json.load(open(sp))
idx = {(x, y, p): j for j, (x, y, p, c) in enumerate(cm) if c >= 2 ** 59}
cost, excl, missing = {}, [], 0
for r in sent['rows']:
    j = idx.get((r['x'], r['y'], r['p']))
    if j is None: missing += 1; continue
    if r['provably_over_budget'] or r.get('lower') is None: excl.append(j)
    else: cost[j] = int(np.floor(r['lower']))
json.dump(dict(cost=cost, exclude=excl, missing=missing, n_sentinel_in_system=len(idx)), open(outp, 'w'), indent=1)
print('override', len(cost), 'priced', len(excl), 'excluded', missing, 'missing (deduplicated into a cheaper key)', len(idx), 'sentinel keys in system')
