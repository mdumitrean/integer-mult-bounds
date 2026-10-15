"""Exchange + joint triangle-hybrid sweep with the #1186 toolkit harness (surrogate optimum + true-moment intervals).

Families (all edits refer to the base word, priced by harness.Pricer(interval=True); audit_local runs on every negative delta):
  xs   every single read-set swap (exchange.movable_reads + joint.swap_edit, the sw4 rule) of every copy pair;
  xp   every pair of single swaps (same or different copy pairs);
  xf   the full exchange of each copy pair (all its movable reads swapped);
  xff  every union of two full exchanges;
  jt   joint triangle-hybrid candidates (joint.candidates) with max_fused <= MAXF, allow_partial, restores canon+after.
usage: xjsweep.py TOOLKIT WORD OUT.json [--workers 3] [--timeout 90] [--maxf 3]"""
import argparse, itertools, json, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--timeout', type=int, default=90); ap.add_argument('--maxf', type=int, default=3)
ap.add_argument('--max-tasks-per-child', type=int, default=40); a = ap.parse_args()
sys.path.insert(0, a.toolkit)
import harness as H, joint as J
from exchange import copy_pairs, movable_reads
from compat import pool_context
P = None
def init(path):
    global P; P = H.Pricer(path, interval=True)
def job(c):
    r = P.price(c['ed'], timeout=a.timeout)
    keep = {k: r[k] for k in ('status', 'delta', 'profile', 'max_gain_units', 'gain_certified', 'realized_delta_units', 'audit', 'why', 'rss_exit') if k in r}
    return dict(c, price=keep)
def build(w):
    pairs = copy_pairs(w); jobs = []; singles = []
    for h, (r, ic) in sorted(pairs.items()):
        M = movable_reads(w, h, r, ic)
        for m in M:
            s = J.swap_edit(w, h, r, ic, m)
            if s: singles.append(((h, m[0]), s)); jobs.append(dict(fam='xs', key=[h, m[0]], ed=s))
        ss = [J.swap_edit(w, h, r, ic, m) for m in M]
        if M and all(ss): jobs.append(dict(fam='xf', key=[h], ed=J.merge(ss)))
    for (k1, s1), (k2, s2) in itertools.combinations(singles, 2):
        m2 = J.merge([s1, s2])
        if m2: jobs.append(dict(fam='xp', key=[list(k1), list(k2)], ed=m2))
    fulls = [j for j in jobs if j['fam'] == 'xf']
    for f1, f2 in itertools.combinations(fulls, 2):
        m2 = J.merge([f1['ed'], f2['ed']])
        if m2: jobs.append(dict(fam='xff', key=[f1['key'][0], f2['key'][0]], ed=m2))
    seen = set()
    for maxf in range(1, a.maxf + 1):
        for c in J.candidates(w, max_fused=maxf, allow_partial=True, restores=("canon", "after")):
            k = json.dumps(c['ed'], sort_keys=True)
            if k in seen: continue
            seen.add(k); jobs.append(dict(fam='jt', key=dict(h=c['h'], fused=c['fused'], swapped=c['swapped']), ed=c['ed']))
    return jobs
if __name__ == '__main__':
    w = H.load(a.word); jobs = build(w); t0 = time.time()
    fams = {}
    for j in jobs: fams[j['fam']] = fams.get(j['fam'], 0) + 1
    print('jobs', len(jobs), fams, flush=True); res = []
    with pool_context().Pool(a.workers, initializer=init, initargs=(a.word,), maxtasksperchild=a.max_tasks_per_child) as pool:
        for n, r in enumerate(pool.imap_unordered(job, jobs, chunksize=1), 1):
            res.append(r); p = r['price']
            if p.get('delta') is not None and p['delta'] < 0: print('  GAIN', r['fam'], r['key'], p, flush=True)
            if n % 50 == 0: print(f'  {n}/{len(jobs)} {time.time()-t0:.0f}s', flush=True)
    st = {}
    for r in res:
        k = (r['fam'], r['price'].get('status')); st[k] = st.get(k, 0) + 1
    bounds = [r['price']['max_gain_units'] for r in res if r['price'].get('status') in ('ok', 'uncertified') and r['price'].get('delta', 1) >= 0 and 'max_gain_units' in r['price']]
    print('done', len(res), f'{time.time()-t0:.0f}s', sorted(st.items()), 'largest possible true gain among non-gains', max(bounds, default=0.0), flush=True)
    json.dump(res, open(a.out, 'w', encoding='utf-8', newline='\n'))
