"""rowgen_qa.py SYSTEM_DIR OUT.json [TOTAL_S] [ITER_S] [MAX_ADD] [MAX_PROPS] (agent Q-blocks, r6): agent I-resolve's rowgen.py with the
exactness and frame checks inside the loop: a proposal exact on all rows is applied to the deleted word; if the whole map is
not exact (interaction) its support is cut; if the frames are infeasible, a MINIMAL conflicting subset (cone.minimal_conflict)
is added as a no-good (valid for every superset: inserts only add frame constraints) and, as an exact accelerator, each
member a of a conflict gets its full pairwise conflict star: with a inserted (a feasible single insert), cone.LU's exact
single-insert test on W1+a rejects every candidate b with W1+a+b infeasible (both placements when b shares a's position),
and each such pair becomes a no-good; frame-feasible exact proposals are
kept for exact pricing and their support is cut.  So INFEASIBLE means: no exact, frame-feasible solution other than the
reported ones exists in the model.  Original docstring: rowgen.py SYSTEM_DIR OUT.json [TOTAL_S] [ITER_S] [MAX_ADD]: agent I-resolve (r6).
Row generation for the integer split-key model saved by lpcert.py (tensor-deduplicated, interaction ban dropped, i.e. a
relaxation of D-depth2's round-1 model): lambda_j integer in [-16,16] (quarter steps), z_j = [lambda_j != 0],
sum z <= 12, sum cost*z <= budget, equations restricted to a growing row set K (start: the target's nonzero rows).
Every restricted model is a relaxation of the full model, so INFEASIBLE on any K proves the full model infeasible.
A solution exact on ALL rows is an exact proposal (reported for pricing); otherwise its violated rows join K."""
import json, os, sys, time
import numpy as np
from ortools.sat.python import cp_model
sysdir, outp = sys.argv[1], sys.argv[2]
TOTAL = float(sys.argv[3]) if len(sys.argv) > 3 else 1800; ITER = float(sys.argv[4]) if len(sys.argv) > 4 else 120
MAXADD = int(sys.argv[5]) if len(sys.argv) > 5 else 400
MAXPROPS = int(sys.argv[6]) if len(sys.argv) > 6 else 1000000
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'N-bigA', 'tools')); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))
from sk3 import H, F, compile_AB, maps, word_seq_insert, absorbable, exact_proj, to_base_edit_ab
from sk4 import to_base_edit_ab4
from cone import feasible, minimal_conflict, LU
from fractions import Fraction as Qf
t00 = time.time(); Z = np.load(os.path.join(sysdir, 'system.npz')); meta = json.load(open(os.path.join(sysdir, 'out.json')))['meta']
E, C, J, costs = Z['E'], Z['C'], Z['J'].astype(np.int64), Z['costs']
rhs = {int(e): int(v) for e, v in zip(Z['rhs_ids'].tolist(), Z['rhs_vals'].tolist())}
n = len(costs); bud = meta['bud']; lamr = meta['lamr']; maxterms = meta['maxterms']
CM = [tuple(r) for r in Z['candmeta'].tolist()]; BAN = os.environ.get('ROWGEN_BAN', '1') == '1'
excluded = set()
if False:
    ov = None; costs = costs.copy()
    for j, c in ov.get('cost', {}).items(): costs[int(j)] = int(c)
    excluded = set(int(j) for j in ov.get('exclude', []))
    print('override: costs', len(ov.get('cost', {})), 'excluded', len(excluded), flush=True)
uE, st = np.unique(E, return_index=True); en = np.append(st[1:], len(E)); seg = {int(e): (int(a), int(b)) for e, a, b in zip(uE, st, en)}
for e in rhs:
    if e not in seg: print('rhs row unreachable -> INFEASIBLE (shape)', e); json.dump(dict(meta=meta, status='SHAPE_INFEASIBLE'), open(outp, 'w')); sys.exit()
