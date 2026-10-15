"""export_pair.py WORD DELS OUTDIR [AWIN_LO AWIN_HI] (agent Q-blocks, r6; from M-bigB's export_sys.py): build the projected split-key round-1 model for a set of deleted gates (DELS = "B1439,B1440"; optional A-section insert window in BASE A indices via sk6.PRound6), with every deleted (target, source) pair banned.
Original: build sk5's projected split-key round-1 model for one deleted B read
(cone-aware, sentinel inserts kept at cost 0, deleted pair banned, quarter-step lambda |lambda| <= 4, <= 12 inserts,
budget -ddel - 1) and save its exact integer equations in r6 I-resolve's rowgen.py format (OUTDIR/system.npz + out.json).
rowgen.py with ROWGEN_BAN=0 then solves growing row restrictions: each is a relaxation of the run5 model (which only adds
lazy cuts), so INFEASIBLE on any restriction proves the run5 model infeasible."""
import json, math, os, sys, time
from fractions import Fraction as Q
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, '..', '..', 'M-bigB', 'scripts')); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))
from sk5 import PRound5
from sk6 import PRound6
from sk3 import H, F, V, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, absorbable
from cone import LU
word, dspec, outd = sys.argv[1], sys.argv[2], sys.argv[3]; os.makedirs(outd, exist_ok=True); t0 = time.time()
awin = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else None
P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base); dels = [(d[0], int(d[1:])) for d in dspec.split(',')]
W1 = compile_AB(P.base, dict(delete=dels))
g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); dg = set(); regs = set()
for s_, i_ in dels:
    gg = seq0[i_ if s_ == 'A' else NA + NC + i_]; regs |= {gg[1], gg[2]}; dg.add((gg[1], gg[2]))
nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
fam, famregs = family_values(fullseq(W1), regs, nreg, 1)
Rd = (PRound6 if awin else PRound5)(P, W1, base_maps, orc, lambda i: i, fam, 1.0, bud, orc_secs=sec_sizes(W1), ab=ab)
if awin:
    nAd = lambda b: sum(1 for s_, i_ in dels if s_ == 'A' and i_ < b); Rd.a_windows = [(max(0, awin[0] - nAd(awin[0])), min(len(W1['A']), awin[1] - nAd(awin[1])))]
Rd.lu = LU(P, W1); cand = Rd.candidates()
Rd.cand = cand = [c for c in cand if (c[0], c[1]) not in dg]
Rd.model(12, lamr=16, ban='none', lam_den=4)
# rebuild the integer equations exactly as sk3.PRound.model does
from collections import defaultdict
eqs = defaultdict(list); rhs = {}; Dn = 4
for j, (x, y, i, (coN, coP), (vN, vP), cst) in enumerate(cand):
    if coN:
        for b, cb in coN.items():
            for rr, val in vN.items(): eqs[(b, 'N', rr)].append((j, cb * val))
    if coP:
        for b, cb in coP.items():
            for rr, val in vP.items(): eqs[(b, 'P', rr)].append((j, cb * val))
for tag, T, B_ in (('N', Rd.TN, Rd.bN), ('P', Rd.TP, Rd.bP)):
    for rr, row in T.items():
        co = B_.coords(row)
        for b, cb in co.items(): rhs[(b, tag, rr)] = cb
keys = sorted(set(eqs) | set(rhs), key=str); kid = {k: n for n, k in enumerate(keys)}
lcm = 1
for k in keys:
    for _, val in eqs.get(k, []): lcm = lcm * Q(val).denominator // math.gcd(lcm, Q(val).denominator)
    q = Q(rhs.get(k, 0)).denominator; lcm = lcm * q // math.gcd(lcm, q)
SC = Dn * lcm; E, C, J = [], [], []
for k in keys:
    for j, val in eqs.get(k, []):
        c = Q(val) * SC; assert c.denominator == 1; E.append(kid[k]); C.append(int(c)); J.append(j)
rhs_e = {}
for k, v in rhs.items():
    rv = Q(v) * Dn * SC; assert rv.denominator == 1
    if rv: rhs_e[kid[k]] = int(rv)
assert max((abs(c) for c in C), default=0) < 2 ** 62 and max((abs(v) for v in rhs_e.values()), default=0) < 2 ** 62
E = np.array(E, np.int64); C = np.array(C, np.int64); J = np.array(J, np.int64); o = np.lexsort((J, E)); E, C, J = E[o], C[o], J[o]
costs = np.array([int(c_[5]) for c_ in cand], np.int64)
candmeta = np.array([(int(c_[0]), int(c_[1]), int(c_[2]), int(c_[5])) for c_ in cand], np.int64)
np.savez(os.path.join(outd, 'system.npz'), E=E, C=C, J=J, costs=costs, rhs_ids=np.array(list(rhs_e), np.int64),
         rhs_vals=np.array(list(rhs_e.values()), np.int64), candmeta=candmeta)
meta = dict(word=os.path.basename(word), dels=dels, a_window=awin, ddel=int(ddel), bud=int(bud), ncand=len(cand), lamr=16, maxterms=12,
            lam_den=4, SC=SC, rows=len(keys), rhs_rows=len(rhs_e), nterms=int(len(E)), shape=Rd.shape,
            sentinel_kept=Rd.sentinel_kept, model=('sk6 A-window' if awin else 'sk5') + ' projected, deleted pairs banned, sentinels at 0', seconds=round(time.time() - t0, 1))
json.dump(dict(meta=meta), open(os.path.join(outd, 'out.json'), 'w'), indent=1); print('system', json.dumps(meta), flush=True)
