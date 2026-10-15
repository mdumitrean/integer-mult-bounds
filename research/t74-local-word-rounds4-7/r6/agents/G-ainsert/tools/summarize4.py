"""summarize4.py: collect agent G-ainsert's runs into out/EVIDENCE.json and out/TABLE.md."""
import glob, json, os
G = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); O = os.path.join(G, 'out')
ev = dict(agent='G-ainsert', round='r6', word='r3/inputs/gauge44-word-566-554.json.gz', b='0.001679754956125544', runs={}, priced=[], calibration={})
rows = []
for f in sorted(glob.glob(os.path.join(O, 'RUN-*.json'))):
    run = os.path.basename(f)[4:-5]
    if run.startswith('calib'): continue
    spec = json.load(open(os.path.join(O, f'SPEC-{run}.json')))
    recs = json.load(open(f)); ev['runs'][run] = dict(a_windows=spec.get('a_windows'), opts={k: v for k, v in spec.items() if k not in ('jobs', 'known')}, jobs=[])
    for r in recs:
        j = dict(dels=r['dels'], gates=r.get('gates'), ddel=r.get('ddel'), ncand=r.get('ncand'), a_kept=r.get('a_kept'), shape=r.get('shape'),
                 stop=r.get('stop'), proposals=[dict(terms=p['terms'], est=p['est']) for p in r.get('proposals', [])],
                 cuts=dict(inexact=sum(1 for c in r.get('cuts', []) if c['kind'] == 'inexact'), frames=sum(1 for c in r.get('cuts', []) if c['kind'] == 'frames')),
                 seconds=r.get('seconds'))
        ev['runs'][run]['jobs'].append(j)
        out = 'shape-infeasible' if not j['shape'] else (f"{len(j['proposals'])} proposal(s), then {j['stop']}" if j['proposals'] else str(j['stop']))
        rows.append(f"| {run} | {j['dels']} | {j['gates'][0] if j['gates'] else ''} | {j['ddel']} | {spec.get('a_windows')} | {j['ncand']} | {j['a_kept']} | {out} |")
for f in sorted(glob.glob(os.path.join(O, 'PRICED-*.json'))) + [os.path.join(O, 'CALIB-k554-PRICED.json')]:
    if os.path.exists(f):
        for p in json.load(open(f)): ev['priced'].append(dict(file=os.path.basename(f), dels=p['dels'], terms=p['terms'], status=p['price'].get('status'), delta=p['price'].get('delta'), comp_gates=p['price'].get('comp_gates'), audit=(p['price'].get('audit') or {}).get('status')))
if os.path.exists(os.path.join(O, 'CALIB-AID.json')): ev['calibration']['a_insert_identity'] = json.load(open(os.path.join(O, 'CALIB-AID.json')))
if os.path.exists(os.path.join(O, 'CALIB-k554.json')):
    c = json.load(open(os.path.join(O, 'CALIB-k554.json')))[0]
    ev['calibration']['k554'] = dict(a_windows=[[3000, 3451]], a_kept=c.get('a_kept'), known_in_candidates=c.get('known_in_candidates'), known_fixed_status=c.get('known_fixed_status'), proposals=[p['terms'] for p in c['proposals']])
for f in glob.glob(os.path.join(O, 'SHAPE-DIAG-*.json')): ev['shape_diag_' + os.path.basename(f)[11:-5]] = json.load(open(f))
ev['gains'] = [p for p in ev['priced'] if isinstance(p.get('delta'), (int, float)) and p['delta'] < 0 and not p['file'].startswith('CALIB')]
json.dump(ev, open(os.path.join(O, 'EVIDENCE.json'), 'w'), indent=1, default=str)
open(os.path.join(O, 'TABLE.md'), 'w').write('| Run | Deletion | Gate | Deletion price | A windows | Candidates | A-kept | Outcome |\n|---|---|---|---:|---|---:|---:|---|\n' + '\n'.join(rows) + '\n')
print('\n'.join(rows)); print('gains:', ev['gains'])
