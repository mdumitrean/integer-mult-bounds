"""summarize.py (agent Q-blocks, r6): collect relaxations, block-search runs and pricings into out/EVIDENCE.json."""
import glob, json, os, sys
Q = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
rel = json.load(open(os.path.join(Q, 'out', 'RELAX-SUMMARY.json')))['rows']
runs = {}; priced = []; gains = []
for f in sorted(glob.glob(os.path.join(Q, 'runs', 'RUN-*.json'))):
    tag = os.path.basename(f)[4:-5]
    try: r = json.load(open(f))
    except Exception: continue
    for rec in r:
        runs[tag] = dict(dels=rec['dels'], ddel=rec.get('ddel'), ncand=rec.get('ncand'), sentinel_kept=rec.get('sentinel_kept'),
                         target_rank=rec.get('target_rank'), shape=rec.get('shape'), stop=rec.get('stop'),
                         proposals=len(rec.get('proposals', [])), cuts=dict(inexact=sum(1 for c in rec.get('cuts', []) if c['kind'] == 'inexact'),
                         frames=sum(1 for c in rec.get('cuts', []) if c['kind'] == 'frames')), seconds=rec.get('seconds'))
for f in sorted(glob.glob(os.path.join(Q, 'runs', 'PRICED-*.json'))):
    tag = os.path.basename(f)[7:-5]
    for p in json.load(open(f)):
        pr = p['price']; e = dict(tag=tag, dels=p['dels'], terms=p['terms'], status=pr.get('status'), delta=pr.get('delta'),
                                  comp_gates=pr.get('comp_gates'), gain_certified=pr.get('gain_certified'))
        priced.append(e)
        if isinstance(e['delta'], (int, float)) and e['delta'] < 0: gains.append(e)
ev = dict(agent='Q-blocks', round='r6', word='r3/inputs/gauge44-word-566-554.json.gz', b='0.001679754956125544',
          relaxations=dict(jobs=len(rel), superadditive=[r for r in rel if r[5] is not None and r[5] < 0]),
          runs=runs, priced=priced, gains=gains)
json.dump(ev, open(os.path.join(Q, 'out', 'EVIDENCE.json'), 'w'), indent=1)
print('runs', len(runs), {t: (v['stop'], v['proposals'], v['cuts']) for t, v in runs.items()})
print('priced', len(priced), 'gains', gains)
