import os, sys, time, copy, json
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
import wcore as K
costs = F.Costs(K.B)
base = K.load(sys.argv[2] + '/gauge44-word-566-554.json.gz'); extra = K.load(sys.argv[2] + '/extra-word-566-554.json.gz')
t = time.time(); rb, gb, nc = K.solve(base, costs); tb = time.time() - t
print('base: cost', rb['cost'], 'certified', rb['certified'], 'profile', dict(sorted(rb['profile'].items())), 'comp', nc, f'{tb:.1f}s', flush=True)
t = time.time(); re_, ge, _ = K.solve(extra, costs); print('extra: cost', re_['cost'], 'delta', re_['cost'] - rb['cost'], 'certified', re_['certified'], dict(sorted(re_['profile'].items())), f'{time.time()-t:.1f}s', flush=True)
w = copy.deepcopy(base)
for q in ('627', '629', '630', '631'): w['start_extra'][q] = [1, 24, 34, 68]
t = time.time(); rv, gv, _ = K.solve(w, costs); print('base with extra start frames: cost', rv['cost'], 'delta', rv['cost'] - rb['cost'], 'certified', rv['certified'], dict(sorted(rv['profile'].items())), f'{time.time()-t:.1f}s', flush=True)
w1 = copy.deepcopy(base); w1['start_extra']['627'] = [1, 24, 34, 68]
t = time.time(); r1, _, _ = K.solve(w1, costs); print('single 627 upgrade: delta', r1['cost'] - rb['cost'], dict(sorted(r1['profile'].items())), f'{time.time()-t:.1f}s', flush=True)
