"""audit_swap: build one swapped word (exact optimal frames written back), confirm its width inventory equals the input
word's, and run main's unchanged audit_local.py --main on it.
usage: audit_swap.py TOOLKIT WORD.json.gz MAIN OUTDIR NAME NARROW_JSON WIDEN_JSON
  NARROW_JSON / WIDEN_JSON: {"members": [...], "basis": [...], "side": "start"|"end"}"""
import os, sys, json, gzip, copy, subprocess, collections
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W, wcore as K
from writeback import write_back
WORD, MAIN, OUTDIR, NAME = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]; nx, ny = json.loads(sys.argv[6]), json.loads(sys.argv[7])
base = K.load(WORD); costs = F.Costs(K.B); rb = K.solve(base, costs)[0]
w = copy.deepcopy(base)
for z in (nx, ny):
    for q in z['members']: (w['start_extra'] if z.get('side', 'start') == 'start' else w['helper_final'])[str(q)] = z['basis']
r, g, nc = K.solve(w, costs); w2 = write_back(w, g, r['assign'])
inv = lambda x: dict(sorted(collections.Counter(W.recount(x)[2]).items()))
p = os.path.join(OUTDIR, NAME + '.json.gz'); gzip.open(p, 'wt').write(json.dumps(w2, sort_keys=True))
aud = os.path.join(OUTDIR, 'AUDIT-' + NAME + '.json')
rc = subprocess.run([sys.executable, '-B', os.path.join(MAIN, 'research/gauge44-frames-x/independent/audit_local.py'), '--word', p, '--output', aud, '--main', MAIN],
                    cwd=MAIN, capture_output=True, text=True).returncode
res = dict(name=NAME, delta=r['cost'] - rb['cost'], certified=r['certified'], profile=dict(sorted(r['profile'].items())), comp_gates=nc,
           inventory_in=inv(base), inventory_out=inv(w2), inventory_unchanged=inv(base) == inv(w2), audit_exit=rc,
           audit_status=(json.load(open(aud)).get('status') if os.path.exists(aud) else None))
print(json.dumps(res)); json.dump(res, open(os.path.join(OUTDIR, 'RESULT-' + NAME + '.json'), 'w'), indent=1)
