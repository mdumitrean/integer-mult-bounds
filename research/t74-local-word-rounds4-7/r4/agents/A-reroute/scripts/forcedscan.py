"""forcedscan: single forced-meet scan (r4 A-reroute, step 1).  Deleted word + ONE structural meet y += q, for every
register y in q's non-full-end column dp and every B/tail slot just after one of y's B/tail gates (or at B start).
Base cone caps (an exact re-delivery restores the base map, hence the base compensation and caps).  Reports the
cheapest feasible slot per y: the per-port relaxation of 'q must meet y somewhere in B/tail'.  usage: forcedscan.py WORD q..."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname = sys.argv[1]; qs = list(map(int, sys.argv[2:])); out = {}
for q in qs:
    t0 = time.time(); aw = AWin(wname, q); w = aw.w; B = w['B']; tail = aw.tail; Bd = set(aw.Breads)
    w1 = H.compile_edits(w, dict(delete=aw.Breads)); seq1B = list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']]
    d = sx.addv(sx.col(list(B) + tail, q), sx.col(seq1B, q), -1); dp = sorted(k for k in d if not aw.full_end(k))
    def run(ins, tl):
        w2 = H.compile_edits(w, dict(delete=aw.Breads, insert=ins, tail=tl))
        try:
            with deadline(120):
                g = F.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=aw.P.caps, cut_equality=True)
                r = F.optimal_frames(inline(w2, True), aw.P.costs, check_literal=False, graph=g)
            return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - aw.P.base_cost)
        except F.Infeasible: return dict(status='infeasible')
        except Timeout: return dict(status='timeout')
    rec = {}
    for y in dp:
        slots = [('B', 0)] + [('B', i + 1) for i, g in enumerate(B) if y in regs(g) and i not in Bd] + [('tail', j + 1) for j, g in enumerate(tail) if y in regs(g)]
        res = []
        for sec, p in slots:
            r = run([[p, gate(y, q, 1)]], []) if sec == 'B' else run([], [[p, gate(y, q, 1)]])
            res.append(dict(sec=sec, pos=p, **r))
        feas = [r for r in res if r['status'] == 'ok']
        best = min(feas, key=lambda r: r['delta']) if feas else None
        rec[y] = dict(slots=len(res), feasible=len(feas), best=best, all=res)
        print(q, 'y', y, 'slots', len(res), 'feasible', len(feas), 'best', (best['sec'], best['pos'], best['delta']) if best else None, flush=True)
    out[q] = dict(dp=dp, ports=rec, seconds=round(time.time() - t0, 1))
json.dump(out, open(os.path.join(HERE, '..', 'out', f'FORCEDSCAN-{wname}-' + '-'.join(map(str, qs)) + '.json'), 'w'), indent=1, default=str)
