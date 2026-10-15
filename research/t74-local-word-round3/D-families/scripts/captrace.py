"""captrace: for pivot q, delete all of q's B reads, take the deleted optimum's join of q's A frames (FAmax), and for every
B/tail meet of q in the BASE word, trace each vector of FAmax outside U(meet) to the chain of later meets that excludes it.
The gates on these blocking chains are the pre-edit targets of the two-column family.  usage: captrace.py WORD q [q...]"""
import sys, os, json, collections
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r2h'))
from common import *
P = H.Pricer(WORDS[sys.argv[1]], b=os.environ['IMB_B'], check_literal=True)
def solve(w):
    caps, comp = cone_caps(w)
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w, True), P.costs, check_literal=False, graph=g)
    Fr = lambda k: r['assign'][k] if k in g.varset else g.nodes[k][1]
    return g, r, Fr
g0, r0, F0 = solve(P.base); sp = lambda X: set(F.span(tuple(X)))
out = {}
for q in map(int, sys.argv[2:]):
    B = P.base['B']; reads = [i for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
    w1 = H.compile_edits(P.base, dict(delete=reads)); g1, r1, F1 = solve(w1)
    FA = [F1(k) for k in g1.chains[q] if g1.nodes[k][2] == 'A']; FAmax = F.basis(tuple(x for f in FA for x in f))
    rec = dict(reads=reads, deletion_delta=r1['cost'] - P.base_cost, FAmax=list(FAmax), meets=[])
    nxt = {}
    for r, ch in enumerate(g0.chains):
        for a, b in zip(ch, ch[1:]): nxt[a, r] = b
    def blame(k, x, depth=0):
        """first later vertices whose U excludes x, following every register of vertex k."""
        regs = g0.nodes[k][0]; path = []
        for r in regs:
            j = nxt.get((k, r))
            if j is None: continue
            if x not in sp(g0.upper[j]) or (g0.nodes[j][2] in ('end',) and x not in sp(g0.nodes[j][1])):
                n = g0.nodes[j]; desc = (n[2], n[3], (P.base['B'][n[3]][:5] if n[2] == 'B' else None), r)
                path.append(desc)
                if n[2] in ('B', 'tail') and depth < 6: path += blame(j, x, depth + 1)
        return path
    for k in g0.chains[q]:
        n = g0.nodes[k]
        if n[2] not in ('B', 'tail'): continue
        U = g0.upper[k]; ex = [x for x in FAmax if x not in sp(U)]
        m = dict(sec=n[2], idx=n[3], gate=(B[n[3]][:5] if n[2] == 'B' else None), U=list(U), excess=ex, blame={})
        for x in ex: m['blame'][x] = blame(k, x)[:8]
        rec['meets'].append(m)
        print(q, n[2], n[3], m['gate'], 'excess', ex, flush=True)
        for x, pth in m['blame'].items(): print('     vec', x, '<-', pth[:5], flush=True)
    out[q] = rec
json.dump(out, open(f'out/CAPTRACE-{sys.argv[1]}.json', 'w'), indent=1, default=str)
