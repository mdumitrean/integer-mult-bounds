"""relax_S: uncompensated deletion relaxation (screen; base cone caps) of every B add gate that reads or writes a register
of the variant's group region S = members + readers, on representative variants, on the base word and on the extra word.
A difference from the base word at the same gate (beyond the 12 early reads) would be a new structure.
usage: relax_S.py OUT.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import harness as H
from compat import deadline, Timeout
OUT = os.path.join(os.path.dirname(__file__), '..', 'out'); WORDS = os.path.join(os.path.dirname(__file__), '..', 'words')
G = json.load(open(os.path.join(OUT, 'GROUPS.json')))['groups']
reps = {'start:619..623': ['619-623-1-24-132-260', '619-623-24-97-133-261'], 'start:627..631': ['627-631-24-35-69-391'],
        'start:651..655': ['651-655-30-96-139-267', '651-655-7-25-235-363']}
words = [('base', os.path.join(C.INP, 'gauge44-word-566-554.json.gz')), ('extra', os.path.join(C.INP, 'extra-word-566-554.json.gz'))]
res = {}; t0 = time.time()
def relax(Pr, dels):
    w1 = H.compile_edits(Pr.base, dict(delete=dels))
    try:
        with deadline(120):
            g = C.F.Graph(C.inline(w1, True), check_literal=False, tail_mutable=True, caps=Pr.caps, cut_equality=True)
            r = C.F.optimal_frames(C.inline(w1, True), Pr.costs, check_literal=False, graph=g)
        return dict(delta=r['cost'] - Pr.base_cost, cert=r['certified'], prof=dict(sorted(r['profile'].items())))
    except C.F.Infeasible: return dict(status='infeasible')
    except Timeout: return dict(status='timeout')
gates = {}
bw = C.base_word()
for label, g in G.items():
    Sreg = set(g['members']) | set(g['readers'])
    gates[label] = [i for i, x in enumerate(bw['B']) if x[0] == 'add' and (x[1] in Sreg or x[2] in Sreg)]
print({k: len(v) for k, v in gates.items()}, flush=True)
todo = [(nm, p, label) for nm, p in words for label in G] + [(nm, os.path.join(WORDS, nm + '.json.gz'), label) for label, nms in reps.items() for nm in nms]
for nm, p, label in todo:
    Pr = H.Pricer(p, b=C.B, check_literal=True); out = {}
    for i in gates[label]: out[i] = relax(Pr, [i])
    res[f'{nm}|{label}'] = dict(base_cost=Pr.base_cost, results={str(k): v for k, v in out.items()})
    print(nm, label, len(out), f'{time.time()-t0:.0f}s', flush=True)
    json.dump(res, open(os.path.join(OUT, sys.argv[1]), 'w'))
print('done', f'{time.time()-t0:.0f}s')
