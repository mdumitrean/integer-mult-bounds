"""Count candidates of the toolkit's generic move classes on a word and time one base solve."""
import sys, time, json
sys.path.insert(0, sys.argv[1])
import harness as H, fusion as G, joint as J
from exchange import copy_pairs, movable_reads
w = H.load(sys.argv[2]); out = {}
B = w['B']; out['B_gates'] = len(B); out['B_adds'] = sum(1 for e in B if e[0] == 'add'); out['early_cleanup'] = len(w['early_cleanup']); out['cleanup'] = len(w['cleanup'])
out['start_extra'] = len(w['start_extra'])
cs = G.candidates(w); out['fusion_candidates'] = len(cs); out['fusion_targets'] = len({c['t'] for c in cs}); out['fusion_tAH'] = len({(c['t'], c['A'], c['H']) for c in cs})
P = copy_pairs(w); out['copy_pairs'] = len(P); mv = {h: movable_reads(w, h, r, i) for h, (r, i) in P.items()}
out['pairs_with_movable'] = sum(1 for v in mv.values() if v); out['movable_reads'] = sum(len(v) for v in mv.values())
for k, kw in (('joint_default', {}), ('joint_partial_after', dict(allow_partial=True, restores=("canon", "after")))):
    t0 = time.time(); out[k] = len(J.candidates(w, **kw)); out[k + '_s'] = round(time.time() - t0, 1)
t0 = time.time(); p = H.Pricer(w, b=sys.argv[3], interval=True); out['base_solve_s'] = round(time.time() - t0, 1)
out['base_cost'] = p.base_cost; out['base_profile'] = p.base_profile; out['base_certified'] = p.base_certified; out['base_interval_width_units'] = p.base_interval['width_units']
print(json.dumps(out))
