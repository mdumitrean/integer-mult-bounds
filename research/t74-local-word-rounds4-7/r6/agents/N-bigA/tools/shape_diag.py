"""shape_diag.py: for shape-infeasible jobs, list the target equations (basis vector, N/P, row) that have no candidate,
with the positions where that basis direction is held at all (agent G-ainsert r6).  usage: shape_diag.py WORD SPEC.json OUT.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import defaultdict
from sk4 import PRound4
from sk3 import (H, F, Q, V, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, absorbable, hist_values, proj)
from cone import LU
word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p))
P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base); out = []
for dels in spec['jobs']:
    dels = [tuple(d) for d in dels]; W1 = compile_AB(P.base, dict(delete=dels))
    g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
    r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
    orc = Orc(write_back(W1, g, r['assign']), P.costs.c)
    NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
    for s, i in dels: gg = seq0[i if s == 'A' else NA + NC + i]; regs |= {gg[1], gg[2]}
    nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
    fam, _ = family_values(fullseq(W1), regs, nreg, 1)
    Rd = PRound4(P, W1, base_maps, orc, lambda i: i, fam, 1.0, -ddel - 1, orc_secs=sec_sizes(W1), ab=ab)
    Rd.a_windows = [tuple(w) for w in spec.get('a_windows', [])]; Rd.lu = LU(P, W1); cand = Rd.candidates()
    Rd.model(12, lamr=16, lam_den=4)
    # rebuild eq/rhs keys to find unmatched ones
    eqs = set()
    for j, (x, y, i, (coN, coP), (vN, vP), cst) in enumerate(cand):
        if coN:
            for b in coN:
                for rr in vN: eqs.add((b, 'N', rr))
        if coP:
            for b in coP:
                for rr in vP: eqs.add((b, 'P', rr))
    missing = []
    for tag, T, B_ in (('N', Rd.TN, Rd.bN), ('P', Rd.TP, Rd.bP)):
        for rr, row in T.items():
            co = B_.coords(row)
            for b, cb in co.items():
                if cb and (b, tag, rr) not in eqs: missing.append((b, tag, rr, str(cb)))
    # where is each missing basis direction held (any register, any position)?
    win = hist_values(Rd.seq, Rd.nreg); held = defaultdict(list)
    for y, ws in win.items():
        for a_, b_, val in ws:
            if not val: continue
            coN = Rd.bN.coords(val)
            if coN:
                for b in coN:
                    held[('N', b)].append((y, a_, b_))
    rec = dict(dels=dels, ddel=ddel, shape=Rd.shape, ncand=len(cand), a_kept=Rd.a_kept, missing=missing[:20],
               held={f'{k[0]}{k[1]}': v[:12] for k, v in held.items() if any(m[0] == k[1] and m[1] == k[0] for m in missing)},
               target_rows={'N': sorted(Rd.TN), 'P': sorted(Rd.TP)}, NA=Rd.NA, NC=Rd.NC, NB=Rd.NB)
    out.append(rec); print(dels, 'shape', Rd.shape, 'missing', missing[:6], flush=True)
json.dump(out, open(out_p, 'w'), indent=1, default=str)
