"""Price the position-class fusion completion (fusion_pos.gen) bare, with intervals; record every status.
usage: posweep.py TOOLKIT WORD OUT.json [--workers 3] [--timeout 90]"""
import argparse, json, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--timeout', type=int, default=90); ap.add_argument('--max-tasks-per-child', type=int, default=60)
a = ap.parse_args(); sys.path.insert(0, a.toolkit); sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
import harness as H, fusion as G, fusion_pos as FP
from compat import pool_context
P = None
def init(path):
    global P; P = H.Pricer(path, interval=True)
def job(c):
    r = P.price(c['ed'], timeout=a.timeout)
    return dict(c, price={k: r[k] for k in ('status', 'delta', 'profile', 'max_gain_units', 'gain_certified', 'audit', 'why') if k in r})
if __name__ == '__main__':
    cs = FP.gen(H.load(a.word), G); print('position-class candidates', len(cs), flush=True); t0 = time.time(); res = []
    with pool_context().Pool(a.workers, initializer=init, initargs=(a.word,), maxtasksperchild=a.max_tasks_per_child) as pool:
        for n, r in enumerate(pool.imap_unordered(job, cs, chunksize=4), 1):
            res.append(r); p = r['price']
            if p.get('delta') is not None and p['delta'] < 0: print('  NEGATIVE', r['t'], r['A'], r['H'], r['p'], r['rest'], p, flush=True)
            if n % 200 == 0: print(f'  {n}/{len(cs)} {time.time()-t0:.0f}s', flush=True)
    st = {}
    for r in res: st[r['price'].get('status')] = st.get(r['price'].get('status'), 0) + 1
    bounds = [r['price']['max_gain_units'] for r in res if r['price'].get('status') in ('ok', 'uncertified') and r['price'].get('delta', 1) >= 0 and 'max_gain_units' in r['price']]
    print(f'done {len(res)} in {time.time()-t0:.0f}s | statuses {st} | negative {sum(1 for r in res if r["price"].get("delta") is not None and r["price"]["delta"] < 0)} | largest possible true gain among non-gains {max(bounds, default=0.0):.3g} units', flush=True)
    json.dump(res, open(a.out, 'w', encoding='utf-8', newline='\n'))
