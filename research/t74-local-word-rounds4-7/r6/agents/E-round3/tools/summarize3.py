"""summarize3.py: per-target, per-round summary of runjob3 trees.  usage: summarize3.py OUT.json... > SUMMARY.json"""
import json, sys
from collections import Counter, defaultdict


def walk(node, acc, path='r'):
    k = node.get('round')
    if k is None: return
    a = acc[k]; a['models'] += 1; a['candidates'] += node.get('ncand', 0); a['proposals'] += node.get('proposals', 0)
    for key in node:
        if key.endswith('_stop'): a['stop:' + str(node[key])] += 1
    if node.get('stop'): a['stop:' + node['stop']] += 1
    a['cone_cuts'] += len(node.get(f'r{k}_cone_cuts', []))
    if node.get('diagnosis'): acc['diagnoses'].append(dict(round=k, **node['diagnosis']))
    for ch in node.get('children', []):
        if ch.get('exact'):
            a['exact'] += 1; pr = ch.get('price', {}); a['price:' + str(pr.get('status'))] += 1
            if isinstance(pr.get('delta'), int):
                acc['priced'].append(dict(round=k, delta=pr['delta'], status=pr.get('status'), terms=ch['terms']))
        if ch.get('next'): walk(ch['next'], acc, path + '.' + str(k))


out = {}
for f in sys.argv[1:]:
    d = json.load(open(f))
    for rec in d['results']:
        acc = defaultdict(Counter); acc['diagnoses'] = []; acc['priced'] = []
        walk(rec['tree'], acc)
        name = f.split('/')[-2] + ':' + '+'.join(f'{s}{i}' for s, i in rec['dels'])
        out[name] = dict(source=f, ddel=rec['ddel'], seconds=rec.get('seconds'), opts={k: rec['opts'][k] for k in
                         ('rounds', 'K', 'r1_diverse', 'merge_cuts') if k in rec['opts']} | {'exact_nogood': rec['opts'].get('exact_nogood', False)},
                         rounds={str(k): dict(v) for k, v in acc.items() if isinstance(k, int)},
                         diagnoses=acc['diagnoses'], priced=acc['priced'],
                         gains=[p for p in acc['priced'] if p['delta'] < 0])
json.dump(out, sys.stdout, indent=1, default=str); print()
