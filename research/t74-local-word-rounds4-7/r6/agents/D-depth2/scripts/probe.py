"""probe.py WORD B_INDEX DEPTH: sizes of the sk2 round-1 model inputs (family, basis, holder windows) and timings."""
import os, sys, time
TOOLS = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'r3', 'agents', 'B-interact', 'tools')
sys.path.insert(0, os.path.abspath(TOOLS))
from sk2 import H, F, Q, V, Round, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, hist_values
word, bi, depth = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); t0 = time.time()
P = H.Pricer(word); base_maps = maps(P.base); print('pricer', round(time.time()-t0, 1), flush=True)
dels = [('B', bi)]; W1 = compile_AB(P.base, dict(delete=dels))
g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); print('ddel', ddel, round(time.time()-t0, 1), flush=True)
NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); gg = seq0[NA + NC + bi]; regs = {gg[1], gg[2]}
nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
t1 = time.time(); fam, famregs = family_values(fullseq(W1), regs, nreg, depth); print('family depth', depth, 'regs', len(famregs), 'values', len(fam), round(time.time()-t1, 1), flush=True)
t1 = time.time(); R1 = Round(P, W1, base_maps, orc, lambda i: i, fam, 1.0, -ddel - 1, orc_secs=sec_sizes(W1))
print('basis', len(R1.basis.piv), 'residual rank', R1.nT, round(time.time()-t1, 1), flush=True)
t1 = time.time(); seq = fullseq(W1); win = hist_values(seq, nreg); nw = sum(len(v) for v in win.values()); nh = 0; npos = 0
for y, ws in win.items():
    for a, b, val in ws:
        if val and R1.basis.coords(val): nh += 1; npos += min(b, len(seq) + 1) - a
print('windows', nw, 'holder windows', nh, 'holder positions', npos, 'nreg', nreg, 'L', len(seq), round(time.time()-t1, 1), flush=True)
