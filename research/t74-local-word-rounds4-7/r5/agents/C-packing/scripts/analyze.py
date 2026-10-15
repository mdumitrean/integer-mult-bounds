import collections, json, sys
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import pmodel as M
m = M.load(); roles, win = m['roles'], m['win']
wb, we = m['widths']['gauge44'], m['widths']['extra']
up = [h for h in range(480) if wb[h] != we[h]]; print('upgraded helpers (base->extra):', [(h, wb[h], we[h]) for h in up])
bins = collections.defaultdict(list)
for z in roles: bins[z['owner_replica'], z['child'], z['port']].append(z)
comp = collections.Counter()
for (o, ch, p), (cap, ts) in ((k + (p,), v) for k, v in win.items() for p in range(112)):
    rr = bins.get((o, ch, p), []); comp[cap, tuple(sorted(r['width'] for r in rr))] += 1
bycap = collections.defaultdict(list)
for (cap, c), n in comp.items(): bycap[cap].append((n, c))
for cap in sorted(bycap):
    tot = sum(n for n, c in bycap[cap]); print(f'cap {cap}: {tot} bins, {len(bycap[cap])} compositions; top:', sorted(bycap[cap], reverse=True)[:8])
# upgraded roles of extra calls: their bins' compositions
ex = [t for t, sr in enumerate(m['order']) if m['disp'][sr] == 'extra']
upc = collections.Counter(); where = collections.Counter()
for z in roles:
    if z['helper'] in up and m['disp'][m['order'][z['time']]] == 'extra':
        k = (z['owner_replica'], z['child'], z['port']); upc[tuple(sorted(r['width'] for r in bins[k]))] += 1; where[win[z['owner_replica'], z['child']][0]] += 1
print('extra calls', len(ex), '| upgraded-role bin caps', dict(where), '| compositions', upc.most_common(6))
print('roles per bin by cap', {cap: collections.Counter(len(bins.get((o, ch, p), [])) for (o, ch), (c, ts) in win.items() if c == cap for p in range(112)).most_common(4) for cap in (8, 16, 32, 48)})
ts = collections.Counter(len(v[1]) for v in win.values()); print('window sizes min/max', min(ts), max(ts))
