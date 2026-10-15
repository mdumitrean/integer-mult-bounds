"""repair.py's sweep (unchanged repair.repair and candidate generator) with every pricing's status recorded.
usage: repair_rec.py TOOLKIT WORD OUT.json [--workers 3] [--timeout 90] [--max-tasks-per-child 50]"""
import argparse, json, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--timeout', type=int, default=90); ap.add_argument('--max-tasks-per-child', type=int, default=50)
a = ap.parse_args(); sys.path.insert(0, a.toolkit)
import repair as R, fusion as G, harness as H
from compat import pool_context
LOG = []
def init(path, timeout):
    R.init(path, timeout, True); inner = R.P.price
    def rec(ed, **kw):
        r = inner(ed, **kw); LOG.append(dict(status=r.get('status'), delta=r.get('delta'), max_gain_units=r.get('max_gain_units'), gain_certified=r.get('gain_certified'), audit=r.get('audit')))
        return r
    R.P.price = rec
def job(c):
    del LOG[:]; r = R.repair(c); r['pricings'] = list(LOG); return r
if __name__ == '__main__':
    cs = G.candidates(H.load(a.word)); print('fusions to repair:', len(cs), flush=True); t0 = time.time(); res = []
    with pool_context().Pool(a.workers, initializer=init, initargs=(a.word, a.timeout), maxtasksperchild=a.max_tasks_per_child) as pool:
        for n, r in enumerate(pool.imap_unordered(job, cs, chunksize=1), 1):
            res.append(r)
            g = [p for p in r['pricings'] if p['delta'] is not None and p['delta'] < 0]
            if g: print('  NEGATIVE', r['t'], r['A'], r['H'], r['p'], r['rest'], g, flush=True)
            if n % 100 == 0: print(f'  {n}/{len(cs)} {time.time()-t0:.0f}s feasible {sum(1 for x in res if x["best"])} evals {sum(x["tried"] for x in res)}', flush=True)
    st = {}
    for x in res:
        for p in x['pricings']: st[p['status']] = st.get(p['status'], 0) + 1
    bounds = [p['max_gain_units'] for x in res for p in x['pricings'] if p['status'] in ('ok', 'uncertified') and p['delta'] is not None and p['delta'] >= 0 and p['max_gain_units'] is not None]
    print(f'done {len(res)} fusions in {time.time()-t0:.0f}s | evals {sum(x["tried"] for x in res)} | statuses {st} | negative {sum(1 for x in res for p in x["pricings"] if p["delta"] is not None and p["delta"] < 0)} | largest possible true gain among non-gains {max(bounds, default=0.0):.3g} units', flush=True)
    json.dump(res, open(a.out, 'w', encoding='utf-8', newline='\n'))
