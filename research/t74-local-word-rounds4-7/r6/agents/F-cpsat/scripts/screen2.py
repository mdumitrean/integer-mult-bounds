"""screen2.py (agent F-cpsat): sharper necessary screen.  A delivery (j, t) joins L_j(t-) into q's frame, which then reaches
q's re-timed writes (sources s) and q's first read.  Frames only grow along chains and uppers are meets of successors, so a
feasible construction needs every delivery's L_j(t-) inside U* = U_q(first read node) meet U_s(first node at/after t_lim)
for every moved write's source s (largest possible t_last = t_lim gives the weakest, still necessary, test), in addition to
screen.py's u-closure windows.  Exact span test of -L over the surviving column classes.  usage: screen2.py WORD OUT SPEC"""
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from model import cone_caps
import zcore as Z, screen as SC, solve_test as ST, explore as EX
def first_node_from(g, r, t):
    for k in g.chains[r]:
        regs, F0, sec, idx = g.nodes[k]
        if (sec == 'B' and idx >= t) or sec in ('tail', 'end'): return k
    return g.chains[r][-1]
W = Z.load(sys.argv[1]); rows = []
for part in sys.argv[3].split(','):
    q, u = map(int, part.split(':')[:2])
    S = EX.setup(W, q, u); g = S['g']; B = W['B']
    reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]; t0 = min(reads)
    kq = first_node_from(g, q, t0)
    Ustar = set(F.span(g.upper[kq]))
    srcs = sorted({e[2] for e in W['A'] if e[1] == q and e[0] == 'add'} | {e[2] for e in B[:S['t_lim']] if e[1] == q and e[0] == 'add'})
    for s in srcs: Ustar &= set(F.span(g.upper[first_node_from(g, s, S['t_lim'])]))
    keep = []
    for (j, t), vec, dimL in S['cand']:
        Lj = EX.lower_before(g, j, t)
        if set(F.span(tuple(Lj) + (u,))) <= Ustar: keep.append(((j, t), vec))
    ok, rank = SC.in_span([v for lab, v in keep], {y: -x for y, x in S['L'].items()})
    row = dict(q=q, u=u, t_lim=S['t_lim'], first_read=t0, Ustar_dim=len(F.basis(tuple(Ustar))) if Ustar else 0, sources=srcs,
               candidates=len(S['cand']), kept=len(keep), kept_targets=sorted({j for (j, t), v in keep}), span_rank=rank,
               leak_cancellable=ok)
    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
