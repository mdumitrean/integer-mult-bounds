"""Summarize the C-repair sweeps into EVIDENCE.json.  usage: summarize.py RUNS_DIR OUT.json"""
import json, sys, collections
from pathlib import Path
D = Path(sys.argv[1]); out = dict(words={}, b='0.001679754956125544')
for word in ('gauge44', 'extra'):
    W = out['words'][word] = {}
    f = D / f'repair-{word}.json'
    if f.exists():
        res = json.load(open(f)); st = collections.Counter(p['status'] for x in res for p in x['pricings'])
        neg = [dict(t=x['t'], A=x['A'], H=x['H'], p=x['p'], rest=x['rest'], pricing=p) for x in res for p in x['pricings'] if p['delta'] is not None and p['delta'] < 0]
        bounds = [p['max_gain_units'] for x in res for p in x['pricings'] if p['status'] in ('ok', 'uncertified') and p['delta'] is not None and p['delta'] >= 0 and p['max_gain_units'] is not None]
        deltas = collections.Counter(p['delta'] for x in res for p in x['pricings'] if p['status'] in ('ok', 'uncertified'))
        W['fusion_repair'] = dict(fusions=len(res), tAH_triples=len({(x['t'], x['A'], x['H']) for x in res}), pricings=sum(x['tried'] for x in res),
                                  fusions_with_feasible_pricing=sum(1 for x in res if x['best']), statuses=dict(st), negative=neg,
                                  feasible_delta_histogram=dict(sorted((str(k), v) for k, v in deltas.items())[:40]),
                                  largest_possible_true_gain_units_among_nongains=max(bounds, default=0.0))
    f = D / f'xj-{word}.json'
    if f.exists():
        res = json.load(open(f)); fam = collections.defaultdict(collections.Counter)
        for r in res: fam[r['fam']][r['price'].get('status')] += 1
        neg = [r for r in res if r['price'].get('delta') is not None and r['price']['delta'] < 0]
        bounds = [r['price']['max_gain_units'] for r in res if r['price'].get('status') in ('ok', 'uncertified') and r['price'].get('delta', 1) >= 0 and 'max_gain_units' in r['price']]
        W['exchange_joint'] = dict(jobs=len(res), families={k: dict(v) for k, v in fam.items()}, negative=[dict(fam=r['fam'], key=r['key'], price=r['price']) for r in neg],
                                   largest_possible_true_gain_units_among_nongains=max(bounds, default=0.0))
    f = D / f'pos-{word}.json'
    if f.exists():
        res = json.load(open(f)); st = collections.Counter(r['price'].get('status') for r in res)
        neg = [r for r in res if r['price'].get('delta') is not None and r['price']['delta'] < 0]
        okd = collections.Counter(r['price'].get('delta') for r in res if r['price'].get('status') == 'ok')
        bounds = [r['price']['max_gain_units'] for r in res if r['price'].get('status') in ('ok', 'uncertified') and r['price'].get('delta', 1) >= 0 and 'max_gain_units' in r['price']]
        W['fusion_position_classes'] = dict(candidates=len(res), triples=len({(r['t'], r['A'], r['H']) for r in res}), statuses=dict(st),
                                            ok_delta_histogram={str(k): v for k, v in okd.items()}, negative=[dict(t=r['t'], A=r['A'], H=r['H'], p=r['p'], rest=r['rest'], price=r['price']) for r in neg],
                                            largest_possible_true_gain_units_among_nongains=max(bounds, default=0.0))
json.dump(out, open(sys.argv[2], 'w'), indent=1); print(json.dumps(out)[:3000])
