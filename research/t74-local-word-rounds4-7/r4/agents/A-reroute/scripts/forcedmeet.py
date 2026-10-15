"""forcedmeet: delivery-forced relaxation diagnostic (r4 A-reroute, step 1).
Deleted word (q's B reads removed) plus STRUCTURAL meets y += q (map not preserved; frames only) placed right after the
last B/tail gate of each register y in q's non-full-end column dp.  Priced with the deleted word's cone caps:
  single: one forced meet at a time (the per-port relaxation, i.e. q's frame must fit y's late upper frame);
  joint:  all forced meets together (q's chain must pass through every meet in time order).
usage: forcedmeet.py WORD q..."""
import sys, os, json, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname = sys.argv[1]; qs = list(map(int, sys.argv[2:])); out = {}
for q in qs:
    aw = AWin(wname, q); w = aw.w; nB = aw.nB; tail = aw.tail
    seq0B = list(w['B']) + tail
    w1 = H.compile_edits(w, dict(delete=aw.Breads)); seq1B = list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']]
    d = sx.addv(sx.col(seq0B, q), sx.col(seq1B, q), -1); dp = sorted(k for k in d if not aw.full_end(k))
    caps1 = cone_caps(w1)[0]
    def placement(y):
        lastB = max([i for i, g in enumerate(w['B']) if y in regs(g) and i not in aw.Breads] or [-1])
        lastT = max([j for j, g in enumerate(tail) if y in regs(g)] or [-1])
        return ('tail', lastT + 1) if lastT >= 0 else ('B', lastB + 1)
    def priced(ys):
        ins, tl = [], []
        for y in ys:
            sec, p = placement(y)
            (tl if sec == 'tail' else ins).append([p, gate(y, q, 1)])
        tl.sort(key=lambda z: z[0]); tl = [[j0 + n, g] for n, (j0, g) in enumerate(tl)]
        w2 = H.compile_edits(w, dict(delete=aw.Breads, insert=ins, tail=tl))
        try:
            with deadline(300):
                g = F.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=caps1, cut_equality=True)
                r = F.optimal_frames(inline(w2, True), aw.P.costs, check_literal=False, graph=g)
            return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - aw.P.base_cost, profile=dict(sorted(r['profile'].items())))
        except F.Infeasible as e: return dict(status='infeasible', why=str(e.args[0][:3]) if e.args else '')
        except Timeout: return dict(status='timeout')
    rec = dict(dp=dp, placements={y: placement(y) for y in dp}, deleted=priced([]), single={}, joint=None)
    for y in dp: rec['single'][y] = priced([y])
    rec['joint'] = priced(dp)
    print(q, 'deleted', rec['deleted'].get('status'), rec['deleted'].get('delta'), '| single:', {y: (v.get('status'), v.get('delta')) for y, v in rec['single'].items()}, '| joint', rec['joint'].get('status'), rec['joint'].get('delta'), flush=True)
    out[q] = rec
json.dump(out, open(os.path.join(HERE, '..', 'out', f'FORCEDMEET-{wname}.json'), 'w'), indent=1, default=str)
