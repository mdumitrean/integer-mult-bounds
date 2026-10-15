"""tscan.py: in-B compensation for q at many delivery slots t (every STEP B positions up to TMAX), with q's start frame span(u).
3 workers, 60 s deadline, RSS flag.  usage: tscan.py WORD OUT.jsonl q:u:tmax[,...] STEP"""
import json, os, sys, time, multiprocessing as mp
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout, peak_rss_gib
import zcore as Z
WORD, OUT, SPEC, STEP = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
B = "0.001679754956125544"; BASE = COSTS = BCOST = None
def init():
    global BASE, COSTS, BCOST
    BASE = Z.load(WORD); COSTS = F.Costs(B)
    caps, comp = cone_caps(BASE); g = F.Graph(inline(BASE, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    BCOST = F.optimal_frames(inline(BASE, True), COSTS, check_literal=False, graph=g)['cost']
def run(task):
    q, u, t = task; t0 = time.time(); out = dict(q=q, u=u, t=t)
    try:
        w1, info = Z.build_at(BASE, q, [u], t)
        if w1 is None: out.update(info); return out
        out.update(deliveries=info['deliveries'], leak_after=info['leak_after'])
        with deadline(60):
            caps, comp = cone_caps(w1)
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), COSTS, check_literal=False, graph=g)
        out.update(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - BCOST, profile=dict(sorted(r['profile'].items())), comp_reads_q=sum(1 for e in comp if e[2] == q))
    except F.Infeasible as e: out.update(status='infeasible', why=list(map(str, e.args[0][:4])) if e.args else None)
    except Timeout: out.update(status='timeout')
    except ValueError as e: out.update(status='error:' + str(e)[:60])
    out['seconds'] = round(time.time() - t0, 2); rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    T = []
    for part in SPEC.split(','):
        q, u, tmax = map(int, part.split(':')); T += [(q, u, t) for t in range(0, tmax + 1, STEP)]
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, initializer=init, maxtasksperchild=60) as pool:
        for r in pool.imap_unordered(run, T, chunksize=2): f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
    print('done', len(T), flush=True)
