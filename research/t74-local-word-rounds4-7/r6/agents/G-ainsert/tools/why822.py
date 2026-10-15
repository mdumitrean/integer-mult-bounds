"""why822.py: why is re-inserting B822's deleted read (531 += 351) not a candidate?  Checks each filter of sk4's
candidate rule at the positions where 351 holds its pre-deletion value (agent G-ainsert r6)."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk4 import PRound4
from sk3 import (H, F, Q, V, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, absorbable, hist_values, proj, isport)
from cone import LU
word, outp = sys.argv[1:3]
P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base); dels = [('B', 822)]
W1 = compile_AB(P.base, dict(delete=dels)); g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); NA, NC, NB = sec_sizes(W1); seq = fullseq(W1)
nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq))
fam, _ = family_values(seq, {531, 351}, nreg, 1)
Rd = PRound4(P, W1, base_maps, orc, lambda i: i, fam, 3.0, None, orc_secs=sec_sizes(W1), ab=ab); lu = LU(P, W1)
win = hist_values(seq, nreg); p0 = NA + NC + 822; out = []
# 351's value windows around the deletion point, and 531's column there
for a, b, val in win[351]:
    if a <= p0 + 2 and b >= p0 - 2:
        coN = Rd.bN.coords(val); pv = proj(val, ab); coP = Rd.bP.coords(pv) if pv else None
        out.append(dict(window=[a, b], val=str(val)[:200], coN=str(coN), proj_val=str(pv)[:200], coP=str(coP)))
# 531's column at p0 (backward propagation, as in sk4)
cols = {}; SF = lambda x: cols.get(x, {x: Q(1)})
for i in range(len(seq) - 1, p0 - 1, -1):
    e = seq[i]
    if e[0] == 'add':
        t, s = e[1], e[2]; c = Q(e[3], e[4]); a_ = dict(SF(s))
        for k, vv in SF(t).items():
            a_[k] = a_.get(k, 0) + c * vv
            if not a_[k]: del a_[k]
        cols[s] = a_
    else: x = e[1]; cols[x] = {k: vv * Q(e[2], e[3]) for k, vv in SF(x).items()}
c531 = SF(531); vN = {k: v for k, v in c531.items() if not isport(k)}; vP = {k: v for k, v in c531.items() if isport(k)}
res = dict(ddel=ddel, p0=p0, windows_351=out, col531_nonport=str(vN)[:300], col531_port=str(vP)[:300],
           cost=orc.cost(531, 351, Rd.orcpos(p0)), cone_ok=lu.ok(531, 351, p0), TN=sorted(Rd.TN), TP=sorted(Rd.TP),
           TN_rows={str(k): str(v)[:160] for k, v in Rd.TN.items()})
json.dump(res, open(outp, 'w'), indent=1, default=str); print(json.dumps(res, default=str)[:2500])
