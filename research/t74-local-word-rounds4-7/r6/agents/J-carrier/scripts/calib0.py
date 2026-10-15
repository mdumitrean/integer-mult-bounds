"""calib0: find a never-written-after-A helper with a zero deletion screen and run the same skeleton search on it."""
import sys, os, json
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
from jcommon import *
import rbnb
w = H.Pricer(WORDS['base'], b=os.environ['IMB_B'], check_literal=True).base
wrB = {g[1] for g in w['cut'] + w['B']}; readB = collections.Counter(g[2] for g in w['B'] if g[0] == 'add')
cands = [r for r in sorted(readB) if r >= 224 and r not in wrB and any(g[1] == r for g in w['A']) and str(r) not in w['helper_final']]
found = None; tried = []
for r in cands[:40]:
    try:
        P = Pivot('base', r); st, c = P.price([]); d = c - P.base_cost if c is not None else None
    except AssertionError as e: continue
    tried.append((r, st, d))
    if st == 'ok' and d == 0 and P.dp: found = r; break
print('tried', tried[:12], 'found', found, flush=True)
json.dump(dict(tried=tried, found=found), open(os.path.join(JDIR, '..', 'out', 'CALIB0-scan.json'), 'w'))
if found is not None: rbnb.solve('base', found)
