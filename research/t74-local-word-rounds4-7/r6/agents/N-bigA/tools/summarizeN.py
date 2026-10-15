"""summarizeN.py: collect N-bigA's full-model runs (RUN-*.json), row-generation runs (RG-*.json) and exact prices
(PRICED-*.json) into out/EVIDENCE.json and out/TABLE.md.  Paths are relative to scratchpad/."""
import glob, json, os
N = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); out = os.path.join(N, 'out')
plan = json.load(open(os.path.join(out, 'PLAN.json')))
w = json.load(__import__('gzip').open(os.path.join(N, '..', '..', '..', 'r3', 'inputs', 'gauge44-word-566-554.json.gz')))
rel = json.load(open(os.path.join(N, '..', '..', '..', 'r3', 'agents', 'A-extra', 'out', 'relaxA-extra.json')))['results']
gain_of = lambda a: rel[str(a)]['delta']
def spec(name): return json.load(open(os.path.join(out, f'SPEC-{name}.json')))
full = []; rg = []; priced = []; gains = []
for f in sorted(glob.glob(os.path.join(out, 'RUN-*.json'))):
    name = os.path.basename(f)[4:-5]
    try: recs = json.load(open(f))
    except Exception: continue
    for rec in recs:
        a = rec['dels'][0][1]
        full.append(dict(run=name, method='full CP-SAT (run4.py)', deletion=f'A{a}', gate=w['A'][a][:5], class_gain=gain_of(a), ddel=rec.get('ddel'),
                         a_window=spec(name).get('a_windows'), tl=spec(name).get('tl'), K=spec(name).get('K'), ncand=rec.get('ncand'),
                         a_kept=rec.get('a_kept'), shape=rec.get('shape'), stop=rec.get('stop') or ('K limit' if len(rec.get('proposals', [])) >= spec(name).get('K', 3) else 'killed/incomplete'),
                         proposals=[p['terms'] for p in rec.get('proposals', [])], seconds=rec.get('seconds')))
for f in sorted(glob.glob(os.path.join(out, 'RG-*.json'))):
    name = os.path.basename(f)[3:-5]
    try: rec = json.load(open(f))[0]
    except Exception: continue
    g = rec['rowgen']; a = rec['dels'][0][1]; sp = spec('a3305' if name.startswith('cal') else (name[:-1] if name.endswith('b') else name))
    rg.append(dict(run=name, method='row generation (rowgen4.py)', deletion=f'A{a}', gate=w['A'][a][:5], class_gain=gain_of(a), ddel=rec.get('ddel'),
                   a_window=sp.get('a_windows'), ncand=g.get('ncand'), rows=g.get('rows'), status=g.get('status'),
                   iterations=g.get('iterations'), final_rows=g['log'][-1]['rows'] if g.get('log') else None,
                   proposals=[dict(terms=p['terms'], exact=p.get('exact'), frames_ok=p.get('frames_ok')) for p in g.get('proposals', [])],
                   seconds=g.get('seconds')))
for f in sorted(glob.glob(os.path.join(out, 'PRICED-*.json'))):
    for p in json.load(open(f)):
        pr = p['price']; e = dict(file=os.path.basename(f), deletion=f"A{p['dels'][0][1]}", terms=p['terms'], status=pr.get('status'),
                                  delta=pr.get('delta'), comp_gates=pr.get('comp_gates'), profile=pr.get('profile'), audit=(pr.get('audit') or {}).get('status'))
        priced.append(e)
        if isinstance(e['delta'], (int, float)) and e['delta'] < 0: gains.append(e)
ev = dict(agent='N-bigA', round='r6', b='0.001679754956125544', word='r3/inputs/gauge44-word-566-554.json.gz',
          model=('G-ainsert sk4.PRound4 first-order projected split-key model: inserts in an A window (+-350 gates around the deletion, or '
                 'the whole A section) and in B/tail, quarter-step |lambda|<=4, <=12 inserts, summed budget |gain|-1 and per-insert cap = '
                 'budget (#1957 oracle), cone-aware admission, no interaction ban; #1957 oracle sentinels (2^60) clipped to cost 1 so they '
                 'are never pruned; proposals checked on the true map (projected exactness) and the exact frame set test, then priced by '
                 'absorb.py (compensation re-derived, certified optimal frames).'),
          classes=plan['reps'], symmetry_sample=plan.get('symmetry_sample'), full_model_runs=full, rowgen_runs=rg, priced=priced, gains=gains)
json.dump(ev, open(os.path.join(out, 'EVIDENCE.json'), 'w'), indent=1, default=str)
rows = ['| Deletion | Class gain | Method | A window | Candidates | Verdict | Exact proposals (all relocations unless noted) | Exact prices |',
        '|---|---:|---|---|---:|---|---:|---|']
def prices(dl, tag):
    ds = [str(p['delta']) for p in priced if p['deletion'] == dl and tag in p['file']]
    return ', '.join(ds) if ds else '-'
for r in full:
    rows.append(f"| {r['deletion']} `{r['gate'][1]} += {r['gate'][2]}` | {r['class_gain']} | full model ({r['run']}) | {r['a_window']} | {r['ncand']} | {r['stop']} | {len(r['proposals'])} | {prices(r['deletion'], 'PRICED-' + r['run'])} |")
for r in rg:
    rows.append(f"| {r['deletion']} `{r['gate'][1]} += {r['gate'][2]}` | {r['class_gain']} | row generation ({r['run']}) | {r['a_window']} | {r['ncand']} | {r['status']} | {len(r['proposals'])} | {prices(r['deletion'], 'rg-' + r['run'])} |")
open(os.path.join(out, 'TABLE.md'), 'w').write('\n'.join(rows) + '\n'); print('\n'.join(rows)); print('gains', gains)
