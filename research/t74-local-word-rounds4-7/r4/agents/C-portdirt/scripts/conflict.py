"""conflict.py: minimal frame-conflicting subsets (deletion filter, agent B's minimal_conflict) for absorbed solutions.
usage: conflict.py WORD.json.gz SPARSE.json B_INDEX [N]"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); sys.path.insert(1, HERE)
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from conelu import feasible, minimal_conflict
P = H.Pricer(sys.argv[1], check_literal=True, interval=False); w = P.base
sol = [c for c in json.load(open(sys.argv[2]))['cands'] if c['B'] == int(sys.argv[3])][:int(sys.argv[4]) if len(sys.argv) > 4 else 3]
def build(W0, ins): return H.compile_edits(W0, dict(delete=[int(sys.argv[3])], insert=[(q, g) for q, g in ins]))
out = []
for c in sol:
    ins = [(int(q), list(g)) for q, g in c['ed']['insert']]
    ok, why = feasible(P, build(w, ins))
    js = minimal_conflict(P, w, ins, build) if not ok else []
    rec = dict(terms=c['terms'], feasible=ok, why=str(why)[:160], minimal_conflict=[c['terms'][j] for j in js])
    out.append(rec); print(rec, flush=True)
json.dump(out, open(os.path.join(os.path.dirname(sys.argv[2]), 'CONFLICT-B%s.json' % sys.argv[3]), 'w'), indent=1)
