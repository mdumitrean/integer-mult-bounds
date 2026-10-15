"""calib_audit.py (agent F-cpsat): write back exact optimal frames into the multi-time constructor's calibration words
(q kept (9,0,9), deliveries at B0) and save them for the unchanged auditor.  usage: calib_audit.py WORD q:u[,...]"""
import gzip, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
from writeback import write_back
import zcore as Z, multi as M, solve_test as ST
W = Z.load(sys.argv[1]); costs = F.Costs(ST.BSTR)
for part in sys.argv[2].split(','):
    q, u = map(int, part.split(':')[:2])
    L, _ = Z.target_leak(W, q); d0 = Z.solve(Z.b_mixing_from(W, 0), L)
    w1, msg = M.build_multi(W, q, None, sorted((0, j, d) for j, d in d0.items()))
    caps, comp = cone_caps(w1)
    g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w1, True), costs, check_literal=False, graph=g)
    w2 = write_back(w1, g, r['assign'])
    p = os.path.join(HERE, '..', 'words', 'F-calib-%d-framed.json.gz' % q)
    open(p, 'wb').write(gzip.compress(json.dumps(w2, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    print(json.dumps(dict(q=q, cost=r['cost'], certified=r['certified'], comp=len(comp), comp_reads_q=sum(1 for e in comp if e[2] == q), word=os.path.basename(p))))
