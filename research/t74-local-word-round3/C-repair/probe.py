"""Price the first N fusion candidates (with repairs) in-process; report time and peak RSS."""
import sys, time, json, resource
sys.path.insert(0, sys.argv[1])
import repair as RP, fusion as G, harness as H
word, n = sys.argv[2], int(sys.argv[3])
t0 = time.time(); RP.init(word, timeout=90, interval=True); t1 = time.time()
cs = G.candidates(H.load(word)); step = max(1, len(cs) // n); res = []
for c in cs[::step][:n]:
    res.append(RP.repair(c))
t2 = time.time()
print(json.dumps(dict(init_s=round(t1 - t0, 1), n=len(res), price_s=round(t2 - t1, 1), evals=sum(r['tried'] for r in res),
                      feasible=sum(1 for r in res if r['best']), gains=[(r['t'], r['A'], r['H'], r['best']['delta']) for r in res if r['best'] and r['best']['delta'] < 0],
                      peak_rss_gib=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3, 2))))
