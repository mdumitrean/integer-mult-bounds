"""rsingles: r-free (q-chain only) single-meet cost for every candidate of pivot q.  usage: rsingles.py WORD q [workers]"""
import sys, os, json, time, resource
import multiprocessing as mp
JDIR = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, JDIR)
from jcommon import *
wname = sys.argv[1]; q = int(sys.argv[2]); W = int(sys.argv[3]) if len(sys.argv) > 3 else 4
P = None
def init():
    global P; P = Pivot(wname, q)
def run(c):
    sec, pos, r, m = c
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3 > 6: return dict(c=c, status='rss')
    st, cost = price_rfree(P, [(sec, pos, r)], timeout=180)
    return dict(c=c, status=st, delta=(cost - P.base_cost) if cost is not None else None)
if __name__ == '__main__':
    t0 = time.time(); init(); C = P.candidates()
    out = dict(word=wname, q=q, dp=P.dp, base_cost=P.base_cost, n=len(C), singles=[])
    with mp.get_context('fork').Pool(W, initializer=init, maxtasksperchild=40) as pool:
        for r in pool.imap_unordered(run, C): out['singles'].append(r)
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(JDIR, '..', 'out', f'RSINGLES-{wname}-{q}.json'), 'w'), default=str)
    ok = [s for s in out['singles'] if s['status'] == 'ok']
    import collections
    print('done', q, 'n', len(C), 'ok', len(ok), 'infeasible', sum(s['status'] == 'infeasible' for s in out['singles']), 'other', collections.Counter(s['status'] for s in out['singles'] if s['status'] not in ('ok', 'infeasible')), 'delta hist', collections.Counter(s['delta'] for s in ok).most_common(8), f"{out['seconds']}s", flush=True)
