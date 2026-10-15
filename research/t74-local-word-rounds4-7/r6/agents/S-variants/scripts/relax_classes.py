"""relax_classes: relaxation of the group-region gates that carry large deletion gains (the -20,893/-19,037/-9,850
classes inside S) on EVERY variant of the given groups.  usage: relax_classes.py OUT.json GROUPLABEL [GROUPLABEL ...]"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import harness as H
from compat import deadline, Timeout
OUT = os.path.join(os.path.dirname(__file__), '..', 'out'); WORDS = os.path.join(os.path.dirname(__file__), '..', 'words')
RS = json.load(open(os.path.join(OUT, 'RELAX-S.json'))); V = json.load(open(os.path.join(OUT, 'VARIANTS.json')))['results']
res = {}; t0 = time.time(); outp = os.path.join(OUT, sys.argv[1])
for label in sys.argv[2:]:
    base = RS[f'base|{label}']['results']
    gates = sorted(int(i) for i, v in base.items() if isinstance(v.get('delta'), int) and v['delta'] < 0)
    for v in [x for x in V if x['label'] == label]:
        Pr = H.Pricer(os.path.join(WORDS, v['name'] + '.json.gz'), b=C.B, check_literal=True); out = {}
        for i in gates:
            w1 = H.compile_edits(Pr.base, dict(delete=[i]))
            try:
                with deadline(120):
                    g = C.F.Graph(C.inline(w1, True), check_literal=False, tail_mutable=True, caps=Pr.caps, cut_equality=True)
                    r = C.F.optimal_frames(C.inline(w1, True), Pr.costs, check_literal=False, graph=g)
                out[str(i)] = dict(delta=r['cost'] - Pr.base_cost, cert=r['certified'])
            except C.F.Infeasible: out[str(i)] = dict(status='infeasible')
            except Timeout: out[str(i)] = dict(status='timeout')
        res[v['name']] = dict(label=label, basis=v['basis'], results=out)
        print(v['name'], sorted({x.get('delta') for x in out.values()}, key=lambda z: (z is None, z or 0)), f'{time.time()-t0:.0f}s', flush=True)
        json.dump(res, open(outp, 'w'))
print('done', f'{time.time()-t0:.0f}s', flush=True)
