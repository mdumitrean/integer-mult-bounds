"""reprice_tail.py: re-price earlier frame-infeasible harness candidates with the solver's tail caps dropped (end-of-B caps
only, as audit_local.py and the native audit check).  Every other harness rule is unchanged (static rules, map screen,
unchanged derived compensation, cut equality, tail-mutable frames, interval bounds, write-back + audit on negative deltas).
usage: reprice_tail.py TOOLKIT WORD OUT.jsonl SELECT(tail|all) CANDIDATE_JSON... [--workers 3] [--timeout 90]"""
import argparse, json, os, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out'); ap.add_argument('select')
ap.add_argument('cands', nargs='+'); ap.add_argument('--workers', type=int, default=3); ap.add_argument('--timeout', type=int, default=90)
a = ap.parse_args(); sys.path.insert(0, a.toolkit)
import frames as F, harness as H
from compat import pool_context
class TailFree(F.Graph):
    def __init__(self, *args, **kw): kw.setdefault('tail_caps', False); super().__init__(*args, **kw)
P = None
def init(path):
    global P; F.Graph = TailFree; P = H.Pricer(path, interval=True)
def job(c):
    r = P.price(c['ed'], timeout=a.timeout)
    return dict(src=c['_src'], idx=c['_idx'], ed=c['ed'], old=c['price'], new={k: r[k] for k in ('status', 'delta', 'profile', 'max_gain_units', 'gain_certified', 'audit', 'why', 'rss_exit') if k in r})
def records(path):
    d = json.load(open(path)) if not path.endswith('.jsonl') else [json.loads(l) for l in open(path) if l.strip()]
    for i, r in enumerate(d):
        if isinstance(r, dict) and 'ed' in r and isinstance(r.get('price'), dict) and r['price'].get('status') == 'infeasible':
            if a.select == 'all' or "'tail'" in str(r['price'].get('why', '')): yield dict(r, _src=os.path.basename(path), _idx=i)
if __name__ == '__main__':
    cs = [c for p in a.cands for c in records(p)]; print('candidates', len(cs), flush=True); t0 = time.time(); n = 0; st = {}
    with pool_context().Pool(a.workers, initializer=init, initargs=(a.word,), maxtasksperchild=50) as pool, open(a.out, 'w') as f:
        for r in pool.imap_unordered(job, cs, chunksize=4):
            n += 1; f.write(json.dumps(r) + '\n'); s = r['new'].get('status'); st[s] = st.get(s, 0) + 1
            if r['new'].get('delta') is not None and r['new']['delta'] < 0: print('  NEGATIVE', r['src'], r['idx'], r['new'], flush=True)
            if n % 200 == 0: print(f'  {n}/{len(cs)} {time.time()-t0:.0f}s {st}', flush=True)
    print(f'done {n} in {time.time()-t0:.0f}s statuses {st}', flush=True)
