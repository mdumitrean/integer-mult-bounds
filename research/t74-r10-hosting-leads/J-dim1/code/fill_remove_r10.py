"""r10 F-lenders: realized fill for aliased words on the retired5 candidate: drop the removed helpers' roles from the
candidate's literal FILL, compact each bin (same bin/window/time/family), recompute idle, combine with the word's certified
local profile, exact moment root (80 digits).  usage: python3 -I fill_remove_r10.py PKG CAND_WORD NEW_WORD [NEW_WORD ...]"""
import gzip, json, sys
from collections import Counter, defaultdict
import mpmath as mp
mp.mp.dps = 90
PKG = sys.argv[1]
rd = lambda p: json.loads(gzip.decompress(open(p, 'rb').read()) if p.endswith('.gz') else open(p, 'rb').read())
M, W, CALLS = 73, 66304, 666
NB = {8: 49728, 16: 33152, 32: 33152, 48: 33152}
REF = mp.mpf('0.001717409316335491643448458477541172229282')
parent = rd(PKG + '/inputs/GLOBAL-TEMPLATE.json.gz'); ranks = {c['child']: c['rank'] for c in parent['idle_children']}
order = rd(PKG + '/inputs/ORDER.json'); dispatch = {(s, r): p for s, r, p in rd(PKG + '/inputs/DISPATCH.json.gz')}
prov = rd(PKG + '/inputs/PROVIDERS.json'); widths = {p: d['widths'] for p, d in prov.items()}
fill = rd(PKG + '/inputs/FILL.json.gz'); assert not fill.get('dispatch_overrides')
w0 = rd(sys.argv[2]); live0 = [r for r in range(224, 704) if r not in set(w0['removed'])]; idx = {r: i for i, r in enumerate(live0)}
bins = defaultdict(list)
for time, helper, rep, child, port, offset in fill['rows']:
    s, r = order[time]; wd = widths[dispatch[s, r]][helper]
    bins[rep, child, port].append((offset, wd, time, helper))
for key, roles in bins.items():
    roles.sort(); pos = 0
    for off, wd, t, h in roles: assert off == pos, ('gap', key); pos += wd
    assert pos <= ranks[key[1]]
def idle_of(drop):
    idle = Counter(); used_by_rank = Counter()
    for (rep, child, port), roles in bins.items():
        cap = ranks[child]; used = sum(wd for off, wd, t, h in roles if h not in drop)
        used_by_rank[cap] += 1
        if cap - used: idle[cap - used] += 1
    for R, n in NB.items(): idle[R] += n - used_by_rank[R]
    return dict(sorted((k, v) for k, v in idle.items() if v))
def root(counts):
    f = lambda a: mp.fsum(n * mp.power(mp.mpf(r) / M, 1 - a) for r, n in counts.items() if r) - W
    return mp.findroot(f, (mp.mpf('0.0016'), mp.mpf('0.0018')), solver='anderson')
def glob(loc, idle):
    c = Counter({r: CALLS * n for r, n in loc.items()}); c.update(idle); return dict(sorted(c.items()))
loc0 = {int(k): v for k, v in w0['report']['local_profile'].items()}
idle0 = idle_of(set()); b0 = root(glob(loc0, idle0))
print('candidate idle', idle0, 'root - REF', mp.nstr(b0 - REF, 5), flush=True)
out = {}
for p in sys.argv[3:]:
    w = rd(p); gone = sorted(set(w['removed']) - set(w0['removed'])); assert set(w0['removed']) <= set(w['removed'])
    loc = {int(k): v for k, v in w['report']['local_profile'].items()}
    assert sum(r * n for r, n in loc.items()) == sum(r * n for r, n in loc0.items()) - sum(widths['gauge44'][idx[h]] for h in gone), 'mass'
    idle = idle_of({idx[h] for h in gone}); g = glob(loc, idle); b = root(g)
    out[p] = dict(removed=gone, local=loc, idle=idle, profile=g, root=mp.nstr(b, 80), margin=mp.nstr(b - REF, 12))
    print(p.split('/')[-1], 'removed', gone, 'idle', idle, 'root', mp.nstr(b, 30), 'margin over candidate', mp.nstr(b - REF, 8), flush=True)
json.dump(out, open(sys.argv[3].rsplit('/', 1)[0] + '/../out/FILL-REMOVE-' + str(abs(hash(tuple(sys.argv[3:]))) % 10**6) + '.json', 'w'), indent=1)
