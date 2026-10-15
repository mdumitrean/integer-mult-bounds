"""screen3.py (agent F-cpsat): sound necessary screen for every exact direct-delivery construction of narrowed q.
Bounding word w_r = narrowed word with every write into q before t_lim REMOVED (frames only; not an exact word):
  - lowers of w_r at B times < t_lim are lower bounds of any construction's lowers before its deliveries (constructions only
    add joins: deliveries, and moved writes placed after the last delivery);
  - uppers of w_r at B nodes are upper bounds of any construction's uppers (constructions only add meets; removed nodes lie
    before them in time or in A);
  - caps = the caps of the exact t=0 construction (identical for every exact construction: same total map, same compensation).
Conditions, all necessary: (i) every node in the forward closure of the delivery's target successor accepts u;
(ii) L_j(t-) + u inside U* = U_q(first read) meet U_s(first node at/after t_lim) for every moved write's source s.
Then the exact span test of -L over all surviving (target, column class) candidates.  usage: screen3.py WORD OUT SPEC"""
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
    q, u = map(int, part.split(':')[:2]); B = W['B']
    reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]; t0 = min(reads); t_lim = ST.move_limit(W, q, t0)
    w0, _ = Z.build_at(W, q, [u], 0); caps, comp = cone_caps(w0)
    srcs = sorted({e[2] for e in W['A'] if e[1] == q and e[0] == 'add'} | {e[2] for e in B[:t_lim] if e[1] == q and e[0] == 'add'})
    qB_writes_before = [i for i, e in enumerate(B[:t_lim]) if e[1] == q]
    wr = copy.deepcopy(W); wr['start_extra'] = dict(W['start_extra']); wr['start_extra'][str(q)] = [u]
    wr['A'] = [e for e in W['A'] if e[1] != q]; wr['B'] = [e for i, e in enumerate(B) if not (i < t_lim and e[1] == q)]
    shift = lambda t: t - sum(1 for i in qB_writes_before if i < t)        # original B index -> w_r B index
    g = SC.graph(wr, caps); bad = SC.bad_nodes(g, u)
    t_lim_r = shift(t_lim); win = SC.windows(g, bad, t_lim_r, len(wr['B']))
    lo = {y: t for y, t in win.items() if t is not None and t <= t_lim_r}
    kq = first_node_from(g, q, shift(t0)); Ustar = set(F.span(g.upper[kq]))
    for s in srcs: Ustar &= set(F.span(g.upper[first_node_from(g, s, t_lim_r)]))
    cols = SC.mixing_columns(wr, lo, t_lim_r)      # w_r keeps every target-target gate (q's writes are not target gates)
    L, _ = Z.target_leak(W, q)
    keep = []; n_cand = 0
    for j, cj in cols.items():
        if not cj: continue
        for t_e, t_l, key in ST.classes(cj, lo[j], t_lim_r):
            for t in sorted({t_e, t_l}):
                n_cand += 1
                Lj = EX.lower_before(g, j, t)
                if set(F.span(tuple(Lj) + (u,))) <= Ustar: keep.append(((j, t), dict(key)))
    ok, rank = SC.in_span([v for lab, v in keep], {y: -x for y, x in L.items()})
    okw, rankw = SC.in_span([dict(c[1]) for j in cols for c in cols[j]], {y: -x for y, x in L.items()})
    row = dict(q=q, u=u, t_lim=t_lim, first_read=t0, q_B_writes_before_t_lim=len(qB_writes_before), sources=srcs,
               windowed_targets=len(lo), cancellable_with_windows_only=okw, Ustar_dim=len(F.basis(tuple(Ustar))) if Ustar else 0,
               candidates=n_cand, kept=len(keep), kept_targets=sorted({j for (j, t), v in keep}), span_rank=rank, leak_cancellable=ok)
    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
