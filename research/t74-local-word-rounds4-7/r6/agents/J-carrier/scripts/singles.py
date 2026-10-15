"""singles: q-free single-meet cost for every candidate of pivot q (deleted word + one meet).  usage: singles.py WORD q [workers]"""
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
    st, cost = P.price([(sec, pos, r)], timeout=180)
    return dict(c=c, status=st, delta=(cost - P.base_cost) if cost is not None else None)
if __name__ == '__main__':
    t0 = time.time(); init(); C = P.candidates(); st, dc = P.price([])
    out = dict(word=wname, q=q, dp=P.dp, base_cost=P.base_cost, deleted_delta=dc - P.base_cost, Lq_dim=len(P.Lq('B', 0)), n=len(C), singles=[])
    with mp.get_context('fork').Pool(W, initializer=init, maxtasksperchild=40) as pool:
        for i, r in enumerate(pool.imap_unordered(run, C), 1):
            out['singles'].append(r)
            if i % 50 == 0: print(q, i, '/', len(C), f'{time.time()-t0:.0f}s', flush=True)
    out['seconds'] = round(time.time() - t0, 1)
    json.dump(out, open(os.path.join(JDIR, '..', 'out', f'SINGLES-{wname}-{q}.json'), 'w'), default=str)
    ok = [s for s in out['singles'] if s['status'] == 'ok']
    print('done', q, 'n', len(C), 'ok', len(ok), 'infeasible', sum(s['status'] == 'infeasible' for s in out['singles']), 'other', sum(s['status'] not in ('ok', 'infeasible') for s in out['singles']), 'deleted', out['deleted_delta'], 'min single', min((s['delta'] for s in ok), default=None), 'max', max((s['delta'] for s in ok), default=None), f"{out['seconds']}s", flush=True)
