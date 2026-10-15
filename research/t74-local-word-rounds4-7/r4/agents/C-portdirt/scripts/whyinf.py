"""whyinf.py: infeasibility reasons for sampled family-S candidates (one per read/source pair), plus a frame diagnosis:
the alternative source's frames on the BASE word's optimal assignment around the insert, and the port's end frame.
usage: whyinf.py WORD.json.gz S.jsonl OUT.json"""
import json, os, sys, collections
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main'))
os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
P = H.Pricer(sys.argv[1], check_literal=True, interval=False)
rs = [json.loads(l) for l in open(sys.argv[2]) if l.strip()]
seen = set(); out = []
for r in rs:
    k = (r['B'], r['y'])
    if k in seen: continue
    seen.add(k)
    ed = dict(delete=[r['B']], insert=[(r['p'], ['add', r['t'], r['y'], r['c'][0], r['c'][1], []])])
    w1 = H.compile_edits(P.base, ed); caps, comp = cone_caps(w1)
    rec = dict(B=r['B'], t=r['t'], s=r['s'], y=r['y'], p=r['p'], comp_changed=comp != P.compensation, comp_gates=len(comp),
               caps_changed=caps != P.caps, ncaps=len(caps), ncaps_base=len(P.caps))
    try:
        F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True); rec['why'] = 'graph-ok?'
    except F.Infeasible as e: rec['why'] = str(e.args[0])[:300] if e.args else ''
    # deletion only (same caps as the base): is the read's removal itself feasible?
    w0 = H.compile_edits(P.base, dict(delete=[r['B']]))
    try:
        F.Graph(inline(w0, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True); rec['deletion_only'] = 'feasible'
    except F.Infeasible as e: rec['deletion_only'] = 'infeasible'
    # same insert but with the base caps (isolates the caps change)
    try:
        F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True); rec['with_base_caps'] = 'feasible'
    except F.Infeasible as e: rec['with_base_caps'] = 'infeasible: ' + (str(e.args[0])[:120] if e.args else '')
    out.append(rec); print(rec, flush=True)
json.dump(out, open(sys.argv[3], 'w'), indent=1)
print(collections.Counter(x['why'].split(' at ')[0][:60] for x in out))
