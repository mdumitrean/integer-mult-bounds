"""rbnb: real shared-node skeleton search per pivot.  For every candidate meet (segment start of a register whose
dataflow reaches dp), price the deleted word + the actual read r += q (q's and r's chains share the node, base caps);
then branch and bound over covers of dp with joint real pricing, pruning partial skeletons whose cost is >= base
(adding reads never lowers the optimum).  A skeleton is the frame part of an exact re-delivery (coefficients and
restores only add gates), so: min skeleton cost >= base  =>  no star re-delivery at these positions gains.
usage: rbnb.py WORD q1 [q2 ...]   (env J_WORKERS, J_LIMIT)"""
import sys, os, json, time, resource, collections
import multiprocessing as mp
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
from jcommon import *
W = int(os.environ.get('J_WORKERS', 4)); LIMIT = int(os.environ.get('J_LIMIT', 2500))
P = None; QQ = None
def init(wname, q):
    global P; P = Pivot(wname, q)
def real(M):
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3 > 6: return M, 'rss', None
    st, c, prof = price_real(P, [m[:3] for m in M], timeout=180)
    return M, st, (c - P.base_cost) if c is not None else None
def solve(wname, q):
    t0 = time.time(); init(wname, q); D = os.path.join(JDIR, '..', 'out')
    C = P.candidates(); st0, c0 = P.price([]); dd = c0 - P.base_cost
    pool = mp.get_context('fork').Pool(W, initializer=init, initargs=(wname, q), maxtasksperchild=80)
    singles = pool.map(real, [(c,) for c in C])
    feas = {M[0]: d for M, st, d in singles if st == 'ok'}
    dp = P.dp; ALL = (1 << len(dp)) - 1; union = 0
    for c in feas: union |= c[3]
    res = dict(word=wname, q=q, dp=dp, deleted_delta=dd, n_cand=len(C), n_feasible=len(feas),
               single_hist=collections.Counter(feas.values()).most_common(6), uncoverable=[y for i, y in enumerate(dp) if not union >> i & 1])
    best = dict(delta=0, cover=None); nodes = [0]; leaves = [0]
    def dfs(M, covered):
        if nodes[0] >= LIMIT: return
        if covered == ALL:
            leaves[0] += 1; return
        unc = [i for i in range(len(dp)) if not covered >> i & 1]
        i0 = min(unc, key=lambda i: sum(1 for c in feas if c[3] >> i & 1))
        kids = sorted([c for c in feas if c[3] >> i0 & 1 and c not in M and feas[c] < best['delta']], key=lambda c: feas[c])
        if not kids: return
        results = pool.map(real, [tuple(sorted(M + (c,))) for c in kids]); nodes[0] += len(results)
        for (MM, st, d), c in sorted(zip(results, kids), key=lambda x: (x[0][2] is None, x[0][2] if x[0][2] is not None else 0)):
            if st == 'ok' and d is not None and d < best['delta']:
                if covered | c[3] == ALL: best.update(delta=d, cover=MM); leaves[0] += 1
                else: dfs(MM, covered | c[3])
    if union == ALL: dfs((), 0)
    pool.close(); pool.join()
    res.update(nodes=nodes[0], limit_hit=nodes[0] >= LIMIT, best=best, seconds=round(time.time() - t0, 1))
    res['status'] = ('closed (no feasible meet for some dp register)' if union != ALL else
                     'no skeleton below base' if best['cover'] is None and nodes[0] < LIMIT else
                     'skeleton below base' if best['cover'] is not None else 'budget hit, none found')
    json.dump(res, open(f'{D}/RBNB-{wname}-{q}.json', 'w'), default=str)
    print(json.dumps(res, default=str), flush=True)
if __name__ == '__main__':
    wname = sys.argv[1]
    for q in map(int, sys.argv[2:]): solve(wname, q)
