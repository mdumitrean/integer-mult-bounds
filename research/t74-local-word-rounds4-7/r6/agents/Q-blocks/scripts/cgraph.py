"""cgraph.py SYSTEM_DIR OUT_PREFIX [TOTAL_S] [ITER_S] [MAX_ADD] (agent Q-blocks, r6): exactness model with an explicit pairwise
frame-conflict graph, solved with growing equation rows (after agent I-resolve's rowgen.py).

Candidates C_K = inserts with a nonzero coefficient in the current row set K (start: the nonzero rhs rows).  For every pair
in C_K the frame test is exact: with a inserted (a passed the single-insert cone test on W1, so W1+a is feasible), cone.LU's
local test on W1+a decides whether W1+a+b is feasible (both placements when b shares a's position: conflict only if both
fail).  Each candidate a adds one star constraint  sum_{b in conf(a)} z_b + 12 z_a <= 12  over the partners present when it
joins; later candidates cover their own pairs.

Soundness: frames are monotone (an insert only adds constraints), so every subset of a frame-feasible set is frame-feasible;
the projection of any exact, frame-feasible solution of the full model onto C_K satisfies the K rows, sum z <= 12, the
budget, and every pair constraint.  So INFEASIBLE of the restricted model (at any K) proves that no exact frame-feasible
solution exists in the full model.  A solution exact on all rows is confirmed with the whole-map exactness check and the
FULL frames.Graph test (a set can fail with no failing pair); a failure adds its minimal conflict as a no-good.
Checkpoints: OUT_PREFIX-ckpt.json (rows, candidates, conflict counts, iterations) every few iterations."""
import json, os, sys, time
import numpy as np
from collections import defaultdict
from fractions import Fraction as Qf
from ortools.sat.python import cp_model
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'N-bigA', 'tools')); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))
from sk3 import H, compile_AB, maps, word_seq_insert, absorbable, exact_proj
from sk4 import to_base_edit_ab4
from cone import LU, feasible, minimal_conflict
sysdir, pref = sys.argv[1], sys.argv[2]
TOTAL = float(sys.argv[3]) if len(sys.argv) > 3 else 8000; ITER = float(sys.argv[4]) if len(sys.argv) > 4 else 300
MAXADD = int(sys.argv[5]) if len(sys.argv) > 5 else 400
t00 = time.time(); Z = np.load(os.path.join(sysdir, 'system.npz')); meta = json.load(open(os.path.join(sysdir, 'out.json')))['meta']
E, C, J, costs = Z['E'], Z['C'], Z['J'].astype(np.int64), Z['costs']
rhs = {int(e): int(v) for e, v in zip(Z['rhs_ids'].tolist(), Z['rhs_vals'].tolist())}
n = len(costs); bud = meta['bud']; lamr = meta['lamr']; maxterms = meta['maxterms']; CM = [tuple(r) for r in Z['candmeta'].tolist()]
uE, st = np.unique(E, return_index=True); en = np.append(st[1:], len(E)); seg = {int(e): (int(a), int(b)) for e, a, b in zip(uE, st, en)}
oj = np.argsort(J, kind='stable'); Jo, Eo, Co = J[oj], E[oj], C[oj]
js, jstart = np.unique(Jo, return_index=True); jend = np.append(jstart[1:], len(Jo)); jseg = {int(j): (int(a), int(b)) for j, a, b in zip(js, jstart, jend)}
WORD = os.path.join(HERE, '..', '..', '..', '..', 'r3', 'inputs', meta['word'])
Pw = H.Pricer(WORD); base_maps = maps(Pw.base); ab = absorbable(Pw.base); DELS = [tuple(d) for d in meta['dels']]
W1 = compile_AB(Pw.base, dict(delete=DELS)); build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))
print('loaded', n, 'cand', len(uE), 'rows', f'{time.time()-t00:.1f}s', flush=True)
# ---- model state
m = cp_model.CpModel(); lam = {}; z = {}; inK = set(); order = []; conf_cnt = {}; stats = dict(lu_builds=0, pair_tests=0, conflicts=0)
card = []; costterms = []
def add_candidates(new):
    """create variables for new candidates and their exact pair conflicts with every candidate present."""
    present = order[:]   # candidates already in the model
    for a in new:
        l = m.NewIntVar(-lamr, lamr, f'l{a}'); b = m.NewBoolVar(f'z{a}'); m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b)
        lam[a] = l; z[a] = b
    allp = present + list(new)
    for k, a in enumerate(new):
        x, y, pa, _ = CM[a]; lu = LU(Pw, build(W1, [(pa, ['add', x, y, 1, 1, []])])); stats['lu_builds'] += 1
        partners = present + list(new[:k])   # pairs (a, b) with b already present or earlier in this batch
        bad = []
        for b_ in partners:
            xb, yb, pb, _ = CM[b_]
            ok = lu.ok(xb, yb, pb) if pb < pa else lu.ok(xb, yb, pb + 1) if pb > pa else (lu.ok(xb, yb, pa) or lu.ok(xb, yb, pa + 1))
            stats['pair_tests'] += 1
            if not ok: bad.append(b_)
        conf_cnt[a] = len(bad); stats['conflicts'] += len(bad)
        if bad: m.Add(sum(z[b_] for b_ in bad) + maxterms * z[a] <= maxterms)
        order.append(a)
        if (k + 1) % 200 == 0: print(f'   +{k+1}/{len(new)} lu {stats["lu_builds"]} tests {stats["pair_tests"]} conflicts {stats["conflicts"]} {time.time()-t00:.0f}s', flush=True)
