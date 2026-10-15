"""Build #2142's split-key CP-SAT model for each deletion job on the base and the extra word (same b, #1957's vendored
#1186 toolkit, as #2142) and compare.  identical = same budget and the same filtered candidate list (keys, positions,
columns, oracle costs), hence the same CP-SAT model.  usage: compare.py BASE EXTRA JOBS.json OUT.json [--workers 3]"""
import argparse, json, os, sys, time, multiprocessing as mp
ap = argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('extra'); ap.add_argument('jobs'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); a = ap.parse_args()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2
from compat_shim import deadline, Timeout, peak_rss_gib
PB = PE = None
def init():
    global PB, PE; PB = sk2.H.Pricer(a.base); PE = sk2.H.Pricer(a.extra)
def key(c): return (c[0], c[1], c[2], c[7], c[6], tuple(sorted(c[4].items())), tuple(sorted(c[5].items())))
def run(job):
    dels = [tuple(x) for x in job]; t0 = time.time(); out = dict(job=job)
    try:
        with deadline(900):
            mb = sk2.build(PB, dels); me = sk2.build(PE, dels)
    except Timeout: out['status'] = 'timeout'; return out
    except Exception as e: out['status'] = 'err:' + repr(e)[:120]; return out
    cb = sk2.candidates(mb, sk2.CANDCAP * mb['bud']); ce = sk2.candidates(me, sk2.CANDCAP * me['bud'])
    kb = [key(c) for c in cb]; ke = [key(c) for c in ce]
    sb = {(x, y, i, ki, vf, vb): cst for (x, y, i, ki, cst, vf, vb) in kb}; se = {(x, y, i, ki, vf, vb): cst for (x, y, i, ki, cst, vf, vb) in ke}
    cheaper = sum(1 for k, c in se.items() if k not in sb or c < sb[k])
    out.update(status='ok', ddel_base=mb['ddel'], ddel_extra=me['ddel'], ncand_base=len(cb), ncand_extra=len(ce), nkeys=len(mb['fam']),
               d=len(mb['d']), dB=len(mb['dBt']), identical=(mb['bud'] == me['bud'] and kb == ke and mb['d'] == me['d'] and mb['dBt'] == me['dBt']),
               extra_cheaper_or_new=cheaper, sec=round(time.time() - t0, 1))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    jobs = json.load(open(a.jobs)); res = []; t0 = time.time()
    with mp.get_context('fork').Pool(a.workers, initializer=init, maxtasksperchild=8) as pool:
        for n, r in enumerate(pool.imap_unordered(run, jobs), 1):
            res.append(r); print(n, len(jobs), f'{time.time()-t0:.0f}s', json.dumps(r), flush=True)
            json.dump(res, open(a.out, 'w'), indent=0)
    print('done', f'{time.time()-t0:.0f}s')
