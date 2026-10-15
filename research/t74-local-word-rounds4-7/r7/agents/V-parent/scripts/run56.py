"""Parallel driver for r = 5, 6 (one block order per worker), with per-task timeout and RSS cap."""
import json, sys, time, resource, signal, itertools, multiprocessing as mp
from collections import Counter
sys.path.insert(0, __import__('os').path.dirname(__file__))
import search_single56 as S
from search_orders import ops_of, apply, geometry
class Timeout(Exception): pass
def _al(*a): raise Timeout()
def work(args):
    calls, r = args; signal.signal(signal.SIGALRM, _al); signal.alarm(2400)
    res = []; tested = 0
    try:
        opts = S.slot_options(calls)
        for slots in itertools.combinations(range(len(opts)), r):
            for choice in itertools.product(*[opts[s] for s in slots]):
                ch = dict(zip(slots, choice)); ev = []
                for k, (p, rev) in enumerate(calls):
                    if k >= 1 and (k - 1) in ch: ev.append(('B',) + ch[k - 1])
                    ev.append(('L', p, rev))
                tested += 1
                if S.zero_diag(apply(ops_of(ev))): res.append(dict(calls=calls, interior=[(s + 1,) + ch[s] for s in slots], runs=geometry(ev)))
    except Timeout: return calls, r, 'timeout', tested
    finally: signal.alarm(0)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1 << 30) > 6: raise MemoryError('RSS cap')
    return calls, r, res, tested
if __name__ == '__main__':
    jobs = [(c, r) for c in S.block_orders() for r in (5, 6)]
    allr = []; tested = 0; t0 = time.time(); to = []
    with mp.get_context('fork').Pool(4, maxtasksperchild=1) as pool:
        for calls, r, res, n in pool.imap_unordered(work, jobs):
            tested += n
            if res == 'timeout': to.append((calls, r)); print('TIMEOUT', r, calls, flush=True); continue
            allr += res; print('done r=%d order=%s: %d tested, %d candidates, %ds' % (r, [p for p, _ in calls], n, len(res), time.time() - t0), flush=True)
    g = Counter(json.dumps({str(k): v for k, v in sorted(x['runs'].items())}) for x in allr)
    json.dump(dict(tested=tested, candidates=len(allr), timeouts=to, geometries=dict(g.most_common()), list=allr[:2000]), open(sys.argv[1], 'w'), indent=0)
    print('TOTAL tested', tested, 'candidates', len(allr), 'timeouts', len(to))
    for k, n in g.most_common(20): print('  ', n, k)