oj = np.argsort(J, kind='stable'); Jo = J[oj]; Eo = E[oj]; Co = C[oj]
js, jstart = np.unique(Jo, return_index=True); jend = np.append(jstart[1:], len(Jo)); jseg = {int(j): (int(a), int(b)) for j, a, b in zip(js, jstart, jend)}
print('loaded', n, 'cand', len(E), 'terms', len(uE), 'rows', f'{time.time()-t00:.1f}s', flush=True)
WORD = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'r3', 'inputs', meta['word'])
Pw = H.Pricer(WORD); base_maps = maps(Pw.base); ab = absorbable(Pw.base); DELS = [tuple(d) for d in meta['dels']]
W1 = compile_AB(Pw.base, dict(delete=DELS)); build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))
checks = dict(exact=0, inexact=0, frames_bad=0, frames_ok=0, stars=0, star_pairs=0); conflicts = []; good = []; star_done = set(); star_ng = []
def star(a, lam=4):
    x, y, pa, _ = CM[a]; W1a = build(W1, [(pa, ['add', x, y, 1, 1, []])]); lu = LU(Pw, W1a); bad = []
    for k in range(n):
        if k == a: continue
        xk, yk, pk, _ = CM[k]
        if pk < pa: ok = lu.ok(xk, yk, pk)
        elif pk > pa: ok = lu.ok(xk, yk, pk + 1)
        else: ok = lu.ok(xk, yk, pa) or lu.ok(xk, yk, pa + 1)
        if not ok: bad.append(k)
    return bad
def check(sol):
    items = sorted(((CM[j][2], j, l) for j, l in sol.items()))
    ins = [(p, ['add', CM[j][0], CM[j][1], Qf(l, 4).numerator, Qf(l, 4).denominator, []]) for p, j, l in items]; jj = [j for p, j, l in items]
    W2 = build(W1, ins)
    if not exact_proj(base_maps, W2, ab): checks['inexact'] += 1; return 'inexact', sorted(sol)
    checks['exact'] += 1; ok, why = feasible(Pw, W2)
    if ok:
        checks['frames_ok'] += 1
        try: ed = to_base_edit_ab4(Pw.base, DELS, W1, ins)
        except Exception as e: ed = dict(error=repr(e)[:100])
        good.append(dict(terms=[(p, CM[j][0], CM[j][1], str(Qf(l, 4))) for p, j, l in items], est=int(sum(costs[j] for j in sol)), exact=True, edit_ab=ed)); return 'good', sorted(sol)
    checks['frames_bad'] += 1; mc = minimal_conflict(Pw, W1, ins, build); cj = sorted(jj[m] for m in mc)
    for a in cj:
        if a in star_done: continue
        star_done.add(a); bad = star(a); checks['stars'] += 1; checks['star_pairs'] += len(bad)
        for k in bad: star_ng.append(sorted((a, k)))
    conflicts.append(dict(why=str(why)[:120], conflict=[CM[j][:3] for j in cj])); return 'frames', cj

