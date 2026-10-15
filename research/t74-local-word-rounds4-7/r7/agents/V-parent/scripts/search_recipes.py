"""V-parent: search nine-stage parent recipes that satisfy global_k.py's integer identity (8 banks X0,Y0..X3,Y3; local
forward Y_p += X_p, reverse X_p -= Y_p; bridge (d,s,c): X_d += c X_s and Y_s -= c Y_d; final exchange (X_j,Y_j)->(Y_j,-X_j);
total must be the identity and every one of the 18 bridge shears necessary), and report their idle-run geometry
(uses = own calls + both pairs of every bridge, as PR1319's make_context marks them).
Family: given call order (stage -> pair, orientation), choose 3 calls to conjugate (bridge +c before, -c after, src != own),
then 3 final bridges before the exchange (solved by table lookup)."""
import itertools, json, sys
from collections import Counter, defaultdict
K = 4; N = 2 * K
def eye(): return tuple(tuple(int(i == j) for j in range(N)) for i in range(N))
def addrow(Z, d, s, c):
    Z = [list(r) for r in Z]; Z[d] = [x + c * y for x, y in zip(Z[d], Z[s])]; return Z
def as_t(Z): return tuple(tuple(r) for r in Z)
def ev_local(Z, p, rev): return addrow(Z, 2 * p, 2 * p + 1, -1) if rev else addrow(Z, 2 * p + 1, 2 * p, 1)
def ev_bridge(Z, d, s, c, skip=None, k=[0]):
    Z = addrow(Z, 2 * d, 2 * s, c); Z = addrow(Z, 2 * s + 1, 2 * d + 1, -c); return Z
def ev_exchange(Z):
    Z = [list(r) for r in Z]
    for j in range(K): Z[2 * j], Z[2 * j + 1] = Z[2 * j + 1], [-x for x in Z[2 * j]]
    return Z
def run(events, skip=-1):
    Z = [list(r) for r in eye()]; cnt = 0
    for e in events:
        if e[0] == 'L': Z = ev_local(Z, e[1], e[2])
        elif e[0] == 'B':
            d, s, c = e[1], e[2], e[3]
            if cnt != skip: Z = addrow(Z, 2 * d, 2 * s, c)
            cnt += 1
            if cnt != skip + 1 or skip < 0: pass
            if cnt - 1 != skip - 1 or True:
                pass
            # second shear
            if cnt != skip: Z = addrow(Z, 2 * s + 1, 2 * d + 1, -c)
            cnt += 1
        else: Z = ev_exchange(Z)
    return as_t(Z), cnt
def run_shears(events, skip):
    Z = [list(r) for r in eye()]; cnt = 0
    for e in events:
        if e[0] == 'L': Z = ev_local(Z, e[1], e[2])
        elif e[0] == 'B':
            d, s, c = e[1], e[2], e[3]
            for (x, y, sg) in ((2 * d, 2 * s, c), (2 * s + 1, 2 * d + 1, -c)):
                if cnt != skip: Z = addrow(Z, x, y, sg)
                cnt += 1
        else: Z = ev_exchange(Z)
    return as_t(Z), cnt
def geometry(events):
    lvl = -1; own = defaultdict(set); uses = defaultdict(list); L = 0
    for e in events:
        if e[0] == 'L': lvl += 1; own[e[1]].add(lvl); L += 1
        elif e[0] == 'B': uses[e[1]].append(lvl + 0.5); uses[e[2]].append(lvl + 0.5)
    runs = {}
    for p in range(K):
        r = []; cur = 0
        for l in range(L):
            if l in own[p]:
                if cur: r.append(cur); cur = 0
                continue
            if cur and any(abs(u - (l - 0.5)) < 1e-9 for u in uses[p]): r.append(cur); cur = 0
            cur += 1
        if cur: r.append(cur)
        runs[p] = tuple(r)
    return runs
