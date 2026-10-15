"""variants: build interface variants of the base word with exact optimal frames written back.
  calib-g2-390: start frames of 627/629/630/631 lose 390 (the extra word's interface) -> must reproduce the extra word
  g1-alt: start frames of 619/621/622/623 lose 260 (same construction on group G1)
usage: variants.py TOOLKIT INPUTS OUTDIR"""
import os, sys, json, gzip, copy
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W, wcore as K
from writeback import write_back
INP, OUT = sys.argv[2], sys.argv[3]
base = K.load(INP + '/gauge44-word-566-554.json.gz'); extra = K.load(INP + '/extra-word-566-554.json.gz'); costs = F.Costs(K.B)
rb = K.solve(base, costs)[0]
V = {'calib-g2-390': ([627, 629, 630, 631], [1, 24, 34, 68]), 'g1-alt': ([619, 621, 622, 623], [1, 24, 96, 132])}
res = {}
for name, (mem, basis) in V.items():
    w = copy.deepcopy(base)
    for q in mem: w['start_extra'][str(q)] = basis
    r, g, nc = K.solve(w, costs); w2 = write_back(w, g, r['assign'])
    p = f'{OUT}/{name}.json.gz'; gzip.open(p, 'wt').write(json.dumps(w2, sort_keys=True))
    paid, centre, widths, starts, ends, endB = W.recount(w2)
    res[name] = dict(delta=r['cost'] - rb['cost'], certified=r['certified'], profile=w2['report']['local_profile'],
                     inventory=w2['report']['width_inventory'], comp_gates=nc)
    if name == 'calib-g2-390':
        same = {s: w2[s] == extra[s] for s in ('A', 'cut', 'B', 'cleanup', 'early_cleanup', 'start_extra', 'helper_final', 'precondition', 'centers', 'center_frames', 'ports')}
        diffB = [i for i, (x, y) in enumerate(zip(w2['B'], extra['B'])) if x != y]
        res[name].update(sections_equal_to_extra_word=same, B_gates_differing_from_extra=diffB[:20], n_B_diff=len(diffB))
    print(name, json.dumps(res[name])[:700], flush=True)
json.dump(res, open(OUT + '/VARIANTS.json', 'w'), indent=1, sort_keys=True)
