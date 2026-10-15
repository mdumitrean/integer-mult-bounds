"""summarize.py: collect run5/price3 results of agent M-bigB into out/EVIDENCE.json and out/TABLE.md."""
import json, glob, os, collections
M = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
jobs = {j['rep']: j for j in json.load(open(os.path.join(M, 'out', 'JOBS.json')))}
rows = []; priced = []; gains = []
for f in sorted(glob.glob(os.path.join(M, 'runs', 'RUN-*.json'))):
    name = os.path.basename(f)[4:-5]
    if ' ' in name or name.endswith('-checks') or not (name.startswith('B') or name.startswith('R') or name == 't1061'): continue
    try: recs = json.load(open(f))
    except Exception: continue
    capf = os.path.join(M, 'runs', ('t1061' if name == 't1061' else name) + '.cap.log'); cap = ''
    if os.path.exists(capf):
        ls = [l for l in open(capf) if l.startswith('[capped]')]; cap = ls[-1].strip() if ls else 'running'
    for r in recs:
        bi = r['dels'][0][1]; j = jobs.get(bi, {})
        kinds = collections.Counter(c['kind'] for c in r.get('cuts', []))
        rows.append(dict(run=name, rerun=name.startswith('R') and not name.startswith('RG'), rowgen=name.startswith('RG'), nobans=name == 't1061', rep=bi, delta_class=j.get('delta'), shape=j.get('shape'), n_members=j.get('n_members'), gate=r.get('gates'),
                         ddel=r.get('ddel'), budget=-r['ddel'] - 1 if r.get('ddel') is not None else None, target_rank=r.get('target_rank'),
                         ncand=r.get('ncand'), sentinel_kept=r.get('sentinel_kept'), sentinel_cone_rejected=r.get('sentinel_cone_rejected'),
                         shape_ok=r.get('shape'), stop=r.get('stop'), cuts=dict(kinds), proposals=len(r.get('proposals', [])),
                         seconds=r.get('seconds'), capped=cap))
for f in sorted(glob.glob(os.path.join(M, 'runs', 'PRICED-*.json'))):
    try: ps = json.load(open(f))
    except Exception: continue
    for p in ps:
        pr = p['price']; e = dict(file=os.path.basename(f), dels=p['dels'], terms=p['terms'], est=p['est'], status=pr.get('status'),
                                  delta=pr.get('delta'), comp_gates=pr.get('comp_gates'), audit=(pr.get('audit') or {}).get('status'),
                                  gain_certified=pr.get('gain_certified'))
        priced.append(e)
        if isinstance(e['delta'], (int, float)) and e['delta'] < 0: gains.append(e)
def stat(r):
    if r['stop'] == 'INFEASIBLE': return 'INFEASIBLE'
    if r['shape_ok'] is False: return 'shape-infeasible'
    if r['proposals']: return f"{r['proposals']} exact proposals"
    return f"stop {r['stop']} (budget/cut limit)" if r['stop'] or r['capped'] else 'unknown'
for r in rows: r['status'] = stat(r)
ev = dict(agent='M-bigB', round='r6', word='r3/inputs/gauge44-word-566-554.json.gz', b='0.001679754956125544',
          jobs_total=len(jobs), jobs_run=len(rows), status_counts=dict(collections.Counter(r['status'] for r in rows)),
          rows=sorted(rows, key=lambda r: (r['ddel'] or 0, r['rep'], r['run'])), priced=priced, gains=gains)
json.dump(ev, open(os.path.join(M, 'out', 'EVIDENCE.json'), 'w'), indent=1, default=str)
with open(os.path.join(M, 'out', 'TABLE.md'), 'w') as t:
    t.write('| Run | Class Δ | Shape | Members | ddel | Cand | Sentinels kept | Status | Cuts | s |\n|---|---:|---|---:|---:|---:|---:|---|---|---:|\n')
    for r in ev['rows']:
        t.write(f"| {r['run']} | {r['delta_class']} | {'/'.join(r['shape'] or [])} | {r['n_members']} | {r['ddel']} | {r['ncand']} | {r['sentinel_kept']} | {r['status']} | {r['cuts']} | {r['seconds']} |\n")
print('jobs run', len(rows), 'of', len(jobs), ev['status_counts'], 'priced', len(priced), 'gains', len(gains))
