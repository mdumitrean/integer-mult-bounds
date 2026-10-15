"""V-parent extension: conjugation family over all interleavings AND orientation variants (each 2-call pair R,F or F,R; the
3-call pair F,R,F or R,F,R), excluding the original variant (already searched), canonical up to pair relabelling."""
import itertools, json, sys, time, resource, signal, multiprocessing as mp
from collections import Counter
sys.path.insert(0, __import__('os').path.dirname(__file__))
import search_orders as S
def orders():
    out = set(); K = 4
    for tri in range(K):
        for var in itertools.product((0, 1), repeat=K):
            if all(v == 0 for v in var): continue
            seqs = {}
            for p in range(K):
                if p == tri: seqs[p] = [(p, False), (p, True), (p, False)] if var[p] == 0 else [(p, True), (p, False), (p, True)]
                else: seqs[p] = [(p, True), (p, False)] if var[p] == 0 else [(p, False), (p, True)]
            labels = [p for p in range(K) for _ in seqs[p]]
            for perm in set(itertools.permutations(labels)):
                idx = {p: 0 for p in range(K)}; calls = []
                for p in perm: calls.append(seqs[p][idx[p]]); idx[p] += 1
                first = []
                for p in perm:
                    if p not in first: first.append(p)
                rl = {p: i for i, p in enumerate(first)}
                out.add(tuple((rl[p], r) for p, r in calls))
    return sorted(out)
class Timeout(Exception): pass
def _al(*a): raise Timeout()
def work(calls):
    signal.signal(signal.SIGALRM, _al); signal.alarm(1200)
    try: r = S.search_order(list(calls))
    except Timeout: return calls, 'timeout'
    finally: signal.alarm(0)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1 << 30) > 6: raise MemoryError('RSS cap')
    return calls, r
if __name__ == '__main__':
    od = orders(); print('orientation-variant canonical orders:', len(od), flush=True)
    allr = []; to = []; t0 = time.time(); n = 0; g = Counter()
    with mp.get_context('fork').Pool(4, maxtasksperchild=200) as pool:
        for calls, r in pool.imap_unordered(work, od, chunksize=4):
            n += 1
            if r == 'timeout': to.append(calls); continue
            allr += r
            for f in r: g[json.dumps({str(k): v for k, v in sorted(f['runs'].items())})] += 1
            if n % 2000 == 0: print(n, '/', len(od), 'recipes', len(allr), 'geoms', len(g), round(time.time() - t0), 's', flush=True)
    json.dump(dict(orders=len(od), recipes=len(allr), timeouts=to, geometries=dict(g.most_common()), list=allr[:2000]), open(sys.argv[1], 'w'), indent=0)
    print('DONE orders', len(od), 'identity recipes', len(allr), 'timeouts', len(to), round(time.time() - t0), 's')
    for k, c in g.most_common(20): print('  ', c, k)
