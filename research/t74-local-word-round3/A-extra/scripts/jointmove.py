"""Joint relocation of a reader's early pivot reads (exact by construction: the pivots are unwritten until their first
writes and no gate in between reads or scales the reader).  Priced with our #1186 rev3 harness (static rules, exact map
screen, unchanged derived compensation, exact optimal frames, interval certificate, audit_local on any negative delta).
usage: jointmove.py TOOLKIT WORD OUT.json [--workers 3]"""
import argparse, json, sys, time, multiprocessing as mp
ap = argparse.ArgumentParser(); ap.add_argument('toolkit'); ap.add_argument('word'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); ap.add_argument('--b', default='0.001679754956125544'); a = ap.parse_args()
sys.path.insert(0, a.toolkit)
import harness as H
P = None
def init():
    global P; P = H.Pricer(a.word, b=a.b, check_literal=True, interval=True)
def jobs(B):
    first = {}
    for i, g in enumerate(B): first.setdefault(g[1], i)
    readers = {t: [i for i in range(397, 409) if B[i][1] == t] for t in (624, 625, 626, 628)}
    out = []
    for t, reads in readers.items():
        fw = min(first[B[i][2]] for i in reads)
        blk = [i for i in range(max(reads) + 1, fw + 1) if (B[i][0] == 'add' and B[i][2] == t) or (B[i][0] == 'scale' and B[i][1] == t)]
        assert not blk, (t, blk)
        ps = sorted({max(reads) + 1, max(reads) + 2, 420, 500, 700, 900, 1000, fw - 5, fw - 4, fw - 3, fw - 2, fw - 1, fw})
        for p in ps: out.append(dict(kind='joint', reader=t, moves=[[j, p] for j in reads]))
        # one read at a time to the late position (the others stay)
        for j in reads:
            for p in (fw - 4, fw - 3, fw): out.append(dict(kind='single', reader=t, moves=[[j, p]]))
    # all four readers together to their late positions
    for p_off in (0, 1, 3, 4):
        mv = []
        for t, reads in readers.items():
            fw = min(first[B[i][2]] for i in reads); mv += [[j, fw - p_off] for j in reads]
        out.append(dict(kind='all4', reader=None, moves=mv))
    return out
def run(job):
    B = P.base['B']; ed = dict(delete=[j for j, p in job['moves']], insert=[[p, list(B[j][:-1]) + [[]]] for j, p in job['moves']])
    r = P.price(ed, timeout=300)
    keep = {k: r[k] for k in ('status', 'delta', 'profile', 'realized_delta_units', 'gain_certified', 'max_gain_units', 'audit', 'why') if k in r}
    return dict(job, ed=ed, **keep)
if __name__ == '__main__':
    init(); J = jobs(P.base['B']); print('base', P.base_cost, P.base_profile, 'jobs', len(J), flush=True); res = []; t0 = time.time()
    with mp.get_context('fork').Pool(a.workers, initializer=init, maxtasksperchild=20) as pool:
        for n, r in enumerate(pool.imap_unordered(run, J), 1):
            res.append(r); print(n, len(J), f'{time.time()-t0:.0f}s', r['kind'], r['reader'], r['moves'][:3], r.get('status'), r.get('delta'), r.get('profile'), r.get('gain_certified'), r.get('audit'), flush=True)
    json.dump(dict(base_cost=P.base_cost, base_profile=P.base_profile, b=a.b, results=res), open(a.out, 'w'), indent=0)
