"""Solve #2142's split-key model for deletion jobs on one word (strict settings as #2142: <=12 inserts, |lambda|<=4 in half
steps, budget |gain|-1), CP-SAT, exact re-price by abkernel.price.  usage: solve.py WORD JOBS.json OUTDIR [--tl 300] [--K 5]"""
import argparse, json, os, sys, time
ap = argparse.ArgumentParser(); ap.add_argument('word'); ap.add_argument('jobs'); ap.add_argument('outdir')
ap.add_argument('--tl', type=float, default=300); ap.add_argument('--K', type=int, default=5); ap.add_argument('--workers', type=int, default=3)
ap.add_argument('--maxterms', type=int, default=12); a = ap.parse_args()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2
P = sk2.H.Pricer(a.word); base_full = sk2.amap(sk2.fullseq(P.base)); os.makedirs(a.outdir, exist_ok=True)
for job in json.load(open(a.jobs)):
    dels = [tuple(x) for x in job]; t0 = time.time(); name = '-'.join('%s%d' % x for x in dels)
    m = sk2.build(P, dels); r = sk2.solve(P, m, a.maxterms, a.K, a.tl, workers=a.workers, base_full=base_full)
    r.update(job=job, sec=round(time.time() - t0, 1), keys=len(m['fam']))
    json.dump(r, open(os.path.join(a.outdir, 'sk-%s.json' % name), 'w'), separators=(',', ':'))
    best = min([x['delta'] for x in r['res'] if x.get('delta') is not None], default=None)
    print('SUMMARY', name, 'ddel', r['ddel'], 'keys', r['keys'], 'cand', r['ncand'], 'shape', r['shape'], 'cp', r['cp_status'], 'nsol', len(r['res']), 'best', best, f"{r['sec']}s", flush=True)
