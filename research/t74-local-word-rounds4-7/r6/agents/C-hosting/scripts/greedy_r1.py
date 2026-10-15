"""Greedy concentration for R1 (no cross-bin moves): repeatedly take the bin with the most still-unassigned width-9 calls
(ties: larger capacity, then random), narrowing all of them there. Best of N random tie-breaks.
usage: greedy_r1.py OUT.json [N=200] [SEED=1]"""
import collections, json, random, sys, time
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
C = {1: 2116454, 2: 4227983, 3: 6337656, 4: 8446126}
N = int(sys.argv[2]) if len(sys.argv) > 2 else 200; rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
t0 = time.time(); L = X.load(); roles = L['roles']; ctx = L['ctx']
bins = collections.defaultdict(list)
for i, z in enumerate(roles):
    if z['width'] == 9: bins[z['owner_replica'], z['child'], z['port']].append(i)
keys = list(bins); call_of = {i: (roles[i]['stage'], roles[i]['replica']) for v in bins.values() for i in v}
inc = collections.defaultdict(list)
for k in keys:
    for i in bins[k]: inc[call_of[i]].append(k)
calls = sorted(inc); best = None
for trial in range(N):
    pri = {k: (ctx['rank'][k[1]], rng.random()) for k in keys}
    avail = {k: len(bins[k]) for k in keys}; done = set(); pick = {}
    buckets = collections.defaultdict(set)
    for k in keys: buckets[avail[k]].add(k)
    while len(done) < len(calls):
        r = max(a for a in buckets if buckets[a])
        k = max(buckets[r], key=lambda k: pri[k]) if r > 1 else max(buckets[r], key=lambda k: pri[k])
        sel = [i for i in bins[k] if call_of[i] not in done]
        for i in sel:
            c = call_of[i]; done.add(c); pick[c] = i
            for k2 in inc[c]:
                if k2 in avail and k2 != k:
                    buckets[avail[k2]].discard(k2); avail[k2] -= 1; buckets[avail[k2]].add(k2)
        buckets[avail[k]].discard(k); del avail[k]
    rem = collections.Counter()
    for c, i in pick.items(): rem[roles[i]['owner_replica'], roles[i]['child'], roles[i]['port']] += 1
    cost = sum(C[v] for v in rem.values())
    if best is None or cost < best[0]: best = (cost, dict(collections.Counter(rem.values())), {f'{c[0]},{c[1]}': i for c, i in pick.items()})
gain = 666 * 2116454 - best[0]
out = dict(trials=N, idle_cost=best[0], rem_hist=best[1], gain_units=gain, kappa_est=gain * 4.1e-8 / (1850 * 666), seconds=round(time.time() - t0, 1), pick=best[2])
json.dump(out, open(sys.argv[1], 'w')); print(json.dumps({k: v for k, v in out.items() if k != 'pick'}))
