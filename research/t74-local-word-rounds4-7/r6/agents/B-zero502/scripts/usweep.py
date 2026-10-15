"""usweep.py: for helper q, price the in-B compensation construction (A-writes of q re-timed to B-start, B-start target
deliveries cancelling q's leak) with q entering at every 1-dim start frame span(u), u in 1..511.
3 workers, per-task deadline 60 s, RSS flag 6 GiB with recycling.  usage: usweep.py WORD Q OUT.jsonl"""
import copy, json, os, sys, time, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout, peak_rss_gib
import zcore as Z
WORD, QQ, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3]
B = "0.001679754956125544"; BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = Z.load(WORD); COSTS = F.Costs(B)
    caps, comp = cone_caps(BASE); g = F.Graph(inline(BASE, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    BCOST = F.optimal_frames(inline(BASE, True), COSTS, check_literal=False, graph=g)['cost']
def run(u):
    t0 = time.time(); out = dict(q=QQ, u=u)
    try:
        w1, info = Z.build(BASE, QQ, [u])
        with deadline(60):
            caps, comp = cone_caps(w1)
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), COSTS, check_literal=False, graph=g)
        out.update(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())),
                   comp=len(comp), comp_reads_q=sum(1 for e in comp if e[2] == QQ))
    except F.Infeasible as e: out.update(status='infeasible', why=list(map(str, e.args[0][:4])) if e.args else None)
    except Timeout: out.update(status='timeout')
    except ValueError as e: out.update(status='error:' + str(e)[:60])
    out['seconds'] = round(time.time() - t0, 2); rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    t0 = time.time()
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=80) as pool:
        for n, r in enumerate(pool.imap_unordered(run, range(1, 512), chunksize=8), 1):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
    print('done', f'{time.time()-t0:.0f}s', flush=True)
