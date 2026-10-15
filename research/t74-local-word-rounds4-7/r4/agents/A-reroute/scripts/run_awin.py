"""run_awin: for each pivot, solve A-window re-deliveries, check whole-program exactness, price.  usage: run_awin.py WORD K q..."""
import sys, os, json, time, resource
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname, K, BUD = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]); qs = list(map(int, sys.argv[4:]))
outdir = os.path.join(HERE, '..', 'out')
for q in qs:
    t0 = time.time(); aw = AWin(wname, q)
    res = aw.run(K=K, budget=BUD)
    recs = []
    for c in res.get('cands', []):
        w1 = aw.materialize(c['ed'])
        same, comp_same, ncomp = aw.check(w1)
        pr = price(w1, aw.P.costs, aw.P.base_cost) if same else dict(status='inexact')
        recs.append(dict(c, exact=same, comp_unchanged=comp_same, ncomp=ncomp, price=pr))
        print(q, 'atoms', c['atoms'], 'slots', c['slots'], 'exact', same, 'comp_same', comp_same, '->', pr.get('status'), pr.get('delta'), pr.get('profile'), flush=True)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3
    print(f'q={q}: status {res["status"]} natoms {res.get("natoms")} (in A {res.get("natomsA")}) nsols {res.get("nsols")} cands {len(recs)} '
          f'neg {sum(1 for r in recs if (r["price"].get("delta") or 0) < 0)} budget_hit {res.get("budget_hit")} nodes {res.get("dfs_nodes")} {time.time()-t0:.0f}s rss {rss:.2f}GiB', flush=True)
    json.dump(dict(q=q, word=wname, K=K, d=res.get('d'), dp=res.get('dp'), natoms=res.get('natoms'), natomsA=res.get('natomsA'), nsols=res.get('nsols'), status=res['status'], budget_hit=res.get('budget_hit'), dfs_nodes=res.get('dfs_nodes'), coverage=res.get('coverage'), cands=recs),
              open(os.path.join(outdir, f'AWIN-{wname}-{q}-K{K}.json'), 'w'), default=str)
