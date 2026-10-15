"""calib_cone.py WORD OUTDIR RUNS...: replay every frame-rejected exact second-order word of the earlier runs through the
cone-aware filter: (1) local single-insert test of each round-1 insert on W1 and of each round-2 insert on W2,
(2) exact set test of W2 and W3 (Graph under base caps), (3) the exact pricer's verdict on W3 (must agree)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import *
from runjob import exact
from cone import LU, feasible, minimal_conflict
word, od, runs = sys.argv[1], Path(sys.argv[2]), sys.argv[3:]
P = H.Pricer(word); bm = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
mk = lambda gg: list(gg[:5]) + [[]]
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))
rows = []
for run in runs:
    for J, rec in enumerate(json.load(open(Path(run) / 'out.json'))):
        dels = [tuple(d) for d in rec['dels']]; W1 = compile_AB(P.base, dict(delete=dels)); lu1 = LU(P, W1)
        for I1, e1 in enumerate(rec['round1']):
            for I2, e2 in enumerate(e1.get('round2', [])):
                if not (e2.get('exact') and (e2.get('price') or {}).get('status') == 'infeasible'): continue
                t0 = time.time(); ins1 = [(p, mk(g)) for p, g in e2['ins1']]; ins2 = [(p, mk(g)) for p, g in e2['ins2']]
                loc1 = [lu1.ok(g[1], g[2], p) for p, g in ins1]; W2 = build(W1, ins1); f2, why2 = feasible(P, W2)
                loc2 = None; f3, why3 = None, None
                if f2:
                    lu2 = LU(P, W2); loc2 = [lu2.ok(g[1], g[2], p) for p, g in ins2]
                W3 = build(W2, ins2); f3, why3 = feasible(P, W3); assert exact(bm, W3)
                stage = ('local filter, round 1' if not all(loc1) else 'set test, round-1 word' if not f2 else
                         'local filter, round 2' if not all(loc2) else 'set test, final word' if not f3 else 'NOT REJECTED')
                mc = minimal_conflict(P, W1, ins1, build) if (all(loc1) and not f2) else None
                rows.append(dict(run=Path(run).name, dels=dels, round1=I1, round2=I2, local1=loc1, round1_word_feasible=f2,
                                 why_round1_word=str(why2), local2=loc2, final_feasible=f3, why_final=str(why3),
                                 rejected_at=stage, minimal_round1_conflict=[ins1[j] for j in mc] if mc else None,
                                 seconds=round(time.time() - t0, 1)))
                print(rows[-1]['run'], dels, I1, I2, '->', stage, '| local1', loc1, '| W2', f2, why2, '| local2', loc2, '| W3', f3, flush=True)
od.mkdir(parents=True, exist_ok=True); json.dump(rows, open(od / 'CALIBRATION.json', 'w'), indent=1, default=str)
print('rejected up front:', sum(r['rejected_at'] != 'NOT REJECTED' for r in rows), 'of', len(rows))
