"""retime_probe.py (agent F-cpsat): directive (b) probe.  Re-time q's late reads (B gates with source q) as late as exact
commutation allows (frames.move_window; processed last-to-first, windows recomputed after each move), so that every q-read
node sits where its partner register's upper frame is largest (uppers grow along chains), then recompute the screen3 bounds
on the bounding word and re-test condition (ii) + exact span.  Also records U* for each single partner of the first read.
usage: retime_probe.py WORD OUT SPEC"""
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
def retime_reads_late(Bl, q):
    Bl = list(Bl); moves = 0
    idxs = [i for i, e in enumerate(Bl) if e[0] == 'add' and e[2] == q]
    for i in sorted(idxs, reverse=True):
        cur = [k for k, e in enumerate(Bl) if e is Bl[i]][0] if False else i
        lo, hi = F.move_window(Bl, i)
        if hi > i: Bl = F.moved(Bl, i, hi); moves += 1
    return Bl, moves
W = Z.load(sys.argv[1]); rows = []
for part in sys.argv[3].split(','):
    q, u = map(int, part.split(':')[:2]); B0 = W['B']
    reads0 = [i for i, e in enumerate(B0) if e[0] == 'add' and e[2] == q]; t0 = min(reads0); t_lim = ST.move_limit(W, q, t0)
    w0, _ = Z.build_at(W, q, [u], 0); caps, comp = cone_caps(w0)
    srcs = sorted({e[2] for e in W['A'] if e[1] == q and e[0] == 'add'} | {e[2] for e in B0[:t_lim] if e[1] == q and e[0] == 'add'})
    Bn, moves = retime_reads_late(B0, q)
    assert sorted(map(json.dumps, Bn)) == sorted(map(json.dumps, B0))
    wt = copy.deepcopy(W); wt['B'] = Bn
    exact_map = Z.target_leak(wt, q)[0] == Z.target_leak(W, q)[0]
    reads1 = [i for i, e in enumerate(Bn) if e[0] == 'add' and e[2] == q]; t1 = min(reads1)
    qBw = [i for i, e in enumerate(Bn[:t_lim]) if e[1] == q]
    wr = copy.deepcopy(wt); wr['start_extra'] = dict(W['start_extra']); wr['start_extra'][str(q)] = [u]
    wr['A'] = [e for e in W['A'] if e[1] != q]; wr['B'] = [e for i, e in enumerate(Bn) if not (i < t_lim and e[1] == q)]
    shift = lambda t: t - sum(1 for i in qBw if i < t)
    try:
        g = SC.graph(wr, caps)
    except F.Infeasible as e:
        row = dict(q=q, u=u, read_moves=moves, status='bounding-word-infeasible', why=list(map(str, e.args[0][:4]))); rows.append(row); print(json.dumps(row)); continue
    bad = SC.bad_nodes(g, u); t_lim_r = shift(t_lim); win = SC.windows(g, bad, t_lim_r, len(wr['B']))
    lo = {y: t for y, t in win.items() if t is not None and t <= t_lim_r}
    kq = first_node_from(g, q, shift(t1)); Uq = set(F.span(g.upper[kq])); Ustar = set(Uq)
    for s in srcs: Ustar &= set(F.span(g.upper[first_node_from(g, s, t_lim_r)]))
    cols = SC.mixing_columns(wr, lo, t_lim_r); L, _ = Z.target_leak(W, q)
    keep = []; n = 0
    for j, cj in cols.items():
        if not cj: continue
        for t_e, t_l, key in ST.classes(cj, lo[j], t_lim_r):
            for t in sorted({t_e, t_l}):
                n += 1
                if set(F.span(tuple(EX.lower_before(g, j, t)) + (u,))) <= Ustar: keep.append(((j, t), dict(key)))
    ok, rank = SC.in_span([v for lab, v in keep], {y: -x for y, x in L.items()})
    row = dict(q=q, u=u, read_moves=moves, first_read_before=t0, first_read_after=t1, map_exact=exact_map,
               Uq_first_read_dim=len(F.basis(tuple(Uq))), Ustar_dim=len(F.basis(tuple(Ustar))) if Ustar else 0,
               windowed=len(lo), candidates=n, kept=len(keep), span_rank=rank, leak_cancellable=ok)
    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open(sys.argv[2], 'w'), indent=1)
