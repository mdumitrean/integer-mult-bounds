"""calib.py WORD B_INDEX DEPTH OUT.json [--no-cone]: sk2.Round.candidates vs gen2.candidates_fast on round 1 of one deletion."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen2
from sk2 import H, F, Round, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, V
from cone import LU
word, bi, depth, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]; cone = '--no-cone' not in sys.argv
P = H.Pricer(word); base_maps = maps(P.base); dels = [('B', bi)]; W1 = compile_AB(P.base, dict(delete=dels))
g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); gg = seq0[NA + NC + bi]; regs = {gg[1], gg[2]}
nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
fam, famregs = family_values(fullseq(W1), regs, nreg, depth)
res = dict(word=os.path.basename(word), dels=dels, depth=depth, cone=cone, ddel=ddel)
def build(cls):
    R = cls(P, W1, base_maps, orc, lambda i: i, fam, 1.0, bud, orc_secs=sec_sizes(W1))
    if cone: R.lu = LU(P, W1)
    return R
t = time.time(); Rf = build(gen2.FastRound); cf = Rf.candidates(); res['fast'] = dict(n=len(cf), seconds=round(time.time() - t, 1), cone_rejected=Rf.cone_rejected)
print('fast', res['fast'], flush=True)
t = time.time(); Ro = build(Round); co = Ro.candidates(); res['sk2'] = dict(n=len(co), seconds=round(time.time() - t, 1), cone_rejected=getattr(Ro, 'cone_rejected', 0))
print('sk2', res['sk2'], flush=True)
same_order = len(co) == len(cf) and all(a == b for a, b in zip(co, cf))
key = lambda c: (c[0], tuple(sorted(c[3].items())), tuple(sorted(c[4][0].items())), tuple(sorted(c[4][1].items())))
so = {key(c): c for c in co}; sf = {key(c): c for c in cf}
res.update(identical_list=same_order, same_keys=set(so) == set(sf), same_cost_and_rep=all(so[k] == sf[k] for k in so if k in sf),
           only_sk2=len(set(so) - set(sf)), only_fast=len(set(sf) - set(so)))
if not same_order:
    diffs = [(i, a[:3] + (a[5],), b[:3] + (b[5],)) for i, (a, b) in enumerate(zip(co, cf)) if a != b][:5]; res['first_diffs'] = [str(d) for d in diffs]
print(json.dumps({k: v for k, v in res.items() if k not in ('fast', 'sk2')}), flush=True)
json.dump(res, open(out, 'w'), indent=1, default=str)
