"""Price peephole alternatives with the rev3 harness (base word). args: out.jsonl budget_seconds infile... ; priority order:
L < k (reductions), k=3 rewrites, k=2 rewrites of length 2, then the rest (big-deletion windows first)."""
import os, sys, json, time, resource, multiprocessing as mp
from fractions import Fraction as Q
S = os.environ['SCR']; sys.path.insert(0, S + '/r3/toolkit-rev3')
out, budget, infiles = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
WORD = os.environ.get('WORD', S + '/r3/inputs/gauge44-word-566-554.json.gz')
P = None
def init():
    global P
    import harness as H
    try: resource.setrlimit(resource.RLIMIT_RSS, (6 << 30, 6 << 30))
    except Exception: pass
    P = H.Pricer(WORD, b='0.001679754956125544', check_literal=True, interval=False)
def gate(t):
    if t[0] == 'add':
        c = Q(t[3]); return ['add', t[1], t[2], c.numerator, c.denominator, []]
    c = Q(t[2]); return ['scale', t[1], c.numerator, c.denominator, []]
def job(r):
    i, k = r['i'], r['k']
    ed = dict(delete=list(range(i, i + k)), insert=[[i, gate(t)] for t in r['alt']])
    t0 = time.time(); p = P.price(ed, timeout=90)
    return dict(r, status=p.get('status'), delta=p.get('delta'), profile=p.get('profile'), audit=p.get('audit'),
                why=p.get('why'), seconds=round(time.time() - t0, 2), rss_exit=p.get('rss_exit', False))
if __name__ == '__main__':
    rows = [json.loads(l) for f in infiles for l in open(f) if l.strip()]
    def pri(r): return (0 if len(r['alt']) < r['k'] else 1 if r['k'] >= 3 else 2 if len(r['alt']) == 2 else 3, 0 if r['big'] else 1, r['i'])
    rows.sort(key=pri); t0 = time.time(); n = 0; neg = 0
    with mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=150) as pool, open(out, 'w') as f:
        for res in pool.imap_unordered(job, rows, chunksize=2):
            f.write(json.dumps(res) + '\n'); f.flush(); n += 1
            if isinstance(res.get('delta'), (int, float)) and res['delta'] < 0:
                neg += 1; print('NEGATIVE', json.dumps(res), flush=True)
            if n % 250 == 0: print(f'{n}/{len(rows)} {time.time() - t0:.0f}s neg={neg}', flush=True)
            if time.time() - t0 > budget: print('budget reached', flush=True); pool.terminate(); break
    print(f'priced {n} of {len(rows)} in {time.time() - t0:.0f}s, negative {neg}', flush=True)
