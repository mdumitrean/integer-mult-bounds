"""why_infeasible.py WORD OUT.json JOB R1 R2: rebuild a round-2 exact candidate and print the exact frame infeasibility reason."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import *
from runjob import exact
word, outp, J, I1, I2 = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
rec = json.load(open(outp))[J]; e2 = rec['round1'][I1]['round2'][I2]; P = H.Pricer(word); bm = maps(P.base)
mk = lambda gg: list(gg[:5]) + [[]]
W1 = compile_AB(P.base, dict(delete=[tuple(d) for d in rec['dels']]))
W2 = compile_AB(W1, word_seq_insert(W1, [(p, mk(g)) for p, g in e2['ins1']]))
W3 = compile_AB(W2, word_seq_insert(W2, [(p, mk(g)) for p, g in e2['ins2']]))
print('exact', exact(bm, W3), 'ins1', e2['ins1'], 'ins2', e2['ins2'])
caps, comp = cone_caps(W3); print('comp gates', len(comp), 'same as base', [list(e[:5]) for e in comp] == [list(e[:5]) for e in cone_caps(P.base)[1]])
try:
    g = F.Graph(inline(W3, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(W3, True), P.costs, check_literal=False, graph=g); print('feasible', r['cost'] - P.base_cost)
except F.Infeasible as e: print('Infeasible:', str(e.args[0])[:1200] if e.args else '')
