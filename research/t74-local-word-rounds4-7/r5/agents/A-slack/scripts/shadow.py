"""shadow.py: DIAGNOSTIC ONLY (unsound relaxations): optimal surrogate frames of a word with genuine checker rules dropped,
to show what each rule costs.  usage: shadow.py TOOLKIT WORD OUT.json"""
import gzip, json, sys
sys.path.insert(0, sys.argv[1])
import frames as F
from word import inline
from model import cone_caps
w = json.load(gzip.open(sys.argv[2])); costs = F.Costs("0.001679754956125544"); caps, _ = cone_caps(w); res = {}
for name, kw in (('checker_model', dict(caps=caps, cut_equality=True)), ('no_cone_caps', dict(caps={}, cut_equality=True)),
                 ('no_cut_equality', dict(caps=caps, cut_equality=False)), ('neither', dict(caps={}, cut_equality=False))):
    try:
        g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, **kw)
        r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
        res[name] = dict(cost=r['cost'], profile=dict(sorted(r['profile'].items())), certified=r['certified'])
    except Exception as e: res[name] = dict(error=repr(e)[:200])
    print(name, res[name], flush=True)
base = res['checker_model']['cost']
for k, v in res.items():
    if 'cost' in v: v['delta_vs_checker_model'] = v['cost'] - base
json.dump(res, open(sys.argv[3], 'w'), indent=1)
