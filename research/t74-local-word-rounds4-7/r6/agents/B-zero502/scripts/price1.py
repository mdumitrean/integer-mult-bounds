"""price1.py: build the in-B compensation word for helper q, re-solve exact optimal frames (cone caps recomputed), write
frames back and save the word.  usage: price1.py WORD Q U[,U..] OUTWORD.json.gz  (toolkit copy in ../toolkit)"""
import gzip, json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
from writeback import write_back
from compat import deadline, Timeout, peak_rss_gib
import zcore as Z
B = "0.001679754956125544"
def solve(w, costs):
    caps, comp = cone_caps(w)
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
    return r, g, comp
def main():
    word, q, u, out = sys.argv[1], int(sys.argv[2]), [int(x) for x in sys.argv[3].split(',')], sys.argv[4]
    costs = F.Costs(B); w = Z.load(word); t0 = time.time()
    with deadline(300):
        rb, gb, compb = solve(w, costs)
    w1, info = Z.build(w, q, u)
    res = dict(q=q, u=u, base_cost=rb['cost'], base_profile=dict(sorted(rb['profile'].items())), base_comp=len(compb), **info)
    if w1 is None: print(json.dumps(res)); return
    try:
        with deadline(300):
            r, g, comp = solve(w1, costs)
        res.update(status='ok' if r['certified'] else 'uncertified', cost=r['cost'], delta=r['cost'] - rb['cost'],
                   profile=dict(sorted(r['profile'].items())), comp=len(comp), comp_reads_q=sum(1 for e in comp if e[2] == q))
        w2 = write_back(w1, g, r['assign'])
        open(out, 'wb').write(gzip.compress(json.dumps(w2, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
        res['word'] = os.path.relpath(out, os.path.join(HERE, '..', '..', '..', '..'))
    except F.Infeasible as e: res.update(status='infeasible', why=str(e.args[0])[:400] if e.args else '')
    except Timeout: res.update(status='timeout')
    res['seconds'] = round(time.time() - t0, 1); rss = peak_rss_gib(); res['peak_rss_gib'] = rss
    print(json.dumps(res))
main()
