"""tailcap.py: exact optimal frames of a word with the solver's end-of-B cone caps applied (a) to the last A/B vertex and
every tail vertex (toolkit default) and (b) only to the last A/B vertex, which is what audit_local.py and the native
audit check (end-of-B frames).  usage: tailcap.py TOOLKIT WORD OUT.json [B]"""
import gzip, json, sys, time
sys.path.insert(0, sys.argv[1])
import frames as F
from word import inline
from model import cone_caps
word_path, out_path = sys.argv[2], sys.argv[3]; b = sys.argv[4] if len(sys.argv) > 4 else "0.001679754956125544"
w = json.load(gzip.open(word_path)); costs = F.Costs(b)
caps, comp = cone_caps(w)
res = dict(word=word_path.split('scratchpad/')[-1], b=b, caps=len(caps), compensation_gates=len(comp))
for tc in (True, False):
    t0 = time.time()
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True, tail_caps=tc)
    tailv = [k for k, (regs, F0, sec, idx) in enumerate(g.nodes) if sec == 'tail' and any(r in caps for r in regs)]
    r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g, interval=True)
    iv = r['interval']
    res['tail_caps' if tc else 'endB_caps_only'] = dict(cost=r['cost'], profile=dict(sorted(r['profile'].items())), certified=r['certified'],
        variables=len(g.var), tail_vertices_on_capped_registers=len(tailv),
        interval_lower=str(iv['lower']), interval_upper=str(iv['upper']), seconds=round(time.time() - t0, 1))
    print(('tail_caps' if tc else 'endB_caps_only'), r['cost'], dict(sorted(r['profile'].items())), 'certified', r['certified'], 'vars', len(g.var), 'tail-capped', len(tailv), f'{time.time()-t0:.1f}s', flush=True)
a, c = res['tail_caps'], res['endB_caps_only']
res['delta_units_per_call'] = c['cost'] - a['cost']
json.dump(res, open(out_path, 'w'), indent=1); print('delta', res['delta_units_per_call'])
