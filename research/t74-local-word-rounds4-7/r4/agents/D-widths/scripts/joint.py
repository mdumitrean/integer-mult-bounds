"""joint: price joint one-level upgrades of helper groups (exact optimal frames, program unchanged).
Tasks: for each group of helpers sharing one start frame (type (5,9)) or one end frame (type (0,4)), every common
hyperplane (start side) or common extension (end side), applied to all members, plus every subset of the
extra word's group with its own choice.  3 workers, deadline, RSS flag, maxtasksperchild.
usage: joint.py TOOLKIT INPUTS OUT.jsonl"""
import os, sys, json, time, copy, itertools, collections, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, word as W
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
INP, OUT = sys.argv[2], sys.argv[3]
BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(f'{INP}/gauge44-word-566-554.json.gz'); COSTS = F.Costs(K.B); BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    label, side, members, basis = task; t0 = time.time(); w = copy.deepcopy(BASE)
    for q in members:
        (w['start_extra'] if side == 'start' else w['helper_final'])[str(q)] = basis
    try:
        with deadline(90):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    rss = peak_rss_gib(); out.update(label=label, side=side, members=members, basis=basis, seconds=round(time.time() - t0, 2))
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
def tasks():
    w = K.load(f'{INP}/gauge44-word-566-554.json.gz'); paid, centre, widths, starts, ends, endB = W.recount(w)
    v, R = w['report']['v'], w['report']['R']; T = []
    typ = lambda q: (W.dimension(starts[q]), W.dimension(ends[q]))
    groups = collections.defaultdict(list)
    for q in range(2 * v, 2 * v + R):
        if typ(q) == (5, 9): groups[('start', tuple(sorted(w['start_extra'][str(q)])))].append(q)
        if typ(q) == (0, 4): groups[('end', tuple(sorted(w['helper_final'][str(q)])))].append(q)
        if typ(q) == (4, 9): groups[('down', tuple(sorted(w['start_extra'][str(q)])))].append(q)
    for (side, frame), mem in sorted(groups.items()):
        choices = K.hyperplanes(list(frame)) if side == 'start' else K.extensions(list(frame))
        for basis in choices: T.append((f'{side}:{mem[0]}..{mem[-1]}', 'start' if side in ('start', 'down') else 'end', mem, basis))
    g2 = [627, 629, 630, 631]; h390 = [1, 24, 34, 68]
    for k in (2, 3):
        for sub in itertools.combinations(g2, k): T.append((f'g2-subset{k}', 'start', list(sub), h390))
    return T, {f'{s}:{m[0]}..{m[-1]}': m for (s, f), m in groups.items()}
if __name__ == '__main__':
    T, G = tasks(); print('groups', {k: len(m) for k, m in G.items()}, 'tasks', len(T), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=40) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=2), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if n % 50 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