# table of products of 3 final bridges (applied in order b1, b2, b3) -> list of triples
BR = [(d, s, c) for d in range(K) for s in range(K) if s != d for c in (1, -1)]
def mat_of(events):
    return run_shears(events, -1)[0]
def compose_final(Zpre_inv_target):
    pass
def main(order_spec):
    calls = [tuple(x) for x in order_spec]          # (pair, rev) per stage in time order
    # target for final three bridges B: E * B3 B2 B1 * Mpre = I  =>  B3 B2 B1 = E^{-1} Mpre^{-1}; compute by brute force table
    table = {}
    for trip in itertools.product(BR, repeat=3):
        ev = [('B',) + b for b in trip]
        table.setdefault(run_shears(ev, -1)[0], []).append(trip)
    Einv = None
    found = []
    idx = range(len(calls))
    for conj in itertools.combinations(idx, 3):
        for srcs in itertools.product(range(K), repeat=3):
            if any(srcs[i] == calls[conj[i]][0] for i in range(3)): continue
            for coefs in itertools.product((1, -1), repeat=3):
                pre = []
                for t, (p, rev) in enumerate(calls):
                    if t in conj:
                        i = conj.index(t); pre.append(('B', p, srcs[i], coefs[i])); pre.append(('L', p, rev)); pre.append(('B', p, srcs[i], -coefs[i]))
                    else: pre.append(('L', p, rev))
                # need X such that exchange * X * pre = I, X = product of 3 bridges: find X by solving: X = E^-1 * pre^-1
                # brute: try all triples via table keyed by X matrix: compute X by inverting numerically (integer, unimodular)
                Mpre = run_shears(pre, -1)[0]
                X = solve_X(Mpre)
                if X is None or X not in table: continue
                for trip in table[X]:
                    events = pre + [('B',) + b for b in trip] + [('X',)]
                    Z, nb = run_shears(events, -1)
                    if Z != eye(): continue
                    if any(run_shears(events, k)[0] == eye() for k in range(nb)): continue   # every shear necessary
                    found.append(dict(conj=[(conj[i], srcs[i], coefs[i]) for i in range(3)], final=list(trip), runs=geometry(events)))
    return found
import fractions
def inv(Z):
    n = len(Z); A = [[fractions.Fraction(Z[i][j]) for j in range(n)] + [fractions.Fraction(int(i == j)) for j in range(n)] for i in range(n)]
    for c in range(n):
        p = next(r for r in range(c, n) if A[r][c] != 0); A[c], A[p] = A[p], A[c]
        pv = A[c][c]; A[c] = [x / pv for x in A[c]]
        for r in range(n):
            if r != c and A[r][c] != 0:
                f = A[r][c]; A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return [[A[i][n + j] for j in range(n)] for i in range(n)]
EINV = None
def solve_X(Mpre):
    global EINV
    if EINV is None: EINV = inv(run_shears([('X',)], -1)[0])
    Mi = inv(Mpre)
    X = [[sum(EINV[i][k] * Mi[k][j] for k in range(N)) for j in range(N)] for i in range(N)]
    if any(x.denominator != 1 for r in X for x in r): return None
    return tuple(tuple(int(x) for x in r) for r in X)
if __name__ == '__main__':
    current = [(0, False), (0, True), (0, False), (1, True), (1, False), (2, True), (2, False), (3, True), (3, False)]
    found = main(current)
    cur_runs = {0: (6,), 1: (2, 1, 4), 2: (4, 1, 2), 3: (6, 1)}
    geoms = Counter(json.dumps({str(k): v for k, v in f['runs'].items()}) for f in found)
    print('identity recipes found (current stage order):', len(found)); print('distinct geometries:', len(geoms))
    for g, n in geoms.most_common(): print('  ', n, g)
    json.dump(dict(order=current, found=found[:5000], geometries=dict(geoms)), open(sys.argv[1], 'w'), indent=0)
