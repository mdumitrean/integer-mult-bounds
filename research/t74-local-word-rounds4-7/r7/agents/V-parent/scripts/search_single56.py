"""V-parent: broader family. Block call orders (each pair's calls contiguous; triple pair at block position t), up to r <= 4
interior SINGLE bridges (at most one per inter-call slot; within a pair's block the bridge must involve that pair, at a
boundary it must join the two adjacent pairs), all remaining bridges at the beginning/end. Necessary and sufficient
condition for begin/end bridges to complete global_k.py's identity: the middle product M (calls + interior bridges) has zero
X->X and Y->Y blocks, M = [[0, -A^-1 B^T], [A^T B^-1, 0]] (A, B = end/begin bridge products acting on the X banks).
Reports every candidate and its idle-run geometry (interior single bridges split runs; begin/end bridges split nothing)."""
import itertools, json, sys, time
from collections import Counter, defaultdict
sys.path.insert(0, __import__('os').path.dirname(__file__))
from search_orders import ops_of, apply, I8, geometry, K
def block_orders():
    out = []
    for t in range(K):
        calls = []
        for p in range(K):
            calls += [(p, False), (p, True), (p, False)] if p == t else [(p, True), (p, False)]
        out.append(tuple(calls))
    return out
def slot_options(calls):
    opts = []
    for k in range(1, len(calls)):
        a, b = calls[k - 1][0], calls[k][0]
        if a == b: pairs = [(a, q) for q in range(K) if q != a] + [(q, a) for q in range(K) if q != a]
        else: pairs = [(a, b), (b, a)]
        opts.append([(d, s, c) for d, s in pairs for c in (1, -1)])
    return opts
def zero_diag(M):
    X = [0, 2, 4, 6]; Y = [1, 3, 5, 7]
    return all(M[i][j] == 0 for i in X for j in X) and all(M[i][j] == 0 for i in Y for j in Y)
RANGE = range(5, 7)
def main(out):
    res = []; t0 = time.time(); tested = 0
    for calls in block_orders():
        opts = slot_options(calls); nslots = len(opts)
        for r in RANGE:
            for slots in itertools.combinations(range(nslots), r):
                for choice in itertools.product(*[opts[s] for s in slots]):
                    ev = []; ch = dict(zip(slots, choice))
                    for k, (p, rev) in enumerate(calls):
                        if k >= 1 and (k - 1) in ch: ev.append(('B',) + ch[k - 1])
                        ev.append(('L', p, rev))
                    M = apply(ops_of(ev)); tested += 1
                    if zero_diag(M):
                        res.append(dict(calls=calls, interior=[(s + 1,) + ch[s] for s in slots], runs=geometry(ev)))
    geoms = Counter(json.dumps({str(k): v for k, v in sorted(r_['runs'].items())}) for r_ in res)
    json.dump(dict(tested=tested, candidates=len(res), geometries=dict(geoms.most_common()), list=res[:500]), open(out, 'w'), indent=0)
    print('tested', tested, 'middle products; zero-diagonal candidates', len(res), 'in', round(time.time() - t0), 's')
    for g, n in geoms.most_common(20): print('  ', n, g)
if __name__ == '__main__': main(sys.argv[1])
