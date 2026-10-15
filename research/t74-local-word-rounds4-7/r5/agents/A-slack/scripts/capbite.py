"""capbite.py: where do the solver's tail caps actually shrink an upper frame?  usage: capbite.py TOOLKIT WORD OUT.json"""
import gzip, json, sys
sys.path.insert(0, sys.argv[1])
import frames as F
from word import inline
from model import cone_caps
w = json.load(gzip.open(sys.argv[2])); caps, _ = cone_caps(w)
g1 = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True, tail_caps=True)
g0 = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True, tail_caps=False)
bite = []
for k, (regs, F0, sec, idx) in enumerate(g1.nodes):
    if g1.upper.get(k) != g0.upper.get(k) or g1.lower.get(k) != g0.lower.get(k):
        bite.append(dict(vertex=k, sec=sec, idx=idx, regs=list(regs), L=list(g1.lower[k]), U_capped=list(g1.upper[k]), U_free=list(g0.upper[k]),
                         dimU_capped=len(g1.upper[k]), dimU_free=len(g0.upper[k]), dimL=len(g1.lower[k])))
print('vertices whose bounds differ:', len(bite), {s: sum(1 for b in bite if b['sec'] == s) for s in {b['sec'] for b in bite}})
for b in bite[:8]: print(' ', b['sec'], b['idx'], b['regs'], 'dimL', b['dimL'], 'dimU capped', b['dimU_capped'], 'free', b['dimU_free'])
json.dump(dict(differing=len(bite), vertices=bite), open(sys.argv[3], 'w'), indent=1)
