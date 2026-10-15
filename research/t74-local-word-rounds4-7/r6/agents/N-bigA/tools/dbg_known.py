import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk3 import *
from sk2 import hist_values
from cone import LU
word = sys.argv[1]; spec = json.load(open(sys.argv[2]))
P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base)
dels = [tuple(d) for d in spec['jobs'][0]]; W1 = compile_AB(P.base, dict(delete=dels))
g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
for s, i in dels: gg = seq0[NA + NC + i]; regs |= {gg[1], gg[2]}
nreg = 704; fam, famregs = family_values(fullseq(W1), regs, nreg, 1)
Rd = PRound(P, W1, base_maps, orc, lambda i: i, fam, 1.0, bud, orc_secs=sec_sizes(W1), ab=ab); lu = LU(P, W1)
print('ddel', ddel, 'TN', {k: dict(v) for k, v in list(Rd.TN.items())[:5]}, 'TP rows', len(Rd.TP), list(Rd.TP.items())[:3])
seq = Rd.seq; win = hist_values(seq, nreg)
for x, y, p, l in spec['known']['0']:
    val = next(v for a, b, v in win[y] if a <= p < b)
    coN = Rd.bN.coords(val); pv = proj(val, ab); coP = Rd.bP.coords(pv) if pv else None
    cst = orc.cost(x, y, Rd.orcpos(p)); ok = lu.ok(x, y, p)
    print('known', (x, y, p, l), 'val', dict(list(val.items())[:4]), 'coN', coN, 'coP', coP, 'cost', cst, 'budget', bud, 'cone ok', ok, 'orcpos', Rd.orcpos(p))
