"""bnb: branch and bound over covers of dp by meets feasible in both relaxations; joint r-free (q-chain) pricing,
pruning any partial cover whose joint cost is already >= base (monotone: adding meets never lowers the optimum).
Leaves (full covers) are also priced q-free.  Reports the minimum cover lower bound (or proves none is below base).
usage: bnb.py WORD q [workers] [node_limit]"""
import sys, os, json, time, resource
import multiprocessing as mp
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
from jcommon import *
wname = sys.argv[1]; q = int(sys.argv[2]); W = int(sys.argv[3]) if len(sys.argv) > 3 else 4; LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 4000
P = None
def init():
    global P; P = Pivot(wname, q)
def rjoint(M):
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3 > 6: return M, 'rss', None
    st, c = price_rfree(P, [m[:3] for m in M], timeout=180)
    return M, st, (c - P.base_cost) if c is not None else None
def qjoint(M):
    st, c = P.price([m[:3] for m in M], timeout=180)
    return M, st, (c - P.base_cost) if c is not None else None
if __name__ == '__main__':
    t0 = time.time(); init(); D = os.path.join(JDIR, '..', 'out')
    a = json.load(open(f'{D}/SINGLES-{wname}-{q}.json')); b = json.load(open(f'{D}/RSINGLES-{wname}-{q}.json'))
    qa = {tuple(s['c'][:3]): s for s in a['singles']}; rb = {tuple(s['c'][:3]): s for s in b['singles']}
    cand = [tuple(qa[k]['c']) for k in qa if qa[k]['status'] == 'ok' and rb.get(k, {}).get('status') == 'ok']
    dp = P.dp; ALL = (1 << len(dp)) - 1
    union = 0
    for c in cand: union |= c[3]
    res = dict(word=wname, q=q, dp=dp, n_cand=len(cand), deleted_delta=a['deleted_delta'], uncoverable=[y for i, y in enumerate(dp) if not union >> i & 1])
    if union != ALL:
        res.update(status='closed: some dp register has no feasible meet', seconds=round(time.time() - t0, 1))
        json.dump(res, open(f'{D}/BNB-{wname}-{q}.json', 'w'), default=str); print(json.dumps(res)); sys.exit()
    rsingle = {c: rb[c[:3]]['delta'] for c in cand}
    best = dict(delta=0, cover=None)   # look for covers strictly below base (delta < 0)
    nodes = 0; leaves = []; pool = mp.get_context('fork').Pool(W, initializer=init, maxtasksperchild=60)
    def dfs(M, covered, cost):
        global nodes
        if nodes >= LIMIT: return
        if covered == ALL:
            leaves.append((M, cost))
            if cost < best['delta']: best.update(delta=cost, cover=M)
            return
        unc = [i for i in range(len(dp)) if not covered >> i & 1]
        i0 = min(unc, key=lambda i: sum(1 for c in cand if c[3] >> i & 1))
        kids = sorted([c for c in cand if c[3] >> i0 & 1 and c not in M], key=lambda c: rsingle[c])
        kids = [c for c in kids if rsingle[c] < best['delta']]          # a single already >= bound cannot help
        results = pool.map(rjoint, [tuple(sorted(M + (c,))) for c in kids])
        nodes += len(results)
        for (MM, st, d), c in sorted(zip(results, kids), key=lambda x: (x[0][2] is None, x[0][2] if x[0][2] is not None else 0)):
            if st == 'ok' and d is not None and d < best['delta']: dfs(MM, covered | c[3], d)
    dfs((), 0, a['deleted_delta'])
    pool.close(); pool.join()
    res.update(nodes=nodes, limit_hit=nodes >= LIMIT, leaves=len(leaves), best_rfree=best, seconds=round(time.time() - t0, 1))
    if best['cover']:
        res['best_qfree'] = qjoint(best['cover'])[1:]
    res['status'] = ('closed: no cover below base in the r-free relaxation' if best['cover'] is None and nodes < LIMIT else
                     'gap: cover below base found' if best['cover'] is not None else 'budget hit')
    json.dump(res, open(f'{D}/BNB-{wname}-{q}.json', 'w'), default=str)
    print(json.dumps({k: v for k, v in res.items() if k != 'leaves'}, default=str), flush=True)
