"""analyze: summarize SWEEP-base.jsonl (single one-level width changes) and JOINT-base.jsonl (group changes).
usage: analyze.py OUTDIR  -> prints and writes OUTDIR/SUMMARY.json"""
import json, sys, collections
O = sys.argv[1]
C = [2116454, 4227983, 6337656, 8446126, 10553701, 12660563, 14766833, 16872596, 18977915]   # c[1..9] at b
EXTRA4 = 8458352; FLOOR = C[8] - C[7]; KAPPA_PER_UNIT_CALL = 4.144e-8 / (1855 * 666)
def load(p):
    try: return [json.loads(l) for l in open(p) if l.strip()]
    except FileNotFoundError: return []
S = load(O + '/SWEEP-base.jsonl'); J = load(O + '/JOINT-base.jsonl')
out = dict(costs_c1_to_c9=C, extra_word_4_upgrades=EXTRA4, extra_per_upgrade=EXTRA4 / 4, marginal_floor_c9_minus_c8=FLOOR)
single = {}
for kind in ('up-start', 'up-end', 'down-start'):
    rs = [r for r in S if r['kind'] == kind]; ok = [r for r in rs if r['status'] == 'ok']
    single[kind] = dict(n=len(rs), status=dict(collections.Counter(r['status'] for r in rs)),
                        delta_counts=dict(sorted(collections.Counter(r['delta'] for r in ok).items())),
                        helpers=len({r['q'] for r in rs}))
out['single'] = single
groups = collections.defaultdict(list)
for r in J: groups[r['label']].append(r)
gsum = {}
for label, rs in sorted(groups.items()):
    ok = [r for r in rs if r['status'] == 'ok']
    best = min(ok, key=lambda r: r['delta']) if ok else None
    gsum[label] = dict(n=len(rs), status=dict(collections.Counter(r['status'] for r in rs)), members=rs[0]['members'] if label.startswith(('start', 'end', 'down')) else None,
                       min_delta=best['delta'] if best else None, max_delta=max(r['delta'] for r in ok) if ok else None,
                       best_basis=best['basis'] if best else None, best_profile=best['profile'] if best else None,
                       delta_counts=dict(sorted(collections.Counter(r['delta'] for r in ok).items())))
    if label.startswith('g2-subset'): gsum[label]['by_members'] = {str(r['members']): r.get('delta') for r in rs}
out['joint'] = gsum
up = {k: v for k, v in gsum.items() if k.startswith(('start:', 'end:')) and v['min_delta'] is not None}
down = {k: v for k, v in gsum.items() if k.startswith('down:') and v['min_delta'] is not None}
if up:
    cheapest = min(up.items(), key=lambda kv: kv[1]['min_delta'])
    out['cheapest_group_upgrade'] = dict(label=cheapest[0], delta=cheapest[1]['min_delta'], vs_extra=cheapest[1]['min_delta'] - EXTRA4,
                                         kappa_if_extra_replaced=-(cheapest[1]['min_delta'] - EXTRA4) * 417 * KAPPA_PER_UNIT_CALL)
if up and down:
    best_down = min(down.items(), key=lambda kv: kv[1]['min_delta'])   # most negative = largest saving
    net = cheapest[1]['min_delta'] + best_down[1]['min_delta']
    out['best_same_inventory_swap'] = dict(narrow=best_down[0], narrow_delta=best_down[1]['min_delta'], widen=cheapest[0], widen_delta=cheapest[1]['min_delta'],
                                           net_delta_per_call=net, note='additive estimate; a gain needs a joint re-price')
json.dump(out, open(O + '/SUMMARY.json', 'w'), indent=1, sort_keys=True)
print(json.dumps({k: out[k] for k in out if k != 'joint'}, indent=1)[:3000])
for label, v in gsum.items(): print(label, v['n'], v['status'], 'min', v['min_delta'], 'max', v['max_delta'], 'deltas', list(v['delta_counts'].items())[:4])
