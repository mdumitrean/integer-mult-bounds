import os, sys, copy, json
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W, wcore as K, endnarrow as E
from model import cone_caps
w = K.load(sys.argv[2] + '/gauge44-word-566-554.json.gz'); P = E.prefinal(w)
out = {}
for q in (595, 603, 635):
    H = E.hyper_containing(P[q])[0]; w1 = copy.deepcopy(w); w1['helper_final'][str(q)] = H
    caps0, _ = cone_caps(w); caps1, _ = cone_caps(w1)
    newcaps = {k: (sorted(caps1[k]) if not isinstance(caps1[k], (list, tuple)) else len(caps1[k])) for k in caps1 if caps0.get(k) != caps1[k]}
    try:
        F.Graph(W.inline(w1, True), check_literal=False, tail_mutable=True, caps=caps1, cut_equality=True); why = 'feasible graph?'
    except F.Infeasible as e: why = str(e.args[0])[:300] if e.args else 'Infeasible'
    out[q] = dict(hyperplane=H, prefinal_dim=W.dimension(P[q]), changed_caps=len(newcaps), capped_registers=sorted(newcaps)[:12], reason=why)
    print(q, json.dumps(out[q])[:500])
json.dump(out, open(sys.argv[3], 'w'), indent=1)
