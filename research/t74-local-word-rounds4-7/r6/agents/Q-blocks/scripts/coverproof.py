"""coverproof.py SYSTEM_DIR OUT.json (agent Q-blocks, r6): exact row-cover proof for a round-1 split-key system.
Every exact solution contains, for each right-hand-side row r with a nonzero value, an insert with a nonzero coefficient
in r.  Frame feasibility is monotone (inserts only add constraints), so if no frame-feasible set of at most |R| candidates
hits every nonzero rhs row, no exact frame-feasible solution exists.  Enumeration: a in C(r1) (smallest row); b over
candidates hitting a row a misses, tested with cone.LU on W1+a (exact single-insert test; both placements on ties); if a
and b still miss a row, c is tested with cone.LU on W1+a+b.  Every frame-feasible covering set found is reported."""
import json, os, sys, time
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'N-bigA', 'tools')); sys.path.insert(0, os.path.join(HERE, '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))
from sk3 import H, compile_AB, word_seq_insert
from cone import LU
sysdir, outp = sys.argv[1], sys.argv[2]; t00 = time.time()
Z = np.load(os.path.join(sysdir, 'system.npz')); meta = json.load(open(os.path.join(sysdir, 'out.json')))['meta']
E, J = Z['E'], Z['J']; CM = [tuple(r) for r in Z['candmeta'].tolist()]
rhs = {int(e): int(v) for e, v in zip(Z['rhs_ids'].tolist(), Z['rhs_vals'].tolist()) if int(v) != 0}
R = sorted(rhs); rows = {e: set(J[E == e].tolist()) for e in R}
hit = {}
for e in R:
    for j in rows[e]: hit.setdefault(j, set()).add(e)
order = sorted(R, key=lambda e: len(rows[e])); r1 = order[0]
print('rows', {e: len(rows[e]) for e in R}, 'r1', r1, 'candidates hitting any row', len(hit), flush=True)
WORD = os.path.join(HERE, '..', '..', '..', '..', 'r3', 'inputs', meta['word'])
Pw = H.Pricer(WORD); DELS = [tuple(d) for d in meta['dels']]; W1 = compile_AB(Pw.base, dict(delete=DELS))
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))
def okat(lu, ps, k):
    """exact test of candidate k on a word with extra inserts at W1 positions ps (sorted list)."""
    xk, yk, pk, _ = CM[k]; shift = sum(1 for p in ps if p < pk); tie = sum(1 for p in ps if p == pk)
    return any(lu.ok(xk, yk, pk + shift + t) for t in range(tie + 1))
gate = lambda j: (CM[j][2], ['add', CM[j][0], CM[j][1], 1, 1, []])
found = []; nlu = 1; stats = dict(singles=0, pairs_ok=0, triples_tested=0)
for j, h in hit.items():
    if h == set(R): found.append([j]); stats['singles'] += 1
for ia, a in enumerate(sorted(rows[r1])):
    luA = LU(Pw, build(W1, [gate(a)])); nlu += 1; miss_a = set(R) - hit[a]
    Bs = [b for b in hit if b != a and hit[b] & miss_a]
    for b in Bs:
        if not okat(luA, [CM[a][2]], b): continue
        miss = miss_a - hit[b]
        if not miss: found.append([a, b]); stats['pairs_ok'] += 1; continue
        stats['pairs_ok'] += 1
        Cs = [c for c in hit if c not in (a, b) and hit[c] >= miss]
        if not Cs: continue
        luAB = LU(Pw, build(W1, [gate(a), gate(b)])); nlu += 1; ps = sorted([CM[a][2], CM[b][2]])
        for c in Cs:
            stats['triples_tested'] += 1
            if okat(luAB, ps, c): found.append([a, b, c])
        if len(found) > 200: break
    if (ia + 1) % 20 == 0: print(f'  {ia+1}/{len(rows[r1])} found {len(found)} stats {stats} LU {nlu} {time.time()-t00:.0f}s', flush=True)
    if len(found) > 200: break
verdict = 'PROOF: no frame-feasible set of <= %d candidates covers every nonzero rhs row' % len(R) if not found else 'not closed: frame-feasible covering sets exist'
out = dict(meta=meta, rows={str(e): len(rows[e]) for e in R}, r1=r1, stats=stats, lu_builds=nlu, found=len(found),
           sample=[[CM[j][:3] for j in s] for s in found[:40]], verdict=verdict, seconds=round(time.time() - t00, 1))
json.dump(out, open(outp, 'w'), indent=1); print('done', verdict, 'found', len(found), stats, out['seconds'], flush=True)
