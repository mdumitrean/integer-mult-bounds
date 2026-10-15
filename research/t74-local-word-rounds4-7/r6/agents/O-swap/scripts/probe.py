"""probe: base-word frames graph structure (components) and where the width-4/5 helper groups live."""
import os, sys, json, time, collections
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W
from model import cone_caps
from word import inline
import wcore as K
w = K.load(sys.argv[2]); costs = F.Costs(K.B); t0 = time.time()
caps, comp = cone_caps(w)
g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
print('graph', f'{time.time()-t0:.1f}s', 'nodes', len(g.nodes), 'vars', len(g.var), 'components', len(g.components), 'sizes', [len(c) for c in g.components[:12]], flush=True)
compof = {}
for i, c in enumerate(g.components):
    for k in c: compof[k] = i
paid, centre, widths, starts, ends, endB = W.recount(w); v, R = w['report']['v'], w['report']['R']
typ = lambda q: (W.dimension(starts[q]), W.dimension(ends[q]))
groups = collections.defaultdict(list)
for q in range(2 * v, 2 * v + R):
    t = typ(q)
    if t == (5, 9): groups[('up-start', tuple(sorted(w['start_extra'][str(q)])))].append(q)
    if t == (0, 4): groups[('up-end', tuple(sorted(w['helper_final'][str(q)])))].append(q)
    if t == (4, 9): groups[('down', tuple(sorted(w['start_extra'][str(q)])))].append(q)
out = {}
for (kind, fr), mem in sorted(groups.items(), key=lambda x: x[1][0]):
    comps = collections.Counter(compof[k] for q in mem for k in g.chains[q] if k in compof)
    out[f'{kind}:{mem[0]}..{mem[-1]}'] = dict(members=mem, comps=dict(comps))
    print(kind, mem, 'components (index:count of chain vars):', dict(sorted(comps.items())[:10]))
t1 = time.time(); r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
print('solve', f'{time.time()-t1:.1f}s', 'cost', r['cost'], 'certified', r['certified'], dict(sorted(r['profile'].items())))
json.dump(dict(components=[len(c) for c in g.components], groups=out), open(sys.argv[3], 'w'), indent=1)
