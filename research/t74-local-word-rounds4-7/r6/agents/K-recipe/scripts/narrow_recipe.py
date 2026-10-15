"""narrow_recipe.py: recipe-level narrowing of one width-9 helper exactly as the FOUR-RECIPE mechanism changes entrance
labels: start_extra[q] := basis, scalar program unchanged, frames re-solved and written back with the #1186 toolkit.
usage: narrow_recipe.py TOOLKIT WORD q BASIS(comma) B OUT.json.gz REPORT.json"""
import sys, json, gzip
tk, wordp, q, basis, b, outp, repp = sys.argv[1:8]
sys.path.insert(0, tk)
import frames as F, harness as H
from word import inline
from model import cone_caps
from writeback import write_back
w = json.loads(gzip.decompress(open(wordp, 'rb').read()))
assert q not in w['start_extra'], 'already entering'
w['start_extra'][q] = [int(x) for x in basis.split(',')]
caps, comp = cone_caps(w)
reads_q = [g for g in comp if g[2] == int(q)]
costs = F.Costs(b)
g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
w2 = write_back(w, g, r['assign'])
open(outp, 'wb').write(gzip.compress(json.dumps(w2, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
rep = dict(q=int(q), basis=w['start_extra'][q], certified=r['certified'], cost=r['cost'], profile={str(k): v for k, v in sorted(r['profile'].items())},
           compensation_gates=len(comp), compensation_reads_q=len(reads_q), width_inventory=w2['report'].get('width_inventory'))
json.dump(rep, open(repp, 'w'), indent=1); print(json.dumps(rep))
