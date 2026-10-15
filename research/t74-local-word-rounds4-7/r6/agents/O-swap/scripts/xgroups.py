"""xgroups: single GROUP width changes on the extra word, in the JOINT-base.jsonl format, so gswap.py can pair them.
Narrowings: every (4,9) group (incl. 627..631, upgraded in the extra word) at every extension of its common start frame;
widenings: the (5,9) groups (619..623, 651..655) at every hyperplane, the (0,4) groups at every extension.
usage: xgroups.py TOOLKIT EXTRA.json.gz OUT.jsonl [--no-end]   (4 workers, deadline, RSS check)"""
import os, sys, json, time, copy, collections, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, OUT = sys.argv[2], sys.argv[3]; NOEND = '--no-end' in sys.argv
BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(WORD); COSTS = F.Costs(K.B); BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    label, side, members, basis = task; t0 = time.time(); w = copy.deepcopy(BASE)
    for q in members: (w['start_extra'] if side == 'start' else w['helper_final'])[str(q)] = basis
    try:
        with deadline(90):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    out.update(label=label, side=side, members=members, basis=basis, seconds=round(time.time() - t0, 2))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
def tasks():
    w = K.load(WORD); paid, centre, widths, starts, ends, endB = W.recount(w); v, R = w['report']['v'], w['report']['R']
    typ = lambda q: (W.dimension(starts[q]), W.dimension(ends[q])); groups = collections.defaultdict(list); T = []
    for q in range(2 * v, 2 * v + R):
        t = typ(q)
        if t == (5, 9): groups[('start', tuple(sorted(w['start_extra'][str(q)])))].append(q)
        if t == (0, 4) and not NOEND: groups[('end', tuple(sorted(w['helper_final'][str(q)])))].append(q)
        if t == (4, 9): groups[('down', tuple(sorted(w['start_extra'][str(q)])))].append(q)
    for (side, frame), mem in sorted(groups.items(), key=lambda x: x[1][0]):
        choices = K.hyperplanes(list(frame)) if side == 'start' else K.extensions(list(frame))
        for basis in choices: T.append((f'{side}:{mem[0]}..{mem[-1]}', 'start' if side in ('start', 'down') else 'end', mem, basis))
    return T
if __name__ == '__main__':
    T = tasks(); print('tasks', len(T), collections.Counter(t[0].split(':')[0] for t in T), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=60) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=2), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if n % 100 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
