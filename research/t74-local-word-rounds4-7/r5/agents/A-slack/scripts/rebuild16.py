"""rebuild16.py: rebuild r3 B-interact's 16 exact second-order words that exact frames rejected (lead1/CALIBRATION.json),
using B's own unchanged tools, and dump each word.  usage: (agi venv) rebuild16.py R3_B_DIR BASE_WORD OUT_DIR"""
import gzip, json, os, sys
Bdir, base_word, outdir = sys.argv[1:4]
sys.path.insert(0, os.path.join(Bdir, 'tools'))
from sk2 import *            # noqa: F401,F403  (B's round model: compile_AB, word_seq_insert, maps, H, F)
from runjob import exact
os.makedirs(outdir, exist_ok=True)
P = H.Pricer(base_word); bm = maps(P.base)
mk = lambda gg: list(gg[:5]) + [[]]
cal = json.load(open(os.path.join(Bdir, 'lead1/CALIBRATION.json'))); index = []
for n, c in enumerate(cal):
    recs = json.load(open(os.path.join(Bdir, 'runs', c['run'], 'out.json')))
    J = next(j for j, r in enumerate(recs) if [list(d) for d in r['dels']] == [list(d) for d in c['dels']])
    e2 = recs[J]['round1'][c['round1']]['round2'][c['round2']]
    W1 = compile_AB(P.base, dict(delete=[tuple(d) for d in c['dels']]))
    W2 = compile_AB(W1, word_seq_insert(W1, [(p, mk(g)) for p, g in e2['ins1']]))
    W3 = compile_AB(W2, word_seq_insert(W2, [(p, mk(g)) for p, g in e2['ins2']]))
    ok = exact(bm, W3)
    name = f"{n:02d}-{c['run']}-{'_'.join(s + str(i) for s, i in c['dels'])}-{c['round1']}-{c['round2']}.json.gz"
    with gzip.open(os.path.join(outdir, name), 'wt') as f: json.dump(W3, f)
    index.append(dict(name=name, run=c['run'], dels=c['dels'], round1=c['round1'], round2=c['round2'], exact=ok,
                      ins1=e2['ins1'], ins2=e2['ins2'], why_final_r3=c['why_final']))
    print(name, 'exact', ok, flush=True)
json.dump(index, open(os.path.join(outdir, 'INDEX.json'), 'w'), indent=1)
