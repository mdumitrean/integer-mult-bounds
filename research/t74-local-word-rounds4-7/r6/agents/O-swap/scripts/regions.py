"""regions: for each single width change Z (narrowing 5->4 of one (4,9) helper at its feasible basis, or widening 4->5 of one
(5,9)/(0,4) helper at one option), the node region it can influence: nodes whose (L, U) differ from the base graph, plus every
frames-graph component (of Z's graph) containing such a node, plus one chain hop.  Two changes whose regions are disjoint
are priced additively by optimal_frames (separable components), so only overlapping pairs need a joint re-price.
usage: regions.py TOOLKIT WORD.json.gz SWEEP.jsonl OUT.json   (4 workers, per-task deadline, RSS check)"""
import os, sys, json, time, copy, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
from model import cone_caps
from word import inline
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, SWEEP, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
BASE = L0 = U0 = V0 = None
def graph(w):
    caps, comp = cone_caps(w)
    return F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
def init():
    global BASE, L0, U0, V0
    BASE = K.load(WORD); g = graph(BASE); L0, U0, V0 = g.lower, g.upper, g.varset
def run(task):
    q, kind, basis, delta = task; w = copy.deepcopy(BASE)
    (w['helper_final'] if kind == 'up-end' else w['start_extra'])[str(q)] = basis
    try:
        with deadline(60):
            g = graph(w)
    except F.Infeasible: return dict(q=q, kind=kind, basis=basis, status='infeasible')
    except Timeout: return dict(q=q, kind=kind, basis=basis, status='timeout')
    changed = {k for k in range(len(g.nodes)) if g.lower[k] != L0[k] or g.upper[k] != U0[k] or ((k in g.varset) != (k in V0))}
    comp_of = {}
    for i, c in enumerate(g.components):
        for k in c: comp_of[k] = i
    region = set(changed)
    for i in {comp_of[k] for k in changed if k in comp_of}: region.update(g.components[i])
    hop = set(region)
    for k in region:
        for r in g.nodes[k][0]:
            for nb in (g.prev.get((k, r)), g.nxt.get((k, r))):
                if nb is not None: hop.add(nb)
    out = dict(q=q, kind=kind, basis=basis, delta=delta, status='ok', changed=len(changed), region=sorted(hop))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    rows = [json.loads(l) for l in open(SWEEP) if l.strip()]
    T = [(r['q'], r['kind'], r['basis'], r['delta']) for r in rows if r['status'] in ('ok', 'uncertified')]
    print('single changes', len(T), flush=True); t0 = time.time(); res = []
    with mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=100) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=8), 1):
            res.append(r)
            if n % 200 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    json.dump(res, open(OUT, 'w')); print('done', len(res), f'{time.time()-t0:.0f}s', flush=True)
