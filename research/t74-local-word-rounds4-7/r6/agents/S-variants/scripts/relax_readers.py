"""relax_readers: uncompensated deletion relaxation (screen, base cone caps as r3 A relax.py) of the reader-related early
reads on every variant word and on the base and extra words: each single read (12), each reader's three reads (4), and
all 12.  usage: relax_readers.py OUT.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, pool as P
import harness as H
from compat import deadline, Timeout
OUT = os.path.join(os.path.dirname(__file__), '..', 'out'); WORDS = os.path.join(os.path.dirname(__file__), '..', 'words')
G = json.load(open(os.path.join(OUT, 'GROUPS.json')))['groups']; V = json.load(open(os.path.join(OUT, 'VARIANTS.json')))['results']
def delsets(label):
    reads = G[label]['early_reads']; out = [('single', [i]) for i, t, q, c in reads]
    for t in G[label]['readers']: out.append((f'reader{t}', [i for i, tt, q, c in reads if tt == t]))
    out.append(('all12', [i for i, t, q, c in reads])); return out
CACHE = {}
def pricer(path):
    if path not in CACHE: CACHE.clear(); CACHE[path] = H.Pricer(path, b=C.B, check_literal=True)
    return CACHE[path]
def run(task):
    wname, path, label, kind, dels = task; t0 = time.time(); Pr = pricer(path)
    w1 = H.compile_edits(Pr.base, dict(delete=dels))
    try:
        with deadline(120):
            g = C.F.Graph(C.inline(w1, True), check_literal=False, tail_mutable=True, caps=Pr.caps, cut_equality=True)
            r = C.F.optimal_frames(C.inline(w1, True), Pr.costs, check_literal=False, graph=g)
        res = dict(delta=r['cost'] - Pr.base_cost, prof=dict(sorted(r['profile'].items())), cert=r['certified'])
    except C.F.Infeasible: res = dict(status='infeasible')
    except Timeout: res = dict(status='timeout')
    return dict(word=wname, group=label, kind=kind, dels=dels, base_cost=Pr.base_cost, sec=round(time.time() - t0, 2), **res)
if __name__ == '__main__':
    tasks = []
    for nm, path in (('base', os.path.join(C.INP, 'gauge44-word-566-554.json.gz')), ('extra', os.path.join(C.INP, 'extra-word-566-554.json.gz'))):
        for label in G:
            for kind, dels in delsets(label): tasks.append((nm, path, label, kind, dels))
    for v in V:
        path = os.path.join(WORDS, v['name'] + '.json.gz')
        for kind, dels in delsets(v['label']): tasks.append((v['name'], path, v['label'], kind, dels))
    res = []; t0 = time.time()
    def done(r):
        res.append(r)
        if len(res) % 100 == 0: print(len(res), len(tasks), f'{time.time()-t0:.0f}s', flush=True)
    killed = P.run_pool(run, tasks, workers=4, maxtasks=400, chunksize=17, on_result=done)
    json.dump(dict(results=res, killed=killed, seconds=round(time.time() - t0)), open(os.path.join(OUT, sys.argv[1]), 'w'))
    print('done', len(res), 'killed', killed, f'{time.time()-t0:.0f}s')
