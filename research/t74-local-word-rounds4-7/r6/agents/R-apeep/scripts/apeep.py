"""apeep.py: exact peephole equivalents of A-section windows (agent R-apeep, r6), adapted from r6 P-peephole's peep.py.

For a window W = A[i:i+k] on registers R (no A gate touches a port, so R has no port), its map is computed exactly.
Alternative sequences of length L <= Lmax over R (adds t += c s, c in +-{1/4,1/2,1,2,4}, t != s; scales by +-2, +-1/2, -1
only if W has a scale) with the same map are found by meet-in-the-middle in float64 (exact for these dyadics) and
re-verified in exact rationals.  Differences from peep.py: pure permutations of W (commuting reorders) are KEPT when
include_perm=True, because A-section reorders were only tried in two pivot blocks (r4 A-reroute, 459 moves); the
original sequence, consecutive same-(t,s) gates and scale/inverse-scale pairs are still excluded."""
import numpy as np
from fractions import Fraction as Q
V = 112
ADD_C = [Q(1, 4), Q(1, 2), Q(1), Q(2), Q(4), Q(-1, 4), Q(-1, 2), Q(-1), Q(-2), Q(-4)]
SCL_C = [Q(-2), Q(2), Q(-1, 2), Q(1, 2), Q(-1)]
def gt(g):
    return ('add', g[1], g[2], Q(g[3], g[4])) if g[0] == 'add' else ('scale', g[1], Q(g[2], g[3]))
def regs(t): return (t[1], t[2]) if t[0] == 'add' else (t[1],)
def isport(r): return V <= r < 2 * V
def mat(t, ix, n):
    M = np.eye(n)
    if t[0] == 'add': M[ix[t[1]], ix[t[2]]] += float(t[3])
    else: M[ix[t[1]], ix[t[1]]] = float(t[2])
    return M
def inv(t): return ('add', t[1], t[2], -t[3]) if t[0] == 'add' else ('scale', t[1], 1 / t[2])
def qmap(seq, R):
    ix = {r: j for j, r in enumerate(R)}; n = len(R)
    M = [[Q(int(a == b)) for b in range(n)] for a in range(n)]
    for t in seq:
        if t[0] == 'add':
            a, s = ix[t[1]], ix[t[2]]; M[a] = [M[a][j] + t[3] * M[s][j] for j in range(n)]
        else:
            a = ix[t[1]]; M[a] = [t[2] * x for x in M[a]]
    return M
def key(A): return (np.ascontiguousarray(A) + 0.0).tobytes()
def mergeable(a, b):
    if a[0] == 'add' and b[0] == 'add': return a[1] == b[1] and a[2] == b[2]
    if a[0] == 'scale' and b[0] == 'scale': return a[1] == b[1]
    return False
def equivalents(W, Lmax, max_n=8, include_perm=True):
    R = sorted({r for t in W for r in regs(t)}); n = len(R)
    if n > max_n: return None
    assert not any(isport(r) for r in R), 'A window touches a port'
    ix = {r: j for j, r in enumerate(R)}
    M = np.eye(n)
    for t in W: M = mat(t, ix, n) @ M
    singles = [('add', a, b, c) for a in R for b in R for c in ADD_C if a != b]
    if any(t[0] == 'scale' for t in W): singles += [('scale', a, c) for a in R for c in SCL_C]
    m = len(singles)
    Sm = np.stack([mat(t, ix, n) for t in singles]); Si = np.stack([mat(inv(t), ix, n) for t in singles])
    sols = set(); one = {}
    for a in range(m): one.setdefault(key(Sm[a]), []).append(a)
    for a in one.get(key(M), []): sols.add((singles[a],))
    if Lmax >= 2:
        PP = np.matmul(Sm[None, :, :, :], Sm[:, None, :, :]).reshape(m * m, n, n)   # [a*m+b] = S[b] @ S[a]
        pairs = {}
        for idx in range(m * m):
            a, b = divmod(idx, m)
            if mergeable(singles[a], singles[b]): continue
            pairs.setdefault(key(PP[idx]), []).append((a, b))
        for (a, b) in pairs.get(key(M), []): sols.add((singles[a], singles[b]))
        if Lmax >= 3:
            T = np.matmul(M[None], Si)
            for a in range(m):
                for (b, c) in pairs.get(key(T[a]), []):
                    if mergeable(singles[a], singles[b]): continue
                    sols.add((singles[a], singles[b], singles[c]))
        if Lmax >= 4:
            T2 = np.matmul(np.matmul(M[None], Si)[:, None, :, :], Si[None, :, :, :]).reshape(m * m, n, n)
            for idx in range(m * m):
                a, b = divmod(idx, m)
                if mergeable(singles[a], singles[b]): continue
                for (c, d) in pairs.get(key(T2[idx]), []):
                    if mergeable(singles[b], singles[c]): continue
                    sols.add((singles[a], singles[b], singles[c], singles[d]))
    orig = tuple(W); ms = sorted(map(str, W)); target = qmap(W, R); out = []
    for s in sols:
        if s == orig: continue
        perm = sorted(map(str, s)) == ms
        if perm and not include_perm: continue
        if any(mergeable(s[j], s[j + 1]) for j in range(len(s) - 1)): continue
        if qmap(s, R) != target: continue
        out.append((s, perm))
    return sorted(out, key=lambda x: (len(x[0]), str(x[0])))
