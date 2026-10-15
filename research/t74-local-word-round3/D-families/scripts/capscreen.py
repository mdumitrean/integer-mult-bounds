"""capscreen: information-flow frame bound for never-written pivots.
Any exact B/tail/prepend edit keeps q's column of the B+tail map on the ports (prepends may not touch ports), so for every
port y with d_y != 0 some chain of meets carries q's information to y after A.  Upper frames are monotone along chains and
every vertex of y lies inside y's end hyperplane perp(p_y); hence q's frame at that first meet, and so q's A-end frame,
lies in K(q) = intersection of perp(p_y) over those ports.  capscreen prices, per pivot:
  screen   = delete all B reads of q (no compensation; heuristic, as in #1337/round 2);
  capped   = the same with q's A-end frame (its last A vertex) capped at K(q): an optimistic bound for
             compensations that only insert gates; the difference is the part of the screen no exact edit can realize.
usage: capscreen.py WORD OUT.json q1,q2,..."""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'r2h')); sys.path.insert(1, os.path.dirname(os.path.abspath(__file__)))
from common import *
import sx
from model import meet
import frames_x as FX
WN, OUT, QS = sys.argv[1:4]
P = H.Pricer(WORDS[WN], b=os.environ['IMB_B'], check_literal=True); w = P.base; B = w['B']
seq = list(B) + [w['cleanup'][i] for i, U in w['early_cleanup']]; N = sx.nregs(w); Sfx = sx.Suffix(seq, N)
FULL = tuple(1 << i for i in range(9))
def price_caps(w1, caps, xcaps=None):
    FX.XCAPS.clear(); FX.XCAPS.update(xcaps or {})
    try:
        with deadline(300):
            g = FX.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = FX.optimal_frames(inline(w1, True), FX.Costs(os.environ['IMB_B']), check_literal=False, graph=g)
        return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - P.base_cost, profile=dict(sorted(r['profile'].items())))
    except (F.Infeasible, FX.Infeasible): return dict(status='infeasible')
    except Timeout: return dict(status='timeout')
out = {}
for q in map(int, QS.split(',')):
    t0 = time.time()
    reads = [i for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
    col = sx.col(seq, q)                       # q's column of the B+tail map (exactness keeps it)
    low = {int(k): tuple(U) for k, U in w['helper_final'].items()}
    ports = sorted(k for k in col if 112 <= k < 224 and k != q); lows = sorted(k for k in col if k in low and k != q)
    K = FULL
    for y in ports: K = meet(K, tuple(F.G.perp(w['ports'][y - 112])))
    for y in lows: K = meet(K, F.basis(low[y]))
    w1 = H.compile_edits(w, dict(delete=reads)); caps1, comp1 = cone_caps(w1)
    s = price_caps(w1, caps1)
    c = price_caps(w1, caps1, {q: K})
    b0 = price_caps(w, cone_caps(w)[0], {q: K})            # control: the base word itself satisfies the bound
    out[q] = dict(reads=reads, ports=ports, lows=lows, K=list(K), dimK=len(K), screen=s, capped=c, base_capped=b0,
                  unrealizable=(c.get('delta', 0) - s.get('delta', 0)) if s.get('delta') is not None and c.get('delta') is not None else None)
    print(q, 'reads', len(reads), 'ports', ports, 'lows', lows, 'dimK', len(K), 'screen', s.get('status'), s.get('delta'), '| capped', c.get('status'), c.get('delta'), '| base capped', b0.get('status'), b0.get('delta'), f'{time.time()-t0:.1f}s', flush=True)
json.dump(out, open(OUT, 'w'), indent=1)
