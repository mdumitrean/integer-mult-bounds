"""summarize.py: collect run3 outputs (out/RUN-*.json) and price3 outputs into out/EVIDENCE.json and out/TABLE.md."""
import glob, json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(os.path.dirname(HERE), 'out')
rows = []; tot = collections.Counter()
for f in sorted(glob.glob(os.path.join(OUT, 'RUN-*.json'))):
    for r in json.load(open(f)):
        cuts = collections.Counter(c['kind'] for c in r.get('cuts', []))
        rows.append(dict(run=os.path.basename(f)[4:-5], dels=r['dels'], gate=r.get('gates'), ddel=r.get('ddel'), target_rank=r.get('target_rank'),
                         ncand=r.get('ncand'), cone_rejected=r.get('cone_rejected'), shape=r.get('shape'), proposals=len(r.get('proposals', [])),
                         exact=sum(1 for e in r.get('proposals', []) if e.get('exact')), inexact_cuts=cuts.get('inexact', 0),
                         frame_cuts=cuts.get('frames', 0), stop=r.get('stop'), seconds=r.get('seconds')))
        tot['jobs'] += 1; tot['proposals'] += rows[-1]['proposals']; tot['inexact_cuts'] += rows[-1]['inexact_cuts']; tot['frame_cuts'] += rows[-1]['frame_cuts']
        tot['stop:' + str(r.get('stop'))] += 1
priced = []
for f in sorted(glob.glob(os.path.join(OUT, 'PRICED-*.json'))):
    for x in json.load(open(f)): priced.append(dict(src=os.path.basename(f), dels=x['dels'], status=x['price'].get('status'), delta=x['price'].get('delta'),
                                                   audit=(x['price'].get('audit') or {}).get('status')))
calib = {}
for nm in ('CALIB-ABSORB.json',):
    p = os.path.join(OUT, 'calib', nm)
    if os.path.exists(p): calib['absorb'] = json.load(open(p))
p = os.path.join(OUT, 'CALIB-k554-PRICED.json')
if os.path.exists(p): calib['k554_priced'] = [dict(terms=x['terms'], status=x['price']['status'], delta=x['price']['delta'], comp=x['price'].get('comp_gates'),
                                                    audit=(x['price'].get('audit') or {}).get('status')) for x in json.load(open(p))]
ev = dict(totals=dict(tot), jobs=rows, priced=priced, gains=[x for x in priced if isinstance(x['delta'], (int, float)) and x['delta'] < 0], calibration=calib)
json.dump(ev, open(os.path.join(OUT, 'EVIDENCE.json'), 'w'), indent=1, default=str)
with open(os.path.join(OUT, 'TABLE.md'), 'w') as t:
    t.write('| Run | Deletion | Gate | ddel | T rank (N,P) | Candidates | Shape | Inexact cuts | Frame cuts | Exact proposals | Outcome |\n|---|---|---|---:|---|---:|---|---:|---:|---:|---|\n')
    for r in rows:
        t.write(f"| {r['run']} | {r['dels']} | {r['gate']} | {r['ddel']} | {r['target_rank']} | {r['ncand']} | {r['shape']} | {r['inexact_cuts']} | {r['frame_cuts']} | {r['exact']} | {r['stop'] or ('proposals' if r['proposals'] else '-')} |\n")
print(json.dumps(dict(tot), indent=1)); print('gains', ev['gains'])
