"""summarize: collect r4 A-reroute evidence into RESULTS.json."""
import json, glob, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); O = os.path.join(HERE, '..', 'out')
PIV = [439, 444, 438, 434, 436, 446, 226, 228, 230, 231, 232, 236, 238]
res = dict(agent='A-reroute', round='r4', b='0.001679754956125544', words={'base': 'r3/inputs/gauge44-word-566-554.json.gz', 'extra': 'r3/inputs/extra-word-566-554.json.gz'})
aw = {}
for wn in ('base', 'extra'):
    for K in (4, 5):
        for q in PIV:
            f = os.path.join(O, f'AWIN-{wn}-{q}-K{K}.json')
            if os.path.exists(f):
                a = json.load(open(f)); aw.setdefault(f'{wn}-K{K}', {})[q] = dict(atoms=a['natoms'], atoms_with_A_slot=a['natomsA'], solutions=a['nsols'], candidates=len(a['cands']),
                    budget_hit=a.get('budget_hit'), dfs_nodes=a.get('dfs_nodes'), negative=sum(1 for c in a['cands'] if (c['price'].get('delta') or 0) < 0))
res['a_window_redelivery'] = aw
car = {}
for f in glob.glob(os.path.join(O, 'CARRIER-base-*.json')):
    for q, r in json.load(open(f)).items():
        car[q] = dict(reads=len(r['reads']), singles=sum(len(v['singles']) for v in r['reads'].values()), pairs=sum(len(v['pairs']) for v in r['reads'].values()), priced=len(r['priced']))
res['carrier_substitution'] = car
am = {}
for f in glob.glob(os.path.join(O, 'AMOVE-base-*.json')):
    recs = json.load(open(f)); st = collections.Counter()
    for r in recs:
        p = r['price']; d = p.get('delta')
        st[(p.get('status'), 'neg' if (d or 0) < 0 else ('zero' if d == 0 else ('pos' if d else 'none')))] += 1
    am[os.path.basename(f)] = dict(candidates=len(recs), exact=sum(r['exact'] for r in recs), status={f'{a}/{b}': c for (a, b), c in st.items()})
res['a_gate_retimings'] = am
fs = {}
for f in glob.glob(os.path.join(O, 'FORCEDSCAN-base-*.json')):
    for q, r in json.load(open(f)).items():
        fs[q] = {y: dict(slots=v['slots'], feasible=v['feasible'], best=(dict(sec=v['best']['sec'], pos=v['best']['pos'], delta=v['best']['delta']) if v['best'] else None)) for y, v in r['ports'].items()}
res['forced_single_meet'] = fs
f = os.path.join(O, 'FORCEDMEET-base.json')
if os.path.exists(f):
    res['forced_meet_after_last_gate'] = {q: dict(deleted=r['deleted'], single={y: v.get('status') for y, v in r['single'].items()}, joint=r['joint'].get('status')) for q, r in json.load(open(f)).items()}
f = os.path.join(O, 'ASLOTS-base.json')
if os.path.exists(f): res['a_window_port_slots'] = {q: {y: dict(cut_target_level=v['cut_target_level'], slots_feasible=v['slots_feasible'], slots_tried=v['slots_tried']) for y, v in r['ports'].items()} for q, r in json.load(open(f)).items()}
res['structure'] = dict(A_gates_touching_ports=0, cut_gates=176, cut_gates_writing_ports=176, target_levels_nonempty=0, port_centers=0,
                        note='both words; ports have no A vertices and empty cut frames, so with cut equality no A gate may write a port; the cut gates are outside the priced frame graph')
json.dump(res, open(os.path.join(HERE, '..', 'RESULTS.json'), 'w'), indent=1, default=str)
print(json.dumps({k: (v if k not in ('a_window_redelivery', 'forced_single_meet', 'a_window_port_slots') else '...') for k, v in res.items()}, default=str)[:1500])