def add_rows(rows):
    for e in rows:
        a, b_ = seg[e]; jj = J[a:b_].tolist(); cc = C[a:b_].tolist()
        m.Add(sum(c * lam[j] for j, c in zip(jj, cc)) == rhs.get(e, 0)); inK.add(e)
def ckpt(status, extra=None):
    d = dict(meta=meta, status=status, rows=len(inK), candidates=len(order), stats=stats, iterations=it, proposals=len(props),
             good=good, conflicts_logged=nogood_log[-50:], seconds=round(time.time() - t00, 1))
    if extra: d.update(extra)
    json.dump(d, open(pref + '-ckpt.json', 'w'), indent=1, default=str)
for e in rhs:
    if e not in seg: print('rhs row unreachable -> SHAPE_INFEASIBLE'); json.dump(dict(meta=meta, status='SHAPE_INFEASIBLE'), open(pref + '-final.json', 'w')); sys.exit()
it = 0; props = []; good = []; nogood_log = []
K0 = sorted(rhs); newc = sorted(set(np.concatenate([J[seg[e][0]:seg[e][1]] for e in K0]).tolist()))
print('initial rows', len(K0), 'candidates', len(newc), flush=True)
add_candidates(newc); add_rows(K0); ckpt('building')
status = None
while time.time() - t00 < TOTAL:
    it += 1; t0 = time.time()
    zs = [z[j] for j in order]
    mm = m.Clone(); mm.Add(sum(zs) <= maxterms)
    mm.Add(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) for j in order]) <= bud)
    mm.Minimize(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) + 50 for j in order]))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = min(ITER, max(10.0, TOTAL - (time.time() - t00))); sv.parameters.num_workers = 1
    r = sv.Solve(mm); sname = sv.StatusName(r)
    rec = dict(it=it, rows=len(inK), cand=len(order), status=sname, seconds=round(time.time() - t0, 1))
    if r == cp_model.INFEASIBLE: status = 'INFEASIBLE'; print(rec, flush=True); break
    if r not in (cp_model.FEASIBLE, cp_model.OPTIMAL): status = 'UNKNOWN'; print(rec, flush=True); break
    sol = {j: sv.Value(lam[j]) for j in order if sv.Value(lam[j]) != 0}
    res = {}
    for j, l in sol.items():
        a, b_ = jseg[j]
        for e, c in zip(Eo[a:b_].tolist(), Co[a:b_].tolist()): res[e] = res.get(e, 0) + c * l
    for e, v in rhs.items(): res[e] = res.get(e, 0) - v
    bad = sorted((e for e, v in res.items() if v != 0 and e not in inK), key=lambda e: -abs(res[e]))
    rec.update(support=len(sol), est=int(sum(costs[j] for j in sol)), violated=len(bad)); print(rec, flush=True)
    if bad:
        rows = bad[:MAXADD]; newc = sorted(set(np.concatenate([J[seg[e][0]:seg[e][1]] for e in rows]).tolist()) - set(order))
        print(f'   grow rows +{len(rows)} candidates +{len(newc)}', flush=True)
        add_candidates(newc); add_rows(rows); ckpt('running'); continue
    # exact on all rows: whole-map exactness and the FULL frame test
    items = sorted(((CM[j][2], j, l) for j, l in sol.items()))
    ins = [(p, ['add', CM[j][0], CM[j][1], Qf(l, 4).numerator, Qf(l, 4).denominator, []]) for p, j, l in items]; jj = [j for p, j, l in items]
    W2 = build(W1, ins); props.append([(CM[j][:3], str(Qf(l, 4))) for p, j, l in items])
    if not exact_proj(base_maps, W2, ab):
        m.Add(sum(z[j] for j in jj) <= len(jj) - 1); nogood_log.append(dict(kind='inexact', size=len(jj))); print('   inexact -> support no-good', flush=True); continue
    ok, why = feasible(Pw, W2)
    if ok:
        try: ed = to_base_edit_ab4(Pw.base, DELS, W1, ins)
        except Exception as ex: ed = dict(error=repr(ex)[:100])
        good.append(dict(terms=[(p, CM[j][0], CM[j][1], str(Qf(l, 4))) for p, j, l in items], est=int(sum(costs[j] for j in sol)), exact=True, edit_ab=ed))
        m.Add(sum(z[j] for j in jj) <= len(jj) - 1); print('   FRAME-FEASIBLE exact proposal', len(good), flush=True); ckpt('running')
        if len(good) >= 20: status = 'GOOD_LIMIT'; break
        continue
    mc = minimal_conflict(Pw, W1, ins, build); cj = [jj[k] for k in mc]
    m.Add(sum(z[j] for j in cj) <= len(cj) - 1); nogood_log.append(dict(kind='frames', size=len(cj), why=str(why)[:100], members=[CM[j][:3] for j in cj]))
    print(f'   full-Graph conflict of size {len(cj)} (pairs were compatible) -> no-good', flush=True); ckpt('running')
if status is None: status = 'TIME'
ckpt(status); json.dump(dict(meta=meta, status=status, rows=len(inK), candidates=len(order), stats=stats, iterations=it, proposals=props, good=good,
                             nogoods=nogood_log, conf_degree=dict(max=max(conf_cnt.values()) if conf_cnt else 0, mean=(sum(conf_cnt.values()) / len(conf_cnt)) if conf_cnt else 0),
                             seconds=round(time.time() - t00, 1)), open(pref + '-final.json', 'w'), indent=1, default=str)
print('done', status, round(time.time() - t00, 1), flush=True)
