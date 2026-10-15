"""R3: R1 plus dispatch shift, still without moving any role between bins.
Switch extra calls to the (narrowed) base word: a switched call's four extra-only helpers (403/405/406/407, width 5 in
extra, 4 in base) are relabelled onto four of its width-5 roles chosen in (5,9,9,9) 32-bins whose three nines are narrowed
by three distinct calls, so each such bin ends at remainder 4. Remaining calls narrow in place by the R1 greedy.
usage: fill_r3.py OUTDIR [REG=478] [SEED=1]"""
import collections, json, random, sys, time
from pathlib import Path
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=False); REG = int(sys.argv[2]) if len(sys.argv) > 2 else 478; HS = REG - 224
rng = random.Random(int(sys.argv[3]) if len(sys.argv) > 3 else 1)
C = {0: 0, 1: 2116454, 2: 4227983, 3: 6337656, 4: 8446126}; UP = 8458352
t0 = time.time(); L = X.load(); roles = L['roles']; ctx = L['ctx']; V = 112; disp = dict(L['dispatch'])
wb, we = L['widths']['gauge44'], L['widths']['extra']; UPH = [h for h in range(480) if wb[h] != we[h]]
assert sorted((wb[h], we[h]) for h in UPH) == [(4, 5)] * 4, UPH
callof = lambda z: (z['stage'], z['replica'])
bins = collections.defaultdict(list)
for i, z in enumerate(roles): bins[z['owner_replica'], z['child'], z['port']].append(i)
pat = {k: tuple(sorted(roles[i]['width'] for i in v)) for k, v in bins.items()}
used = set(); switches = []; usedbins = set()
extra_calls = [c for c, p in disp.items() if p == 'extra']; rng.shuffle(extra_calls)
fives = collections.defaultdict(list)
for k, v in bins.items():
    if ctx['rank'][k[1]] == 32 and pat[k] == (5, 9, 9, 9):
        f = next(i for i in v if roles[i]['width'] == 5); fives[callof(roles[f])].append((k, f))
for e in extra_calls:
    if e in used: continue
    cand = []
    for k, f in fives[e]:
        if k in usedbins: continue
        ns = [i for i in bins[k] if roles[i]['width'] == 9]; cs = {callof(roles[i]) for i in ns}
        if len(cs) == 3 and not (cs & used) and e not in cs: cand.append((k, f, ns, cs))
    rng.shuffle(cand); chosen, cc = [], set()
    for k, f, ns, cs in cand:
        if not (cs & cc): chosen.append((k, f, ns)); cc |= cs
        if len(chosen) == 4: break
    if len(chosen) == 4 and len(used | cc | {e}) == len(used) + 13 - (1 if e in cc else 0):
        if len(used) + 12 > 666: break
        switches.append(dict(call=list(e), bins=[list(k) for k, f, ns in chosen], fives=[f for k, f, ns in chosen], nines=[i for k, f, ns in chosen for i in ns]))
        used |= cc; usedbins |= {k for k, f, ns in chosen}
print('switches', len(switches), 'narrowed calls used', len(used), round(time.time() - t0, 1), flush=True)
new = [dict(z) for z in roles]; at = collections.defaultdict(dict)
for i, z in enumerate(new): at[callof(z)][z['helper']] = i
def relabel(i, h):
    c = callof(new[i]); j = at[c][h]
    if j != i:
        hi = new[i]['helper']; new[i]['helper'], new[j]['helper'] = h, hi; at[c][hi] = j; at[c][h] = i
for sw in switches:
    e = tuple(sw['call']); disp[e] = 'gauge44'
    for f, h in zip(sw['fives'], UPH): relabel(f, h); new[f]['width'] = 4
    for i in sw['nines']: relabel(i, HS); new[i]['width'] = 8
narrowed = {callof(new[i]) for sw in switches for i in sw['nines']}
left = sorted({callof(z) for z in roles} - narrowed)
nb = collections.defaultdict(list); lset = set(left)
for i, z in enumerate(roles):
    k = (z['owner_replica'], z['child'], z['port'])
    if z['width'] == 9 and k not in usedbins and callof(z) in lset: nb[k].append(i)
inc = collections.defaultdict(list)
for k, v in nb.items():
    for i in v: inc[callof(roles[i])].append(k)
done = set(); avail = {k: len(v) for k, v in nb.items()}; buckets = collections.defaultdict(set)
for k, a in avail.items(): buckets[a].add(k)
pri = {k: (ctx['rank'][k[1]], rng.random()) for k in nb}
while len(done) < len(left):
    r = max(a for a in buckets if buckets[a]); k = max(buckets[r], key=lambda k: pri[k])
    for i in [i for i in nb[k] if callof(roles[i]) not in done]:
        c = callof(roles[i]); done.add(c); relabel(i, HS); new[i]['width'] = 8
        for k2 in inc[c]:
            if k2 in avail and k2 != k: buckets[avail[k2]].discard(k2); avail[k2] -= 1; buckets[avail[k2]].add(k2)
    buckets[avail[k]].discard(k); del avail[k]
X.dump(OUT / 'OWNERS-UNRESTACKED.json.gz', new)
X.dump(OUT / 'DISPATCH.json', [[s, r, disp[s, r]] for s, r in sorted(disp, key=lambda c: ctx['at'][c])])
json.dump(dict(switches=switches, leftover=len(left), seconds=round(time.time() - t0, 1)), open(OUT / 'SWITCHES.json', 'w'))
print('built', len(switches), 'switches;', 'leftover', len(left), 'dispatch', dict(collections.Counter(disp.values())), round(time.time() - t0, 1), flush=True)
