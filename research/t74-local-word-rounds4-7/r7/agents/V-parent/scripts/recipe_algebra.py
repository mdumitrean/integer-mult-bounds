"""V-parent: the parent recipe as a linear map on the 8 half-blocks [X0,Y0,X1,Y1,X2,Y2,X3,Y3] (each block a scalar multiple
of the identity on its port/data space). Local call on pair p: forward Y_p += X_p, reverse X_p += Y_p (global_k.py mapper:
reverse swaps the two halves of the local word, whose map is second-half += first-half). Bridge: pair dst += c * pair src.
Usage: recipe_algebra.py TEMPLATE.json.gz  -> prints the global map of the template's recipe and its idle-run geometry."""
import gzip, json, sys
from fractions import Fraction as Q
N = 8
def eye(): return [[Q(int(i == j)) for j in range(N)] for i in range(N)]
def mul(A, B): return [[sum(A[i][k] * B[k][j] for k in range(N)) for j in range(N)] for i in range(N)]
def op_local(p, rev):
    E = eye(); x, y = 2 * p, 2 * p + 1
    if rev: E[x][y] += 1        # X_p += Y_p
    else:   E[y][x] += 1        # Y_p += X_p
    return E
def op_bridge(dst, src, c):
    E = eye()
    for h in (0, 1): E[2 * dst + h][2 * src + h] += Q(c)
    return E
def apply_recipe(recipe):
    G = eye()
    for e in recipe:
        if e['kind'] == 'local': G = mul(op_local(e['pair'], e['reverse']), G)
        elif e['kind'] == 'bridge': G = mul(op_bridge(e['dst'], e['src'], e['coefficient']), G)
    return G
def geometry(recipe, K=4):
    """Idle runs per pair: levels = local calls in time order; a pair is 'used' at its own calls and at bridges touching it
    (src or dst, as PR1319's make_context marks both). Runs are maximal stretches of other pairs' levels with no use."""
    levels = [e for e in recipe if e['kind'] == 'local']; L = len(levels)
    # use[p] = list of (time) where time is a half-step: level index for calls, level-0.5 style for bridges between calls
    t = 0.0; uses = {p: [] for p in range(K)}; own = {p: set() for p in range(K)}; lvl = -1
    for e in recipe:
        if e['kind'] == 'local':
            lvl += 1; own[e['pair']].add(lvl); uses[e['pair']].append(lvl)
        elif e['kind'] == 'bridge':
            uses[e['dst']].append(lvl + 0.5); uses[e['src']].append(lvl + 0.5)
    runs = {}
    for p in range(K):
        cut = sorted(set(uses[p])); r = []; cur = 0
        for l in range(L):
            if l in own[p]:
                if cur: r.append(cur); cur = 0
                continue
            # a use strictly between level l-1 and l (bridge at l-0.5) splits before l
            if any(abs(u - (l - 0.5)) < 1e-9 for u in cut) and cur: r.append(cur); cur = 0
            cur += 1
        if cur: r.append(cur)
        runs[p] = r
    return runs
if __name__ == '__main__':
    t = json.loads(gzip.decompress(open(sys.argv[1], 'rb').read()))
    G = apply_recipe(t['recipe'])
    print('global map (rows X0,Y0,X1,Y1,X2,Y2,X3,Y3):')
    for row in G: print('  ', [str(x) for x in row])
    print('idle runs per pair:', geometry(t['recipe']))
