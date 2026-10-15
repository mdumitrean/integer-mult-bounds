"""Sanity: PR1319's check_roles accepts the current owner map with the 566+554 provider profiles."""
import json, sys, time
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
t = time.time(); L = X.load(); A = L['A']
c = X.set_inventory(L, L['dispatch'], L['widths'], L['paid'], {48: 22748})
r = A.check_roles(c, L['roles']); assert r['profile'] == {int(k): v for k, v in L['plan72']['profile'].items()}, r['profile']
ctrl = A.controls(c, L['roles'])
out = dict(status=r['status'], idle=r['idle'], profile=r['profile'], charts=r['actual_73_axis_charts'], prefix_bits=r['prefix_bits'],
           charged=r['charged_prefix_bits'], row=r['physical_row_coefficient'], rank_mass=r['rank_mass'], controls=len(ctrl), seconds=round(time.time() - t, 1))
json.dump(out, open(sys.argv[1], 'w'), indent=1); print(json.dumps(out))
