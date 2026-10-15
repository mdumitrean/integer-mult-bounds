"""frames_calib.py: re-solve optimal frames for the scalar program rebuilt from the recipe chain (new gates carry no
frames) and for the shipped current word, with the #1186 toolkit (rev3, read-only copy); costs must agree.
usage: frames_calib.py TOOLKIT SHIPPED.json.gz REBUILT.json.gz B OUT.json"""
import sys, json, gzip
tk, shipped, rebuilt, b, out = sys.argv[1:6]
sys.path.insert(0, tk)
import harness as H
res = {}
for name, path in (('shipped', shipped), ('rebuilt', rebuilt)):
    P = H.Pricer(path, b=b, check_literal=False)
    res[name] = dict(cost=P.base_cost, profile={str(k): v for k, v in P.base_profile.items()})
res['equal'] = res['shipped'] == res['rebuilt']
json.dump(res, open(out, 'w'), indent=1); print(json.dumps(res))
