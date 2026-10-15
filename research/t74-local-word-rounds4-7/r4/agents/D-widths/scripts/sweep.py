"""sweep: price every one-level width change of selected helpers on the base word (exact optimal frames, program unchanged).
kinds: up-start (start frame -> a hyperplane of it), up-end (end frame -> a superspace), down-start (start frame -> a
superspace).  3 workers (fork), per-task deadline, RSS flag at 6 GiB (worker exits), maxtasksperchild.
usage: sweep.py TOOLKIT INPUTS OUT.jsonl [--word gauge44|extra]"""
import os, sys, json, time, copy, collections, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
INP, OUT = sys.argv[2], sys.argv[3]; WORD = sys.argv[5] if len(sys.argv) > 5 else 'gauge44'
BASE = None; COSTS = None; BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(f'{INP}/{WORD}-word-566-554.json.gz'); COSTS = F.Costs(K.B)
    BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    q, kind, basis = task; t0 = time.time(); w = copy.deepcopy(BASE)
    if kind in ('up-start', 'down-start'):
        if basis: w['start_extra'][str(q)] = basis
        else: w['start_extra'].pop(str(q), None)
    else: w['helper_final'][str(q)] = basis
    try:
        with deadline(60):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    rss = peak_rss_gib(); out.update(q=q, kind=kind, basis=basis, seconds=round(time.time() - t0, 2))
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
def tasks():
    w = K.load(f'{INP}/{WORD}-word-566-554.json.gz'); paid, centre, widths, starts, ends, endB = W.recount(w)
    v, R = w['report']['v'], w['report']['R']; T = []
    for q in range(2 * v, 2 * v + R):
        wd = widths[q - 2 * v]; sd = W.dimension(starts[q]); ed = W.dimension(ends[q])
        sv = list(w['start_extra'].get(str(q), [])); ev = list(w['helper_final'].get(str(q), []))
        if wd == 4:   # upgrade to 5
            if sd > 0: T += [(q, 'up-start', h) for h in K.hyperplanes(sv)]
            if ed < 9: T += [(q, 'up-end', e) for e in K.extensions(ev)]
        if wd == 5 and sd < 9:   # narrow to 4 via the start frame
            T += [(q, 'down-start', e) for e in K.extensions(sv)]
    return T
if __name__ == '__main__':
    T = tasks(); print('tasks', len(T), collections.Counter(k for _, k, _ in T), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=50) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=4), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if n % 200 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
