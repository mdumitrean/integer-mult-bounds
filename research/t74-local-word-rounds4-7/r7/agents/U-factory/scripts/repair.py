"""repair.py: for a side-identity dump, solve whether each damaged target's missing clean contribution is a combination
of registers it may read legally (frame union inside the target's hyperplane), excluding entering helpers and the dropped
helper.  usage: repair.py DUMP.json DROPPED_HELPER ENTERING.json OUT.json"""
import json, sys
from fractions import Fraction as Q
V = 120  # factory numbering: v = 120 data lines; targets are v..2v
def basis(vectors):
    b = {}
    for x in vectors:
        for p in sorted(b, reverse=True):
            if x >> p & 1: x ^= b[p]
        if x:
            p = x.bit_length() - 1
            for q in b:
                if b[q] >> p & 1: b[q] ^= x
            b[p] = x
    return tuple(b[p] for p in sorted(b, reverse=True))
def inside(a, b): return basis(list(a) + list(b)) == tuple(b)
def solve(cols, target):
    """exact: find c with sum c_i cols_i == target (dict vectors); returns dict index->coef or None"""
    keys = sorted({k for c in cols for k in c} | set(target)); n = len(cols)
    A = [[cols[j].get(k, Q(0)) for j in range(n)] + [target.get(k, Q(0))] for k in keys]
    piv = []; r = 0
    for c in range(n):
        p = next((i for i in range(r, len(A)) if A[i][c]), None)
        if p is None: continue
        A[r], A[p] = A[p], A[r]; inv = 1 / A[r][c]; A[r] = [x * inv for x in A[r]]
        for i in range(len(A)):
            if i != r and A[i][c]:
                f = A[i][c]; A[i] = [x - f * y for x, y in zip(A[i], A[r])]
        piv.append(c); r += 1
    if any(A[i][n] for i in range(r, len(A))): return None
    return {piv[i]: A[i][n] for i in range(r) if A[i][n]}
d = json.load(open(sys.argv[1])); drop = int(sys.argv[2]); ent = set(json.load(open(sys.argv[3])))
regs = {int(r): dict(clean={int(k): Q(x) for k, x in z['clean'].items()}, frame=tuple(z['frame'])) for r, z in d['regs'].items()}
out = {}
for t, bad in d['bad'].items():
    t = int(t); need = {int(k): Q(x) for k, x in bad.items()}; H = tuple(d['hyper'][str(t)]); tf = tuple(d['targets'][str(t)]['frame'])
    cand = [r for r, z in regs.items() if r != drop and r not in ent and z['clean'] and inside(basis(list(tf) + list(z['frame'])), H)]
    sol = solve([regs[r]['clean'] for r in cand], need)
    if sol is None: out[t] = dict(feasible=False, candidates=len(cand), need=len(need))
    else:
        used = {cand[i]: str(c) for i, c in sol.items()}
        F = basis(list(tf) + [x for r in used for x in regs[r]['frame']])
        out[t] = dict(feasible=inside(F, H), reads=used, joint_frame_rank=len(F), target_frame_rank=len(tf), candidates=len(cand), need=len(need))
json.dump(out, open(sys.argv[4], 'w'))
print('damaged targets', len(out), '| individually repairable', sum(v['feasible'] for v in out.values()), '| reads needed', sum(len(v.get('reads', {})) for v in out.values()))
