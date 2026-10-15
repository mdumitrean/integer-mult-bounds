"""diag.py (agent F-cpsat): is the late-B / tail conflict caused by narrowing + re-timing q's writes alone (no deliveries)?
For each (q,u): (a) narrowed word, writes in place; (b) narrowed, writes moved to t (no deliveries) for several t;
(c) un-narrowed, writes moved to t.  Reports the exact Graph outcome and, for failures, the conflicting node's registers,
lower and upper frames.  usage: diag.py WORD q:u[,...]"""
import copy, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
import zcore as Z, multi as M, solve_test as ST
def test(w, caps):
    try:
        g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True); return 'feasible', None
    except F.Infeasible as e: return 'infeasible', list(map(str, e.args[0][:4]))
W = Z.load(sys.argv[1]); out = []
for part in sys.argv[2].split(','):
    q, u = map(int, part.split(':')[:2])
    B = W['B']; reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]; t0 = min(reads); t_lim = ST.move_limit(W, q, t0)
    w0, _ = Z.build_at(W, q, [u], 0); caps, comp = cone_caps(w0)
    wn = copy.deepcopy(W); wn['start_extra'] = dict(W['start_extra']); wn['start_extra'][str(q)] = [u]
    row = dict(q=q, u=u, t_lim=t_lim, first_read=t0, narrowed_in_place=test(wn, caps))
    for t in sorted({0, t_lim // 4, t_lim // 2, (3 * t_lim) // 4, t_lim}):
        # moved writes only: a zero-coefficient delivery is not a gate, so build with an empty delivery list via a dummy
        w1, msg = M.build_multi(W, q, u, [(t, 112, 0)])
        if w1 is None: row['moved_%d' % t] = msg; continue
        w1['B'] = [e for e in w1['B'] if not (e[0] == 'add' and e[2] == q and e[3] == 0)]
        row['narrowed_moved_%d' % t] = test(w1, caps)
        w2, _ = M.build_multi(W, q, None, [(t, 112, 0)]); w2['B'] = [e for e in w2['B'] if not (e[0] == 'add' and e[2] == q and e[3] == 0)]
        row['plain_moved_%d' % t] = test(w2, cone_caps(w2)[0])
    out.append(row); print(json.dumps(row), flush=True)
