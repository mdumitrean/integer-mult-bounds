"""bulk.py: in-B compensation construction for every frame-feasible width-9 helper/basis of r5 C's NARROW-base.jsonl
(excluding agent A's 478/479/490/491), at delivery slots B0, B550 and B705.  3 workers, 60 s deadline, RSS flag 6 GiB.
usage: bulk.py WORD NARROW.jsonl OUT.jsonl"""
import copy, json, os, sys, time, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout, peak_rss_gib
import zcore as Z
WORD, NARROW, OUT = sys.argv[1:4]
B = "0.001679754956125544"; BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = Z.load(WORD); COSTS = F.Costs(B)
    caps, comp = cone_caps(BASE); g = F.Graph(inline(BASE, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    BCOST = F.optimal_frames(inline(BASE, True), COSTS, check_literal=False, graph=g)['cost']
def run(task):
    q, basis, t = task; t0 = time.time(); out = dict(q=q, basis=basis, t=t)
    try:
        w1, info = Z.build_at(BASE, q, basis, t)
        if w1 is None: out.update(info); return out
        out.update(deliveries=info['deliveries'], moved=info['moved'], leak_after=info['leak_after'])
        with deadline(60):
            caps, comp = cone_caps(w1)
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), COSTS, check_literal=False, graph=g)
        out.update(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())),
                   comp=len(comp), comp_reads_q=sum(1 for e in comp if e[2] == q))
    except F.Infeasible as e: out.update(status='infeasible', why=list(map(str, e.args[0][:4])) if e.args else None)
    except Timeout: out.update(status='timeout')
    except ValueError as e: out.update(status='error:' + str(e)[:60])
    out['seconds'] = round(time.time() - t0, 2); rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    rows = [json.loads(l) for l in open(NARROW)]
    tasks = sorted({(r['q'], tuple(r['basis'])) for r in rows if r['status'] == 'ok' and r['q'] not in (478, 479, 490, 491)})
    T = [(q, list(b), t) for q, b in tasks for t in (0, 550, 705)]
    print('tasks', len(T), flush=True); t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=60) as pool:
        for n, r in enumerate(pool.imap_unordered(run, T, chunksize=4), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
    print('done', f'{time.time()-t0:.0f}s', flush=True)
