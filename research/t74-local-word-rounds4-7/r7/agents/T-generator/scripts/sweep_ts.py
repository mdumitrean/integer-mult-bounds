"""sweep_ts.py: run tscreen.py for every full-c1 narrowable helper; 4 concurrent processes, 900 s timeout each.
usage: sweep_ts.py WORD NARROW.jsonl TOOLKIT OUTDIR"""
import json, subprocess, sys, os, time
from concurrent.futures import ThreadPoolExecutor
word, narrow, tk, outd = sys.argv[1:5]
here = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(narrow) if l.strip()]
Q = sorted({r['q'] for r in rows if r.get('status') == 'ok' and r.get('delta') == -2116454})
def job(q):
    out = os.path.join(outd, f'{q}.json')
    if os.path.exists(out): return q, 'cached'
    t0 = time.time()
    try:
        p = subprocess.run([sys.executable, '-B', os.path.join(here, 'tscreen.py'), word, narrow, tk, str(q), out, '1'],
                           capture_output=True, text=True, timeout=900, env=dict(os.environ))
        st = 'ok' if p.returncode == 0 else 'rc%d' % p.returncode
    except subprocess.TimeoutExpired: st = 'timeout'
    return q, f'{st} {time.time()-t0:.0f}s'
with ThreadPoolExecutor(4) as ex:
    for q, st in ex.map(job, Q): print(q, st, flush=True)
agg = {}
for q in Q:
    p = os.path.join(outd, f'{q}.json')
    if os.path.exists(p):
        d = json.load(open(p)); agg[q] = {k: d[k] for k in ('leak', 'candidates', 'rank', 'in_span', 'nops', 'dyadic')}
json.dump(agg, open(os.path.join(outd, 'SUMMARY.json'), 'w'), indent=1)
print('in_span:', [q for q, a in agg.items() if a['in_span']], 'max rank', max((a['rank'] for a in agg.values()), default=0), flush=True)
