"""endnarrow: narrow a helper by one level on the END side (helper_final = an 8-dim hyperplane containing the helper's
frame just before its final climb in the base word's optimal frames), singles for every width-5 helper and every helper
group sharing a start frame; exact optimal frames with recomputed cone caps.  3 workers, deadline, RSS flag.
usage: endnarrow.py TOOLKIT INPUTS OUT.jsonl"""
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
    label, members, bases = task; t0 = time.time(); w = copy.deepcopy(BASE)
    for q, b in zip(members, bases): w['helper_final'][str(q)] = b
    try:
        with deadline(90):
            r, g, nc = K.solve(w, COSTS)
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp=nc)
    except F.Infeasible: out = dict(status='infeasible')
    except Timeout: out = dict(status='timeout')
    except ValueError as e: out = dict(status='error:' + str(e)[:60])
    rss = peak_rss_gib(); out.update(label=label, members=members, bases=bases, seconds=round(time.time() - t0, 2))
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
def prefinal(w):
    """each register's frame after A, centres, B and the early tail (before the final climb), from the stored frames"""
    v, R = w['report']['v'], w['report']['R']; n = 2 * v + R
    cur = [W.span((p,)) for p in w['ports']] + [frozenset((0,))] * (n - v)
    for q, vs in w['start_extra'].items(): cur[int(q)] = W.span(tuple(vs))
    for sec in ('A', 'B'):
        for e in w[sec]:
            t = W.span(tuple(e[-1]))
            for r in (e[1:3] if e[0] == 'add' else e[1:2]): cur[r] = t
    for i, vs in w['early_cleanup']:
        e = w['cleanup'][i]; t = W.span(tuple(vs))
        for r in (e[1:3] if e[0] == 'add' else e[1:2]): cur[r] = t
    return cur
def hyper_containing(P):
    """all 8-dim subspaces of GF(2)^9 containing span P, as basis lists"""
    pv = [x for x in P if x]; basis = list(K.echelon(pv).values()); out = []
    for H in K.hyperplanes(list(range(1, 512)) and [1 << i for i in range(9)]):
        if all(K.reduce_vec(b, K.echelon(H)) == 0 for b in basis): out.append(H)
    return out
def tasks():
    w = K.load(f'{INP}/gauge44-word-566-554.json.gz'); paid, centre, widths, starts, ends, endB = W.recount(w)
    v, R = w['report']['v'], w['report']['R']; P = prefinal(w); T = []; groups = collections.defaultdict(list); cand = {}
    for q in range(2 * v, 2 * v + R):
        if widths[q - 2 * v] == 5 and W.dimension(ends[q]) == 9:
            cand[q] = hyper_containing(P[q]); groups[tuple(sorted(w['start_extra'].get(str(q), [])))].append(q)
            for H in cand[q]: T.append((f'single:{q}', [q], [H]))
    for frame, mem in groups.items():
        for combo in itertools.product(*[cand[q] for q in mem]):
            T.append((f'group:{mem[0]}..{mem[-1]}', mem, list(combo)))
    info = {q: dict(prefinal_dim=W.dimension(P[q]), candidates=len(cand[q])) for q in cand}
    return T, info
if __name__ == '__main__':
    T, info = tasks(); print('tasks', len(T), 'prefinal dims', dict(collections.Counter(i['prefinal_dim'] for i in info.values())), flush=True); t0 = time.time()
    json.dump(info, open(OUT.replace('.jsonl', '-INFO.json'), 'w'), sort_keys=True)
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=40) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=2), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            if n % 50 == 0: print(f'  {n}/{len(T)} {time.time()-t0:.0f}s', flush=True)
    print('done', len(T), f'{time.time()-t0:.0f}s', flush=True)
