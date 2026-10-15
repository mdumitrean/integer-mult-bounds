"""sswap: price SINGLE-helper same-inventory swaps jointly (one (4,9) helper narrowed 5->4 + one (5,9)/(0,4) helper widened
4->5).  Pairs: every pair whose influence regions overlap (regions.py), plus a seeded random control sample of
non-overlapping pairs (expected exactly additive).  4 workers, per-task deadline, RSS check, maxtasksperchild.
usage: sswap.py TOOLKIT WORD.json.gz REGIONS.json SPAIRS.json OUT.jsonl [N_CONTROL]"""
import os, sys, json, time, copy, random, multiprocessing as mp
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F
from compat import deadline, Timeout, peak_rss_gib
import wcore as K
WORD, REG, SP, OUT = sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]; NC = int(sys.argv[6]) if len(sys.argv) > 6 else 200
BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = K.load(WORD); COSTS = F.Costs(K.B); BCOST = K.solve(BASE, COSTS)[0]['cost']
def run(task):
    tag, x, y = task; t0 = time.time(); w = copy.deepcopy(BASE)
    w['start_extra'][str(x['q'])] = x['basis']
    (w['helper_final'] if y['kind'] == 'up-end' else w['start_extra'])[str(y['q'])] = y['basis']
    try:
        with deadline(90):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    out.update(tag=tag, narrow=x, widen=y, additive=x['delta'] + y['delta'], seconds=round(time.time() - t0, 2))
    rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    pairs = json.load(open(SP)); T = [('overlap', p['narrow'], p['widen']) for p in pairs]
    R = json.load(open(REG)); nar = [r for r in R if r['kind'] == 'down-start' and r['status'] == 'ok']
    wid = [r for r in R if r['kind'] in ('up-start', 'up-end') and r['status'] == 'ok']
    seen = {(p['narrow']['q'], p['widen']['q'], tuple(p['widen']['basis'])) for p in pairs}; rng = random.Random(20261015); ctl = []
    while len(ctl) < NC:
        x, y = rng.choice(nar), rng.choice(wid)
        if (x['q'], y['q'], tuple(y['basis'])) in seen or set(x['region']) & set(y['region']): continue
        seen.add((x['q'], y['q'], tuple(y['basis'])))
        ctl.append(('control', dict(q=x['q'], basis=x['basis'], delta=x['delta']), dict(q=y['q'], kind=y['kind'], basis=y['basis'], delta=y['delta'])))
    T += ctl; print('overlap pairs', len(pairs), 'controls', len(ctl), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(4, initializer=init, maxtasksperchild=60) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=4), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if r.get('delta') is not None and r['delta'] < 0: print('  NEGATIVE', json.dumps(r)[:300], flush=True)
            if n % 200 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
