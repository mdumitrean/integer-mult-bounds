"""aprice.py: price A-window peephole alternatives with the compensation-aware pricer (absorb.AbsorbPricer.price_ab:
section-tagged A edits, whole A+cut+B+tail map checked up to absorbed port columns, compensation re-derived, static
rules, cone caps recomputed, exact optimal frames with cut equality) at b = 0.001679754956125544 on the base word.
args: out.jsonl budget_seconds infile... ; order: strict reductions, then same-length rewrites, then permutations,
then longer rewrites; within a group, large-deletion windows first, nonzero-frame windows first.
4 workers, 90 s per pricing, maxtasksperchild=100, run stops if a worker's peak RSS passes 5.5 GiB."""
import os, sys, json, time, multiprocessing as mp
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import absorb
from compat import peak_rss_gib
WORD = os.path.join(absorb.SCR, 'r3/inputs', os.environ.get('WORDFILE', 'gauge44-word-566-554.json.gz'))
B_ = '0.001679754956125544'
P = None; _cache = {}; _orig = absorb.main_rows
def main_rows_cached(w, npre=0):
    if P is not None and w is P.base:
        if npre not in _cache: _cache[npre] = _orig(w, npre)
        return _cache[npre]
    return _orig(w, npre)
absorb.main_rows = main_rows_cached
def init():
    global P
    P = absorb.AbsorbPricer(WORD, b=B_, check_literal=True, interval=False)
def gate(t):
    if t[0] == 'add': c = Q(t[3]); return ['add', t[1], t[2], c.numerator, c.denominator, []]
    c = Q(t[2]); return ['scale', t[1], c.numerator, c.denominator, []]
def edit(r):
    i, k = r['i'], r['k']
    return dict(delete=[['A', j] for j in range(i, i + k)], insert=[['A', i, gate(t)] for t in r['alt']])
def job(r):
    t0 = time.time(); p = P.price_ab(edit(r), timeout=90)
    return dict(r, status=p.get('status'), delta=p.get('delta'), profile=p.get('profile'), comp_gates=p.get('comp_gates'),
                comp_changed=p.get('comp_changed'), why=p.get('why'), seconds=round(time.time() - t0, 2), rss=peak_rss_gib())
def pri(r):
    L, k = len(r['alt']), r['k']
    grp = 0 if L < k else (1 if (L == k and not r['perm']) else (2 if r['perm'] else 3))
    return (grp, 0 if r['big'] else 1, 0 if r['nz'] else 1, r['i'])
if __name__ == '__main__':
    out, budget, infiles = sys.argv[1], float(sys.argv[2]), sys.argv[3:]
    rows = [json.loads(l) for f in infiles for l in open(f) if l.strip()]
    if not os.environ.get('KEEP_ORDER'): rows.sort(key=pri)
    t0 = time.time(); n = neg = 0
    print('to price', len(rows), flush=True)
    with mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=100) as pool, open(out, 'w') as f:
        for res in pool.imap_unordered(job, rows, chunksize=2):
            f.write(json.dumps(res) + '\n'); f.flush(); n += 1
            if isinstance(res.get('delta'), (int, float)) and res['delta'] < 0:
                neg += 1; print('NEGATIVE', json.dumps(res), flush=True)
            if res.get('rss') and res['rss'] > 5.5: print('RSS cap exceeded', res['rss'], flush=True); pool.terminate(); break
            if n % 200 == 0: print(f'{n}/{len(rows)} {time.time() - t0:.0f}s neg={neg}', flush=True)
            if time.time() - t0 > budget: print('budget reached', flush=True); pool.terminate(); break
    print(f'priced {n} of {len(rows)} in {time.time() - t0:.0f}s, negative {neg}', flush=True)
