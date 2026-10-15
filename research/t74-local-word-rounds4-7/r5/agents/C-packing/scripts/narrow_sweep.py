"""Price start-side narrowings (NARROW-TASKS.json) on a word with exact optimal frames (cone caps recomputed).
3 workers (fork), per-task deadline 60 s, RSS flag 6 GiB with worker recycling (maxtasksperchild).
usage: narrow_sweep.py TOOLKIT WORD TASKS OUT.jsonl"""
import copy, json, os, sys, time, multiprocessing as mp
TK = sys.argv[1]; sys.path.insert(0, TK); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, TASKS, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(WORD); COSTS = F.Costs(K.B); BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    q, wd, basis, sec, i = task; t0 = time.time(); w = copy.deepcopy(BASE); w['start_extra'][str(q)] = basis
    try:
        with deadline(60):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    rss = peak_rss_gib(); out.update(q=q, width=wd, basis=basis, first=[sec, i], seconds=round(time.time() - t0, 2))
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    T = [tuple(t) for t in json.load(open(TASKS))]; t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=60) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=4), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if n % 100 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
