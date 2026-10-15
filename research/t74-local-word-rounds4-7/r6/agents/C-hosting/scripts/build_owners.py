"""Build and verify a narrowed owner map from a per-call pick (role index whose helper becomes HSTAR, width 8).
Verification: PR1319's unchanged independent_core.check_roles + its controls + the wrong-provider control, with the
narrowed provider widths and paid profiles (H1 -1 per call, the class of helpers 478/479/490/491).
usage: build_owners.py PICK.json OUTDIR [REG=478]"""
import collections, copy, json, sys, time
from pathlib import Path
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
PICK, OUT = Path(sys.argv[1]), Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=False); REG = int(sys.argv[3]) if len(sys.argv) > 3 else 478; HS = REG - 224
t0 = time.time(); L = X.load(); A = L['A']; roles = L['roles']; ctx = L['ctx']
pick = {tuple(map(int, c.split(','))): i for c, i in json.load(open(PICK))['pick'].items()}
assert len(pick) == 666
new = [dict(z) for z in roles]; at = collections.defaultdict(dict)
for i, z in enumerate(new): at[z['stage'], z['replica']][z['helper']] = i
for c, i in pick.items():
    assert new[i]['width'] == 9 and (new[i]['stage'], new[i]['replica']) == c
    j = at[c][HS]
    if j != i:
        hi = new[i]['helper']; new[i]['helper'], new[j]['helper'] = HS, hi; at[c][hi] = j; at[c][HS] = i
    new[i]['width'] = 8
bins = collections.defaultdict(list)
for i, z in enumerate(new): bins[z['owner_replica'], z['child'], z['port']].append(i)
occ = collections.Counter()
for k, v in bins.items():
    off = 0
    for i in sorted(v, key=lambda i: roles[i]['offset']): new[i]['offset'] = off; off += new[i]['width']
    assert off <= ctx['rank'][k[1]]; occ[k] = off
idle = collections.Counter()
for (owner, child) in ctx['windows']:                          # every bin, including empty ones (as check_roles)
    for port in range(112):
        rem = ctx['rank'][child] - occ[owner, child, port]
        if rem: idle[rem] += 1
widths = {p: list(w) for p, w in L['widths'].items()}
for p in widths: assert widths[p][HS] == 9; widths[p][HS] = 8
paid = {p: collections.Counter(L['paid'][p]) for p in L['paid']}
for p in paid: paid[p][1] -= 1                                  # narrowing removes the helper's rank-1 first jump
c = X.set_inventory(L, L['dispatch'], widths, paid, idle)
new.sort(key=lambda r: (r['time'], r['helper']))
r = A.check_roles(c, new); ctrl = A.controls(c, new)
call = next(cc for cc, p in L['dispatch'].items() if p == 'extra'); bad = dict(c, call_widths=dict(c['call_widths'])); bad['call_widths'][call] = widths['gauge44']
try: A.check_roles(bad, new)
except ValueError as e: assert str(e) == 'whole-helper residual width'; ctrl.append(dict(name='wrong_provider_at_changed_call', reason=str(e)))
else: raise AssertionError('wrong provider accepted')
# changed-role accounting against the current owner map
key = lambda z: (z['stage'], z['replica'], z['helper'])
oldm = {key(z): z for z in roles}; changed = [z for z in new if oldm[key(z)] != z]
moved_bins = sum(1 for z in changed if (z['owner_replica'], z['child'], z['port']) != (oldm[key(z)]['owner_replica'], oldm[key(z)]['child'], oldm[key(z)]['port']))
X.dump(OUT / 'OWNERS.json.gz', new)
json.dump(dict(gauge44=widths['gauge44'], extra=widths['extra']), open(OUT / 'PROVIDER-WIDTHS.json', 'w'))
rec = dict(status=r['status'], helper_register=REG, helper_index=HS, dispatch=dict(collections.Counter(L['dispatch'].values())),
           inventories={p: dict(sorted(collections.Counter(w).items())) for p, w in widths.items()},
           assumed_paid={p: dict(sorted(paid[p].items())) for p in paid}, idle=r['idle'], profile=r['profile'], rank_mass=r['rank_mass'],
           charts=r['actual_73_axis_charts'], prefix_bits=r['prefix_bits'], charged_prefix_bits=r['charged_prefix_bits'],
           physical_row_coefficient=r['physical_row_coefficient'], controls_rejected=[x['name'] for x in ctrl],
           roles=len(new), roles_changed=len(changed), roles_moved_between_bins=moved_bins, owners_content_sha256=X.content_sha(new), seconds=round(time.time() - t0, 1))
json.dump(rec, open(OUT / 'CHECK.json', 'w'), indent=1); print(json.dumps({k: v for k, v in rec.items() if k not in ('inventories', 'assumed_paid')}))
