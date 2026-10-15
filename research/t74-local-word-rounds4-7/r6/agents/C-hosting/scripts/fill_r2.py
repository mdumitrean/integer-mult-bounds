"""R2: R1 plus regional consolidation moves that empty 48-bins.
Region = the two cap-48 children of one owner that share a window and a pair ((8,10) or (12,13)); every role of a call in
the window may sit in any of the region's 224 bins (distinct families; same pair, so the active-pair rule is unchanged).
Move = 12 full (4,8,9,9,9,9) bins of one region whose 48 width-9 roles belong to 48 distinct, still-unused calls: narrow all
48 (9 -> 8), then CP-SAT packs the 12 fours + 60 eights exactly into 11 of the bins with distinct calls per bin, emptying
one. Remaining calls are narrowed in place (R1 greedy) outside the moved bins.
usage: fill_r2.py OUTDIR [REG=478] [MOVES=13] [SEED=1]"""
import collections, json, random, sys, time
from pathlib import Path
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
from ortools.sat.python import cp_model
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=False)
REG = int(sys.argv[2]) if len(sys.argv) > 2 else 478; HS = REG - 224; MOVES = int(sys.argv[3]) if len(sys.argv) > 3 else 13
rng = random.Random(int(sys.argv[4]) if len(sys.argv) > 4 else 1)
C = {1: 2116454, 2: 4227983, 3: 6337656, 4: 8446126, 48: 100931344}
t0 = time.time(); L = X.load(); roles = L['roles']; ctx = L['ctx']; V = 112
callof = lambda z: (z['stage'], z['replica'])
bins = collections.defaultdict(list)
for i, z in enumerate(roles): bins[z['owner_replica'], z['child'], z['port']].append(i)
pat = lambda k: tuple(sorted(roles[i]['width'] for i in bins[k]))
c48 = sorted(ch for ch, r in ctx['rank'].items() if r == 48)
groups = collections.defaultdict(list)                    # (owner, pair, window) -> cap-48 children
for o in range(74):
    for ch in c48: groups[o, ctx['child_pair'][ch], ctx['windows'][o, ch]].append(ch)
regions = [(g, chs) for g, chs in groups.items() if len(chs) == 2]
used = set(); moves = []
order = list(range(len(regions))); rng.shuffle(order)
for ri in order:
    if len(moves) >= MOVES: break
    (o, pair, w), chs = regions[ri]
    full = [(o, ch, p) for ch in chs for p in range(V) if pat((o, ch, p)) == (4, 8, 9, 9, 9, 9)]
    rng.shuffle(full)
    while len(moves) < MOVES:
        grp, gc = [], set()
        for k in full:
            if k in {b for m in moves for b in m['bins']}: continue
            cs = [callof(roles[i]) for i in bins[k] if roles[i]['width'] == 9]
            if len(set(cs)) == 4 and not (set(cs) & (used | gc)):
                grp.append(k); gc |= set(cs)
                if len(grp) == 12: break
        if len(grp) < 12: break
        moves.append(dict(region=[o, pair], bins=grp, calls=sorted(gc))); used |= gc
print('moves', len(moves), 'calls used', len(used), round(time.time() - t0, 1), flush=True)
new = [dict(z) for z in roles]; at = collections.defaultdict(dict)
for i, z in enumerate(new): at[callof(z)][z['helper']] = i
def narrow(i):
    c = callof(new[i]); j = at[c][HS]
    if j != i:
        hi = new[i]['helper']; new[i]['helper'], new[j]['helper'] = HS, hi; at[c][hi] = j; at[c][HS] = i
    new[i]['width'] = 8
place = {}                                                 # role index -> new bin
for mv in moves:
    items = [i for k in mv['bins'] for i in bins[k]]
    for i in items:
        if new[i]['width'] == 9: narrow(i)
    target = mv['bins'][:11]; m = cp_model.CpModel(); x = {(i, b): m.NewBoolVar('') for i in items for b in range(11)}
    for i in items: m.AddExactlyOne(x[i, b] for b in range(11))
    for b in range(11):
        m.Add(sum(new[i]['width'] * x[i, b] for i in items) == 48)
        byc = collections.defaultdict(list)
        for i in items: byc[callof(new[i])].append(x[i, b])
        for v in byc.values():
            if len(v) > 1: m.AddAtMostOne(v)
    s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = 30; s.parameters.num_workers = 1; st = s.Solve(m)
    assert st in (cp_model.OPTIMAL, cp_model.FEASIBLE), ('pack failed', mv['bins'][0])
    for i in items:
        b = next(b for b in range(11) if s.Value(x[i, b])); place[i] = target[b]
    mv['emptied'] = list(mv['bins'][11])
moved_bins = {k for mv in moves for k in mv['bins']}
# leftover calls: R1 greedy in place, outside moved bins
left = sorted({callof(z) for z in roles} - used)
nb = collections.defaultdict(list)
for i, z in enumerate(roles):
    k = (z['owner_replica'], z['child'], z['port'])
    if z['width'] == 9 and k not in moved_bins and callof(z) in set(left): nb[k].append(i)
inc = collections.defaultdict(list)
for k, v in nb.items():
    for i in v: inc[callof(roles[i])].append(k)
done = set(); avail = {k: len(v) for k, v in nb.items()}; buckets = collections.defaultdict(set)
for k, a in avail.items(): buckets[a].add(k)
pri = {k: (ctx['rank'][k[1]], rng.random()) for k in nb}
while len(done) < len(left):
    r = max(a for a in buckets if buckets[a]); k = max(buckets[r], key=lambda k: pri[k])
    for i in [i for i in nb[k] if callof(roles[i]) not in done]:
        c = callof(roles[i]); done.add(c); narrow(i)
        for k2 in inc[c]:
            if k2 in avail and k2 != k: buckets[avail[k2]].discard(k2); avail[k2] -= 1; buckets[avail[k2]].add(k2)
    buckets[avail[k]].discard(k); del avail[k]
for i, k in place.items():
    o, ch, p = k; z = new[i]; z.update(owner_replica=o, child=ch, port=p, copy=V * o + p, family=o * 896 + (2 * ctx['child_pair'][ch] + ctx['side'][ch]) * V + p)
nbins = collections.defaultdict(list)
for i, z in enumerate(new): nbins[z['owner_replica'], z['child'], z['port']].append(i)
for k, v in nbins.items():
    off = 0
    for i in sorted(v, key=lambda i: (roles[i]['offset'] if i not in place else 10 ** 6 + i)): new[i]['offset'] = off; off += new[i]['width']
    assert off <= ctx['rank'][k[1]], k
pick = {}
for i, z in enumerate(new):
    if z['helper'] == HS: pick[f'{z["stage"]},{z["replica"]}'] = i
X.dump(OUT / 'OWNERS-UNVERIFIED.json.gz', new)
json.dump(dict(moves=moves, leftover_calls=len(left), seconds=round(time.time() - t0, 1)), open(OUT / 'MOVES.json', 'w'))
print('built', len(moves), 'moves; leftover', len(left), round(time.time() - t0, 1), flush=True)
