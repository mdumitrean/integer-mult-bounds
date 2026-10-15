"""acalib.py: calibration for the A-section peephole (agent R-apeep r6).
(1) identity substitutions of A windows (k = 2, 3, 4, nonzero frames) price ok at delta 0 with the compensation unchanged;
(2) r4 A-reroute's neutral re-timing 'A1248 to 1247' (adjacent swap of A1247/A1248, priced delta 0 there) is rediscovered by
apeep as a permutation equivalent of window [1247, 1248] and prices delta 0 here; (3) an inexact control (the window's
first gate dropped) is rejected as inexact."""
import os, sys, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import aprice, apeep
t0 = time.time(); aprice.init(); P = aprice.P
print('init', round(time.time() - t0, 1), 's base', P.base_cost, P.base_profile, 'comp', len(P.compensation), flush=True)
A = P.base['A']; out = []
nzw = [i for i in range(len(A) - 4) if all(A[j][-1] for j in range(i, i + 4))]
for i, k in ((nzw[10], 2), (nzw[len(nzw) // 2], 3), (nzw[-5], 4)):
    r = dict(i=i, k=k, alt=[list(map(str, apeep.gt(A[j]))) for j in range(i, i + k)], perm=False, nz=True, big=False)
    r['alt'] = [[x if not isinstance(y, apeep.Q) else str(y) for x, y in zip(map(str, t), t)] for t in [apeep.gt(A[j]) for j in range(i, i + k)]]
    r['alt'] = [[t[0], t[1], t[2], str(t[3])] if t[0] == 'add' else [t[0], t[1], str(t[2])] for t in [apeep.gt(A[j]) for j in range(i, i + k)]]
    t1 = time.time(); res = aprice.job(r); res['kind'] = 'identity'; out.append(res)
    print('identity', i, k, res['status'], res['delta'], res['comp_gates'], res['comp_changed'], res['seconds'], 's', flush=True)
Wn = [apeep.gt(A[1247]), apeep.gt(A[1248])]
alts = apeep.equivalents(Wn, 2, 8)
swap = (apeep.gt(A[1248]), apeep.gt(A[1247]))
found = [s for s, p in alts if s == swap]
print('window 1247-1248:', Wn, '->', len(alts), 'alternatives; swap rediscovered:', bool(found), flush=True)
if found:
    r = dict(i=1247, k=2, alt=[[t[0], t[1], t[2], str(t[3])] if t[0] == 'add' else [t[0], t[1], str(t[2])] for t in swap], perm=True, nz=True, big=False)
    res = aprice.job(r); res['kind'] = 'r4A-swap-1248-to-1247'; out.append(res); print('swap priced', res['status'], res['delta'], flush=True)
i = nzw[10]
r = dict(i=i, k=2, alt=[[t[0], t[1], t[2], str(t[3])] if t[0] == 'add' else [t[0], t[1], str(t[2])] for t in [apeep.gt(A[i + 1])]], perm=False, nz=True, big=False)
res = aprice.job(r); res['kind'] = 'inexact-control'; out.append(res); print('inexact control', res['status'], flush=True)
json.dump(dict(base_cost=P.base_cost, base_profile=P.base_profile, comp=len(P.compensation), runs=out), open(os.path.join(HERE, '..', 'out', 'CALIB.json'), 'w'), indent=1, default=str)
