"""V-parent: all nine-stage call orders (one F,R,F pair + three R,F pairs, every interleaving, canonical up to pair relabelling)
x every choice of 3 conjugated calls (src != own pair, coefficient +-1, bridge +c before / -c after) x 3 final bridges solved by
lookup; keep recipes satisfying global_k.py's integer identity with every one of the 18 shears necessary; record geometries.
usage: search_orders.py OUT.json [--workers 4] [--limit N]"""
import itertools, json, os, sys, time, resource, multiprocessing as mp
from collections import Counter, defaultdict
K = 4; N = 8
I8 = tuple(tuple(int(i == j) for j in range(N)) for i in range(N))
def rowadd(Z, d, s, c):
    Z = list(Z); rd, rs = Z[d], Z[s]; Z[d] = tuple(x + c * y for x, y in zip(rd, rs)); return Z
def exch(Z):
    Z = list(Z)
    for j in range(K): Z[2 * j], Z[2 * j + 1] = Z[2 * j + 1], tuple(-x for x in Z[2 * j])
    return Z
def exch_inv(Z):
    Z = list(Z)
    for j in range(K): Z[2 * j], Z[2 * j + 1] = tuple(-x for x in Z[2 * j + 1]), Z[2 * j]
    return Z
def ops_of(events):
    """elementary row ops (d, s, c) or 'X' in application order"""
    out = []
    for e in events:
        if e[0] == 'L':
            p, rev = e[1], e[2]; out.append((2 * p, 2 * p + 1, -1) if rev else (2 * p + 1, 2 * p, 1))
        elif e[0] == 'B':
            d, s, c = e[1], e[2], e[3]; out.append((2 * d, 2 * s, c)); out.append((2 * s + 1, 2 * d + 1, -c))
        else: out.append('X')
    return out
def apply(ops, Z=I8, skip=-1):
    Z = list(Z); k = 0
    for o in ops:
        if o == 'X': Z = exch(Z); continue
        if k != skip: Z = rowadd(Z, *o)
        k += 1
    return tuple(Z)
def inverse_of(ops):
    Z = list(I8)
    for o in reversed(ops):
        Z = exch_inv(Z) if o == 'X' else rowadd(Z, o[0], o[1], -o[2])
    return tuple(Z)
BR = [(d, s, c) for d in range(K) for s in range(K) if s != d for c in (1, -1)]
TABLE = None
def table():
    global TABLE
    if TABLE is None:
        TABLE = defaultdict(list)
        for trip in itertools.product(BR, repeat=3):
            TABLE[apply(ops_of([('B',) + b for b in trip]))].append(trip)
    return TABLE
def geometry(events):
    lvl = -1; own = defaultdict(set); uses = defaultdict(set); L = 0
    for e in events:
        if e[0] == 'L': lvl += 1; own[e[1]].add(lvl); L += 1
        elif e[0] == 'B': uses[e[1]].add(lvl); uses[e[2]].add(lvl)     # bridge after level lvl (splits before lvl+1)
    runs = {}
    for p in range(K):
        r = []; cur = 0
        for l in range(L):
            if l in own[p]:
                if cur: r.append(cur); cur = 0
                continue
            if cur and (l - 1) in uses[p]: r.append(cur); cur = 0
            cur += 1
        if cur: r.append(cur)
        runs[p] = tuple(r)
    return runs
def search_order(calls):
    T = table(); res = []
    for conj in itertools.combinations(range(9), 3):
        for srcs in itertools.product(range(K), repeat=3):
            if any(srcs[i] == calls[conj[i]][0] for i in range(3)): continue
            for coefs in itertools.product((1, -1), repeat=3):
                pre = []
                for t, (p, rev) in enumerate(calls):
                    if t in conj:
                        i = conj.index(t); pre += [('B', p, srcs[i], coefs[i]), ('L', p, rev), ('B', p, srcs[i], -coefs[i])]
                    else: pre.append(('L', p, rev))
                # E * X * Mpre = I  ->  X = E^-1 Mpre^-1
                X = tuple(exch_inv(list(inverse_of(ops_of(pre)))))
                if X not in T: continue
                for trip in T[X]:
                    ev = pre + [('B',) + b for b in trip] + [('X',)]
                    ops = ops_of(ev)
                    if apply(ops) != I8: continue
                    nsh = sum(1 for o in ops if o != 'X')
                    if any(apply(ops, skip=k) == I8 for k in range(nsh)): continue
                    res.append(dict(calls=calls, conj=[(conj[i], srcs[i], coefs[i]) for i in range(3)], final=list(trip), runs=geometry(ev)))
    return res
def canonical_orders():
    pats = []
    for tri in range(K):
        seqs = {p: ([(p, False), (p, True), (p, False)] if p == tri else [(p, True), (p, False)]) for p in range(K)}
        lens = {p: len(seqs[p]) for p in range(K)}
        # interleavings: choose pair label sequence of length 9 with counts
        labels = []
        for p in range(K): labels += [p] * lens[p]
        seen = set()
        for perm in set(itertools.permutations(labels)):
            # canonical: first appearances in order 0,1,2,3 after relabel -> skip unless already canonical with tri relabelled
            pos = {p: [] for p in range(K)}
            for i, p in enumerate(perm): pos[p].append(i)
            idx = {p: 0 for p in range(K)}; calls = []
            for p in perm: calls.append(seqs[p][idx[p]]); idx[p] += 1
            # relabel pairs by first appearance
            order = []
            for p in perm:
                if p not in order: order.append(p)
            rl = {p: i for i, p in enumerate(order)}
            can = tuple((rl[p], r) for p, r in calls)
            if can not in seen: seen.add(can); pats.append(can)
    return sorted(set(pats))
class Timeout(Exception): pass
def _alarm(sig, frm): raise Timeout()
def worker(calls):
    import signal
    signal.signal(signal.SIGALRM, _alarm); signal.alarm(1200)          # per-task timeout
    t0 = time.time()
    try: r = search_order(list(calls))
    except Timeout: return calls, 'timeout', time.time() - t0
    finally: signal.alarm(0)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1 << 30)   # bytes on macOS
    if rss > 6: raise MemoryError('worker RSS %.2f GiB above cap' % rss)
    return calls, r, time.time() - t0
if __name__ == '__main__':
    out = sys.argv[1]; W = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
    lim = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else None
    orders = canonical_orders(); print('canonical orders:', len(orders), flush=True)
    if lim: orders = orders[:lim]
    allres = []; geoms = Counter(); t0 = time.time(); done = 0; timeouts = []
    with mp.get_context('fork').Pool(W, maxtasksperchild=50) as pool:
        for calls, r, sec in pool.imap_unordered(worker, orders, chunksize=1):
            done += 1
            if r == 'timeout': timeouts.append(calls); continue
            allres += r
            for f in r: geoms[json.dumps({str(k): v for k, v in sorted(f['runs'].items())})] += 1
            if done % 50 == 0 or done == len(orders):
                print(f'{done}/{len(orders)} orders, {len(allres)} identity recipes, {len(geoms)} geometries, {time.time()-t0:.0f}s', flush=True)
                json.dump(dict(done=done, total=len(orders), recipes=len(allres), geometries=dict(geoms.most_common()), sample=allres[:200]), open(out, 'w'))
    json.dump(dict(done=done, total=len(orders), recipes=len(allres), timeouts=timeouts, geometries=dict(geoms.most_common()), recipes_list=allres), open(out, 'w'))
    print('DONE', len(allres), 'recipes;', len(geoms), 'geometries')
    for g, n in geoms.most_common(40): print('  ', n, g)
