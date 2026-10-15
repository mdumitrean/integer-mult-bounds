"""good2run.py RG_OUT.json RUN.json (agent Q-blocks, r6): turn rowgen_q's exact, frame-feasible proposals into a
run5-format RUN file for r5 D's price3.py (compensation re-derived, rev3 harness with interval bounds)."""
import json, sys
rg = json.load(open(sys.argv[1]))
props = [g for g in rg.get('good', []) if isinstance(g.get('edit_ab'), dict) and 'delete' in g['edit_ab']]
json.dump([dict(dels=[tuple(d) for d in rg['meta']['dels']], proposals=props, source='rowgen_q')], open(sys.argv[2], 'w'), default=str)
print('proposals for pricing:', len(props))
