"""Deletion relaxation (screen, not a bound): price exact optimal frames after deleting ONE B add gate, no compensation,
base cone caps (as #1957 tools/relax.py), on one word.  usage: relax.py TOOLKIT WORD OUT.json [--workers 3]"""
import argparse, json, os, sys, time, multiprocessing as mp
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--b', default='0.001679754956125544'); a = ap.parse_args()
sys.path.insert(0, a.toolkit)
import harness as H, frames as F
from word import inline
from compat import Timeout, deadline, peak_rss_gib
P = None
def init():
    global P; P = H.Pricer(a.word, b=a.b, check_literal=True)
def run(i):
    t0 = time.time(); w1 = H.compile_edits(P.base, dict(delete=[i]))
    try:
        with deadline(120):
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=g)
        res = dict(delta=r['cost'] - P.base_cost, prof=dict(sorted(r['profile'].items())), cert=r['certified'])
    except F.Infeasible: res = dict(status='infeasible')
    except Timeout: res = dict(status='timeout')
    except Exception as e: res = dict(status='err:' + repr(e)[:80])
    res['sec'] = round(time.time() - t0, 2); rss = peak_rss_gib()
    if rss is not None and rss > 6: res['rss_exit'] = True
    return i, res
if __name__ == '__main__':
    init(); B = P.base['B']; idx = [i for i, g in enumerate(B) if g[0] == 'add']
    print('base', P.base_cost, P.base_profile, 'add gates', len(idx), flush=True); out = {}; t0 = time.time()
    with mp.get_context('fork').Pool(a.workers, initializer=init, maxtasksperchild=40) as pool:
        for n, (i, r) in enumerate(pool.imap_unordered(run, idx, chunksize=4), 1):
            out[i] = r
            if n % 200 == 0: print(f'  {n}/{len(idx)} {time.time()-t0:.0f}s', flush=True); json.dump(out, open(a.out + '.part', 'w'))
    json.dump(dict(base_cost=P.base_cost, base_profile=P.base_profile, b=a.b, results={str(k): out[k] for k in sorted(out)}), open(a.out, 'w'), sort_keys=True)
    print('done', len(out), f'{time.time()-t0:.0f}s', flush=True)