K = set(rhs); log = []; proposals = []; status = None; it = 0; nogoods = []; finalK = None; finalC = None
while time.time() - t00 < TOTAL:
    it += 1; t0 = time.time()
    rowsK = sorted(K); cand = np.unique(np.concatenate([J[seg[e][0]:seg[e][1]] for e in rowsK]))
    if excluded: cand = np.array([j for j in cand.tolist() if j not in excluded], np.int64)
    m = cp_model.CpModel(); lam = {}; z = {}
    for j in cand.tolist():
        l = m.NewIntVar(-lamr, lamr, ''); b = m.NewBoolVar(''); m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b)
        lam[j] = l; z[j] = b
    for e in rowsK:
        a, b_ = seg[e]; jj = J[a:b_].tolist(); cc = C[a:b_].tolist()
        m.Add(sum(c * lam[j] for j, c in zip(jj, cc) if j in lam) == rhs.get(e, 0))
    zs = [z[j] for j in cand.tolist()]
    m.Add(sum(zs) <= maxterms)
    if BAN:   # D-depth2/sk2/PR2142 'direct' rule: no insert writing r at p1 with an insert reading r at p2 >= p1
        from collections import defaultdict
        import bisect
        wr = defaultdict(list); rd = defaultdict(list)
        for j in cand.tolist(): x_, y_, p_, _ = CM[j]; wr[x_].append((p_, j)); rd[y_].append((p_, j))
        for r_, writers in wr.items():
            readers = rd.get(r_)
            if not readers: continue
            ps = sorted({p_ for p_, _ in writers}); byp = defaultdict(list); W = {}; prev = None
            for p_, j in writers: byp[p_].append(j)
            for p_ in ps:
                w = m.NewBoolVar('')
                if prev is not None: m.AddImplication(prev, w)
                for j in byp[p_]: m.AddImplication(z[j], w)
                W[p_] = w; prev = w
            for p2, j2 in readers:
                k = bisect.bisect_right(ps, p2) - 1
                if k >= 0: m.AddImplication(z[j2], W[ps[k]].Not())
    m.Add(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) for j in cand.tolist()]) <= bud)
    for ng in nogoods:
        if all(j in z for j in ng): m.Add(sum(z[j] for j in ng) <= len(ng) - 1)
    for a_, k_ in star_ng:
        if a_ in z and k_ in z: m.Add(z[a_] + z[k_] <= 1)
    m.Minimize(cp_model.LinearExpr.WeightedSum(zs, [int(costs[j]) + 50 for j in cand.tolist()]))
    sv = cp_model.CpSolver(); sv.parameters.max_time_in_seconds = min(ITER, max(5.0, TOTAL - (time.time() - t00))); sv.parameters.num_workers = 1
    r = sv.Solve(m); sname = sv.StatusName(r)
    rec = dict(it=it, rows=len(rowsK), cand=int(len(cand)), status=sname, seconds=round(time.time() - t0, 1))
    if r == cp_model.INFEASIBLE:
        status = 'INFEASIBLE'; log.append(rec); print(rec, flush=True); finalK = rowsK; finalC = cand.tolist(); break
    if r not in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        status = 'UNKNOWN'; log.append(rec); print(rec, flush=True); break
    sol = {j: sv.Value(lam[j]) for j in cand.tolist() if sv.Value(lam[j]) != 0}
    res = {}
    for j, l in sol.items():
        a, b_ = jseg[j]
        for e, c in zip(Eo[a:b_].tolist(), Co[a:b_].tolist()): res[e] = res.get(e, 0) + c * l
    for e, v in rhs.items(): res[e] = res.get(e, 0) - v
    bad = sorted((e for e, v in res.items() if v != 0), key=lambda e: -abs(res[e]))
    rec.update(support=len(sol), est=int(sum(costs[j] for j in sol)), violated=len(bad))
    log.append(rec); print(rec, flush=True)
    if not bad:
        kind, ng = check(sol); rec['check'] = kind; rec['nogood'] = len(ng)
        proposals.append(dict(sol={str(j): l for j, l in sol.items()}, est=rec['est'], kind=kind)); nogoods.append(ng)
        print('   check', kind, 'nogood', len(ng), checks, flush=True)
        if len(proposals) >= MAXPROPS: status = 'PROPOSAL_LIMIT'; break
        continue
    K.update(bad[:MAXADD])
if status is None: status = 'TIME'
out = dict(meta=meta, checks=checks, conflicts=conflicts, good=good, star_pairs=len(star_ng), ban=BAN, final_K=finalK, final_cand=finalC, excluded=sorted(excluded), status=status, iterations=it, final_rows=len(K), proposals=proposals, log=log, seconds=round(time.time() - t00, 1))
json.dump(out, open(outp, 'w'), indent=1); print('done', status, out['seconds'], flush=True)
