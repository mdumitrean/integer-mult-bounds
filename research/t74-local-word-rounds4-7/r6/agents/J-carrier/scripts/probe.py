"""probe: dp, candidate counts, deleted/base costs and single costs of the base routing's own meets (calibration)."""
import sys, os, json, time
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
from jcommon import *
wname = sys.argv[1]; q = int(sys.argv[2])
t0 = time.time(); P = Pivot(wname, q)
C = P.candidates()
st, dcost = P.price([])
print('q', q, 'dp', P.dp, 'dfull', len(P.dfull), 'candidates', len(C), 'base', P.base_cost, 'deleted', st, dcost - P.base_cost if dcost else None, 'Lq dim', len(P.Lq('B', 0)), f'{time.time()-t0:.1f}s', flush=True)
cnt = collections.Counter(); 
for sec, pos, r, m in C:
    for i, y in enumerate(P.dp):
        if m >> i & 1: cnt[y] += 1
print('candidates per dp target', dict(cnt), flush=True)
