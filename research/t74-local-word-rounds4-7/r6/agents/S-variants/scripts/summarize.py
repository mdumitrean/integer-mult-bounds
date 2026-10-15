"""summarize: collect all S-variants results into out/EVIDENCE.json (paths relative to scratchpad/)."""
import collections, glob, json, os
HERE = os.path.dirname(os.path.abspath(__file__)); W = os.path.dirname(HERE); OUT = os.path.join(W, 'out'); RUNS = os.path.join(W, 'runs')
ld = lambda p: json.load(open(p)) if os.path.exists(p) else None
E = dict(agent='S-variants', round='r6', b='0.001679754956125544', base_word='r3/inputs/gauge44-word-566-554.json.gz',
         extra_word='r3/inputs/extra-word-566-554.json.gz', extra_cost=11691748602)
V = ld(os.path.join(OUT, 'VARIANTS.json'))['results']
E['variants'] = dict(n=len(V), all_certified=all(v['status'] == 'ok' for v in V), costs=sorted({v['cost'] for v in V}),
                     deltas_vs_base=sorted({v['delta'] for v in V}), per_group=collections.Counter(v['label'] for v in V),
                     B_frames_changed=sorted({len(v['B_diff_base']) for v in V}), tail_changed=sorted({len(v['tail_diff_base']) for v in V}))
R = ld(os.path.join(OUT, 'RELAX-READERS.json'))['results']
sig = collections.defaultdict(set)
for r in R:
    if r['word'] in ('base', 'extra'): continue
    sig[r['group']].add((r['kind'][:6] if r['kind'].startswith('reader') else r['kind'], r.get('delta')))
E['reader_relaxations'] = {g: sorted(s, key=str) for g, s in sig.items()}
E['reader_relaxations_reference'] = dict(base=dict(reader=-8879, all12=-35516), extra_G2=dict(reader=-11938, all12=-47752))
RS = ld(os.path.join(OUT, 'RELAX-S.json')); outl = {}
for k, d in RS.items():
    nm, label = k.split('|'); base = RS[f'base|{label}']['results']
    diff = {i: (base[i].get('delta'), v.get('delta')) for i, v in d['results'].items() if (base[i].get('delta'), base[i].get('status')) != (v.get('delta'), v.get('status'))}
    outl[k] = dict(gates=len(d['results']), differs_from_base=diff)
E['group_region_relaxations'] = outl
for g in ('G12', 'G3'):
    p = os.path.join(OUT, f'RELAX-CLASSES-{g}.json')
    if os.path.exists(p):
        d = ld(p); E[f'class_relaxations_{g}'] = {nm: sorted({x.get('delta') for x in v['results'].values()}, key=lambda z: (z is None, z or 0)) for nm, v in d.items()}
RL = ld(os.path.join(OUT, 'RELOC16.json')) or []
E['relocations_outlier'] = dict(priced=len(RL), by_word={w: {f'{a}:{b}': n for (a, b), n in collections.Counter((r.get('status'), r.get('delta')) for r in RL if r['word'] == w).items()} for w in {r['word'] for r in RL}})
runs = {}
for p in sorted(glob.glob(os.path.join(RUNS, 'RUN-*.json'))):
    tag = os.path.basename(p)[4:-5]
    try: rr = json.load(open(p))
    except Exception: continue
    runs[tag] = [dict(dels=x.get('dels'), ddel=x.get('ddel'), ncand=x.get('ncand'), shape=x.get('shape'), stop=x.get('stop'),
                      proposals=len(x.get('proposals', []))) for x in rr]
E['split_key_runs'] = runs
pr = {}
for p in sorted(glob.glob(os.path.join(RUNS, 'PRICED-*.json'))):
    try: d = json.load(open(p))
    except Exception: continue
    items = d if isinstance(d, list) else d.get('results', [])
    pr[os.path.basename(p)[7:-5]] = {f'{a}:{b}': n for (a, b), n in collections.Counter(((x.get('price') or x).get('status'), (x.get('price') or x).get('delta')) for x in items if isinstance(x, dict)).items()}
E['priced_proposals'] = pr
E['gains'] = [dict(run=t, key=k, n=n) for t, c in pr.items() for k, n in c.items() if k.split(':')[1].lstrip('-').isdigit() and int(k.split(':')[1]) < 0] + \
             [r for r in RL if isinstance(r.get('delta'), int) and r['delta'] < 0]
json.dump(E, open(os.path.join(OUT, 'EVIDENCE.json'), 'w'), indent=1, default=str)
print(json.dumps({k: (v if k in ('variants', 'gains', 'relocations_outlier') else '...') for k, v in E.items()}, default=str)[:1500])
