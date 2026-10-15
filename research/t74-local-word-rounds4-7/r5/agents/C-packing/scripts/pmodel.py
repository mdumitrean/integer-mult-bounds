"""Load PR1319's T74 owner map and parent windows into a packing model; validate against the recorded fill."""
import collections, gzip, json, sys
from pathlib import Path
Q = Path(__file__).resolve().parents[4] / 'wt-566/research/global-mixed-t74-exact-fill'
rd = lambda p: json.loads(gzip.decompress(p.read_bytes()) if p.suffix == '.gz' else p.read_bytes())
def load():
    plan = rd(Q / 'PLAN.json'); roles = rd(Q / 'OWNERS.json.gz'); order = [tuple(x) for x in rd(Q / 'ORDER.json')]
    disp = {(s, r): pid for s, r, pid in rd(Q / 'DISPATCH.json')}
    win = {tuple(map(int, k.split(','))): (v[0], set(v[1])) for k, v in plan['windows'].items()}
    reg = plan['provider_registry']; widths = {p: reg[p]['widths'] for p in reg}
    pair = {int(k): v for k, v in plan['pairs'].items()}; side = {int(k): v for k, v in plan['sides'].items()}
    return dict(plan=plan, roles=roles, order=order, disp=disp, win=win, widths=widths, pair=pair, side=side, reg=reg)
def validate(m):
    roles, win = m['roles'], m['win']; occ = collections.Counter(); out = {}
    for z in roles:
        k = (z['owner_replica'], z['child'], z['port']); occ[k] += z['width']
        assert z['time'] in win[z['owner_replica'], z['child']][1]
        assert z['family'] == z['owner_replica'] * 896 + (2 * m['pair'][z['child']] + m['side'][z['child']]) * 112 + z['port']
        assert z['width'] == m['widths'][m['disp'][tuple(m['order'][z['time']])]][z['helper']]
    idle = collections.Counter()
    for (o, ch), (cap, ts) in win.items():
        for port in range(112):
            rem = cap - occ[o, ch, port]; assert rem >= 0
            if rem: idle[rem] += 1
    H = collections.Counter(idle)
    for t, sr in enumerate(m['order']):
        for r, n in m['reg'][m['disp'][sr]]['actual_paid_profile'].items(): H[int(r)] += n
    out['idle'] = dict(idle); out['profile'] = dict(sorted(H.items())); out['rank_mass'] = sum(r * n for r, n in H.items())
    out['plan_profile_match'] = {int(k): v for k, v in m['plan']['profile'].items()} == dict(H)
    out['dispatch'] = dict(collections.Counter(m['disp'].values())); out['roles'] = len(roles)
    out['capacity'] = sum(cap * 112 for cap, ts in win.values()); out['role_width'] = sum(z['width'] for z in roles)
    return out, occ
if __name__ == '__main__':
    m = load(); out, occ = validate(m); print(json.dumps(out, indent=1))
    json.dump(out, open(sys.argv[1], 'w'), indent=1)
