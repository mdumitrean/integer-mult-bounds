"""r10 F-lenders: literal owner check + exact endpoint for an aliased pair of words on the retired5 candidate package.
Drops the removed helpers' roles from the candidate FILL, renumbers helper indices to the new live order, re-tiles each bin as a
consecutive prefix (same bin/window/time/family), derives PROVIDERS (widths of the new live helpers; paid profile = the words'
certified local profile, equal on both), then runs the package's independent_owners.check with the expected global profile and
brackets the exact moment root on the 1e-24 grid with exact_moment.moment_bounds.
usage: python3 -I owner_check_r10.py PKG NEWBASE NEWEXTRA OUTDIR"""
import gzip, json, sys
from collections import Counter, defaultdict
from fractions import Fraction as Fr
from pathlib import Path
PKG = Path(sys.argv[1]); NB, NE, OUT = map(Path, sys.argv[2:5]); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PKG))
import independent_owners as I, exact_moment as M
rd = lambda p: json.loads(gzip.decompress(Path(p).read_bytes()) if str(p).endswith('.gz') else Path(p).read_bytes())
gz = lambda p, x: Path(p).write_bytes(gzip.compress(json.dumps(x, separators=(',', ':')).encode(), mtime=0))
old = {t: rd(PKG / f'inputs/WORD-{t}.json.gz') for t in ('base', 'extra')}; new = {'base': rd(NB), 'extra': rd(NE)}
live = lambda w: [r for r in range(224, 704) if r not in set(w['removed'])]
L0 = live(old['base']); assert L0 == live(old['extra']); L1 = live(new['base']); assert L1 == live(new['extra'])
gone = sorted(set(L0) - set(L1)); assert set(L1) <= set(L0)
i0 = {r: i for i, r in enumerate(L0)}; i1 = {r: i for i, r in enumerate(L1)}
prov = rd(PKG / 'inputs/PROVIDERS.json'); pid = {'base': 'gauge44', 'extra': 'extra'}; newprov = {}
for t in ('base', 'extra'):
    w = new[t]; wd1 = [prov[pid[t]]['widths'][i0[r]] for r in L1]
    assert dict(Counter(wd1)) == {int(k): v for k, v in w['report']['width_inventory'].items()}, 'width inventory'
    newprov[pid[t]] = dict(prov[pid[t]], widths=wd1, actual_paid_profile={str(k): v for k, v in sorted({int(k): v for k, v in w['report']['local_profile'].items()}.items())})
assert newprov['gauge44']['actual_paid_profile'] == newprov['extra']['actual_paid_profile'], 'paid profiles differ'
order = rd(PKG / 'inputs/ORDER.json'); dispatch = {(s, r): p for s, r, p in rd(PKG / 'inputs/DISPATCH.json.gz')}
fill = rd(PKG / 'inputs/FILL.json.gz'); gi = {i0[r] for r in gone}; bins = defaultdict(list); dropped = 0
for row in fill['rows']:
    t, h, o, c, port, off = row
    if h in gi: dropped += 1; continue
    bins[o, c, port].append([t, i1[L0[h]], o, c, port, off])
rows = []
for key, rs in bins.items():
    rs.sort(key=lambda x: x[5]); pos = 0
    for x in rs:
        s, r = order[x[0]]; x[5] = pos; pos += newprov[dispatch[s, r]]['widths'][x[1]]; rows.append(x)
rows.sort(key=lambda x: (x[0], x[1])); nf = dict(fill, rows=rows)
template = rd(PKG / 'inputs/GLOBAL-TEMPLATE.json.gz'); ranks = {c['child']: c['rank'] for c in template['idle_children']}
NBINS = {8: 49728, 16: 33152, 32: 33152, 48: 33152}
used = defaultdict(int)
for t, h, o, c, port, off in rows:
    s, r = order[t]; used[o, c, port] += newprov[dispatch[s, r]]['widths'][h]
idle = Counter(); seen = Counter()
for (o, c, port), u in used.items():
    seen[ranks[c]] += 1
    if ranks[c] - u: idle[ranks[c] - u] += 1
for R, n in NBINS.items(): idle[R] += n - seen[R]
loc = {int(k): v for k, v in newprov['gauge44']['actual_paid_profile'].items()}
profile = Counter({r: 666 * n for r, n in loc.items()}); profile.update({k: v for k, v in idle.items() if v}); profile = dict(sorted(profile.items()))
owner = I.check(rd(PKG / 'inputs/PLAN.json.gz'), template, order, nf, newprov, dispatch, profile)
assert owner['roles'] == 666 * len(L1) and owner['helpers_per_call'] == len(L1)
# exact endpoint on the 1e-24 grid: the largest grid point C with moment(C) < 66304 < moment(C + 1e-24)
import mpmath as mp
mp.mp.dps = 90
root = mp.findroot(lambda a: mp.fsum(n * mp.power(mp.mpf(r) / 73, 1 - a) for r, n in profile.items()) - 66304, (mp.mpf('0.0016'), mp.mpf('0.0018')), solver='anderson')
C = Fr(int(mp.floor(root * mp.mpf(10) ** 24)), 10 ** 24)
_, a = M.moment_bounds(profile, C); b, _ = M.moment_bounds(profile, C + Fr(1, 10 ** 24)); assert a < 66304 < b, 'exact adjacent root bracket'
kappa = C - Fr(1, 10 ** 46) - Fr(1, 10 ** 70)
ref = Fr(17174093163354916434479999999999999999999998999999999999999999999999, 10 ** 70)   # retired5 candidate CLAIM kappa
gz(OUT / 'FILL.json.gz', nf); (OUT / 'PROVIDERS.json').write_text(json.dumps(newprov, indent=1))
res = dict(removed=gone, dropped_roles=dropped, owner=owner, local_profile=loc, idle=dict(sorted(idle.items())), profile=profile,
           root80=mp.nstr(root, 80), complex_lower=str(C.numerator) + '/' + str(C.denominator), kappa=str(kappa.numerator) + '/' + str(kappa.denominator),
           kappa_decimal=mp.nstr(mp.mpf(kappa.numerator) / kappa.denominator, 40), margin_over_candidate=mp.nstr(mp.mpf((kappa - ref).numerator) / (kappa - ref).denominator, 12))
(OUT / 'OWNER-CHECK.json').write_text(json.dumps(res, indent=1, default=str))
print(json.dumps({k: res[k] for k in ('removed', 'dropped_roles', 'idle', 'root80', 'kappa_decimal', 'margin_over_candidate')}), owner['status'])
