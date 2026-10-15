"""Positive control / diagnostic for the multi-deletion model: per-insert oracle cap SK_CANDCAP (env) and NO summed budget.
The exact relocations of the deleted reads lie in the family, so a correctly wired model must find exact solutions
(cost-neutral or worse).  usage: skm_diag.py WORD JOBS.json OUTDIR [--tl 300] [--K 4]"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2, sk_multi
ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('jobs'); ap.add_argument('outdir')
ap.add_argument('--tl', type=float, default=300); ap.add_argument('--K', type=int, default=4); a = ap.parse_args()
P = sk2.H.Pricer(a.word); base_full = sk2.amap(sk2.fullseq(P.base)); os.makedirs(a.outdir, exist_ok=True)
for job in json.load(open(a.jobs)):
    dels = [tuple(x) for x in job['dels']]; t0 = time.time()
    m = sk_multi.build_multi(P, dels, store_factor=sk2.CANDCAP)
    r = sk2.solve(P, m, 12, a.K, a.tl, workers=1, base_full=base_full, nobud=True)
    r.update(name=job['name'], candcap=sk2.CANDCAP, nobud=True, sec=round(time.time() - t0, 1))
    json.dump(r, open(os.path.join(a.outdir, 'diag-%s.json' % job['name']), 'w'), separators=(',', ':'))
    print('DIAG', job['name'], 'cand', r['ncand'], 'cp', r['cp_status'], [(x['status'], x['delta'], x['terms']) for x in r['res']], f"{r['sec']}s", flush=True)
