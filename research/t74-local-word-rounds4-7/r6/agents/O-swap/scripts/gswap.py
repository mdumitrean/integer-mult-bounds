"""gswap: price same-inventory GROUP swaps jointly (one width-5 group narrowed 5->4 + one width-4 group widened 4->5) on a word.
Program unchanged; only start_extra / helper_final of the helpers change, so the width inventory is unchanged.
Options come from r4 D-widths' JOINT-base.jsonl (feasible narrowing basis per (4,9) group; every widening option per (5,9)
or (0,4) group).  Exact optimal frames (cone caps recomputed), 4 workers (fork), per-task deadline, RSS check, maxtasksperchild.
usage: gswap.py TOOLKIT WORD.json.gz JOINT.jsonl OUT.jsonl [--narrow-only-full]"""
import os, sys, json, time, copy, collections, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, JOINT, OUT = sys.argv[2], sys.argv[3], sys.argv[4]
BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(WORD); COSTS = F.Costs(K.B); BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    nx, ny = task; t0 = time.time(); w = copy.deepcopy(BASE)
    for q in nx['members']: w['start_extra'][str(q)] = nx['basis']
    for q in ny['members']: (w['start_extra'] if ny['side'] == 'start' else w['helper_final'])[str(q)] = ny['basis']
    try:
        with deadline(120):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    out.update(narrow=nx['label'], narrow_basis=nx['basis'], narrow_delta=nx['delta'], widen=ny['label'], widen_side=ny['side'],
               widen_basis=ny['basis'], widen_delta=ny.get('delta'), additive=(nx['delta'] + ny['delta']) if ny.get('delta') is not None else None,
               seconds=round(time.time() - t0, 2))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    rows = [json.loads(l) for l in open(JOINT) if l.strip()]
    narrows = [r for r in rows if r['label'].startswith('down:') and r['status'] == 'ok']
    widens = [r for r in rows if (r['label'].startswith('start:') or r['label'].startswith('end:')) and r['status'] == 'ok']
    T = [(dict(label=n['label'], members=n['members'], basis=n['basis'], delta=n['delta']),
          dict(label=y['label'], members=y['members'], basis=y['basis'], side=y['side'], delta=y['delta'])) for n in narrows for y in widens]
    MAXADD = int(os.environ.get('MAX_ADD', '999999999')); T = [t for t in T if t[0]['delta'] + t[1]['delta'] <= MAXADD]
    T.sort(key=lambda t: (t[0]['delta'] + t[1]['delta'], t[0]['label'], t[1]['label']))
    print('narrowings', len(narrows), 'widening options', len(widens), 'pairs', len(T), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=60) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=4), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if r.get('delta') is not None and r['delta'] < 0: print('  NEGATIVE', json.dumps(r)[:300], flush=True)
            if n % 250 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
