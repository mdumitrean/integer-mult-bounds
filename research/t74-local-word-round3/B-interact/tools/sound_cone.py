"""sound_cone.py STEP0_WORD EDITS BASE_WORD: soundness of the local cone test (no false rejections):
(1) every insert of the feasible k554 kernel passes on the deleted step0 word; (2) re-inserting a deleted read passes."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import *
from cone import LU, feasible
step0, edits, base = sys.argv[1:4]
P0 = H.Pricer(step0); ed = json.load(open(edits)); ed = ed.get('edit', ed); print('edit keys', list(ed))
dels = [('B', i) for i in ed.get('delete', [])]; W1 = compile_AB(P0.base, dict(delete=dels)); lu = LU(P0, W1)
NA, NC = len(W1['A']), len(W1['cut']); dB = sorted(i for _, i in dels)
res = []
for p, g in ed.get('insert', []):
    q = NA + NC + p - sum(1 for t in dB if t < p)          # base B position -> W1 seq insertion point
    res.append(('B', p, g[1], g[2], lu.ok(g[1], g[2], q)))
NB = len(W1['B'])
for j, g in ed.get('tail', []): res.append(('tail', j, g[1], g[2], lu.ok(g[1], g[2], NA + NC + NB + j)))
print('k554 inserts:', res, '| all pass:', all(r[-1] for r in res))
P = H.Pricer(base); ok = []
for i in (783, 802, 1, 3, 8, 39, 44):
    W1b = compile_AB(P.base, dict(delete=[('B', i)])); lub = LU(P, W1b); g = P.base['B'][i]
    q = len(W1b['A']) + len(W1b['cut']) + i
    ok.append((i, lub.ok(g[1], g[2], q)))
print('re-insert deleted read at its slot passes:', ok)
