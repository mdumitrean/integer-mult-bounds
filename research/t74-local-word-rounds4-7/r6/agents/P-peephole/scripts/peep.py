"""peep.py: exact peephole equivalents of B windows (meet-in-the-middle over elementary dyadic gates).

For a window W = B[i:i+k] on registers R, its map M (|R| x |R|, applied in order: x <- G x) is computed exactly.
Alternative sequences of length L over R (adds t += c s with c in +-{1/4,1/2,1,2,4}, t != s, respecting the auditor's
'non-target reads target' rule; scales by +-2, +-1/2, -1 only if W has a scale) with the same map are found by
meet-in-the-middle on float64 (exact here: dyadic entries with small exponents) and re-verified in exact rationals.
Excluded: the original sequence, its permutations (commuting reorders, covered by #1957/r3), consecutive gates on the
same (t, s) (mergeable) and scale/inverse-scale pairs."""
import itertools, numpy as np
from fractions import Fraction as Q
V = 112
ADD_C = [Q(1, 4), Q(1, 2), Q(1), Q(2), Q(4), Q(-1, 4), Q(-1, 2), Q(-1), Q(-2), Q(-4)]
SCL_C = [Q(-2), Q(2), Q(-1, 2), Q(1, 2), Q(-1)]
def gt(g):   # canonical gate tuple
    return ('add', g[1], g[2], Q(g[3], g[4])) if g[0] == 'add' else ('scale', g[1], Q(g[2], g[3]))
def regs(t): return (t[1], t[2]) if t[0] == 'add' else (t[1],)
def legal(t):
    if t[0] == 'add':
        return t[1] != t[2] and not (V <= t[2] < 2 * V and not V <= t[1] < 2 * V)
    return True
def mat(t, ix, n, dtype=float):
    M = np.eye(n, dtype=dtype)
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
def equivalents(W, Lmax, max_n=8):
    """W: list of canonical gate tuples. Returns list of alternative sequences (tuples of gate tuples)."""
    R = sorted({r for t in W for r in regs(t)}); n = len(R)
    if n > max_n: return None
    ix = {r: j for j, r in enumerate(R)}
    M = np.eye(n)
    for t in W: M = mat(t, ix, n) @ M
    singles = [('add', a, b, c) for a in R for b in R for c in ADD_C if a != b]
    if any(t[0] == 'scale' for t in W): singles += [('scale', a, c) for a in R for c in SCL_C]
    singles = [t for t in singles if legal(t)]
    m = len(singles)
    Sm = np.stack([mat(t, ix, n) for t in singles]); Si = np.stack([mat(inv(t), ix, n) for t in singles])
    sols = set()
    one = {}
    for a in range(m): one.setdefault(key(Sm[a]), []).append(a)
    for a in one.get(key(M), []): sols.add((singles[a],))
    if Lmax >= 2 or Lmax >= 3:
        PP = np.matmul(Sm[None, :, :, :], Sm[:, None, :, :]).reshape(m * m, n, n)   # [a*m+b] = S[b] @ S[a]
        pairs = {}
        for idx in range(m * m):
            a, b = divmod(idx, m)
            if mergeable(singles[a], singles[b]): continue
            pairs.setdefault(key(PP[idx]), []).append((a, b))
        for (a, b) in pairs.get(key(M), []): sols.add((singles[a], singles[b]))
        if Lmax >= 3:
            T = np.matmul(M[None], Si)                       # M @ inv(G_a)
            for a in range(m):
                for (b, c) in pairs.get(key(T[a]), []):
                    if mergeable(singles[a], singles[b]): continue
                    sols.add((singles[a], singles[b], singles[c]))
        if Lmax >= 4:
            T2 = np.matmul(np.matmul(M[None], Si)[:, None, :, :], Si[None, :, :, :]).reshape(m * m, n, n)  # M Ga^-1 Gb^-1
            for idx in range(m * m):
                a, b = divmod(idx, m)
                if mergeable(singles[a], singles[b]): continue
                for (c, d) in pairs.get(key(T2[idx]), []):
                    if mergeable(singles[b], singles[c]): continue
                    sols.add((singles[a], singles[b], singles[c], singles[d]))
    orig = tuple(W); ms = sorted(map(str, W)); target = qmap(W, R); out = []
    for s in sols:
        if s == orig or sorted(map(str, s)) == ms: continue
        if any(mergeable(s[j], s[j + 1]) for j in range(len(s) - 1)): continue
        if qmap(s, R) != target: continue           # exact rational re-verification
        out.append(s)
    return sorted(out, key=lambda s: (len(s), str(s)))
