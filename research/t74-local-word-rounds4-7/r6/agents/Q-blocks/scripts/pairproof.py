"""pairproof.py SYSTEM_DIR OUT.json (agent Q-blocks, r6): exact pair-cover proof for a round-1 split-key system.
Every exact solution has, for each right-hand-side row r with a nonzero value, some insert with a nonzero coefficient in r
(C(r)).  Take the two such rows with the smallest C(r); if every pair (a, b) in C(r1) x C(r2), a != b, is frame-infeasible
(cone.LU's exact single-insert test on W1 + a, both placements when b shares a's position), no exact frame-feasible
solution exists: inserts only add frame constraints, so a superset of an infeasible pair is infeasible.  Candidates that
lie in both rows are checked as singletons too (a single insert in C(r1) & C(r2) could cover both rows)."""
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
rows = {e: sorted(set(J[E == e].tolist())) for e in rhs}
order = sorted(rows, key=lambda e: len(rows[e])); r1, r2 = order[0], order[1]
A_, B_ = rows[r1], rows[r2]; both = sorted(set(A_) & set(B_))
print('rhs rows', {e: len(c) for e, c in rows.items()}, 'pick', r1, len(A_), r2, len(B_), 'in both', len(both), flush=True)
WORD = os.path.join(HERE, '..', '..', '..', '..', 'r3', 'inputs', meta['word'])
Pw = H.Pricer(WORD); DELS = [tuple(d) for d in meta['dels']]; W1 = compile_AB(Pw.base, dict(delete=DELS))
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))
compatible = []; done = 0
for a in A_:
    x, y, pa, _ = CM[a]; lu = LU(Pw, build(W1, [(pa, ['add', x, y, 1, 1, []])]))
    for b in B_:
        if b == a: continue
        xb, yb, pb, _ = CM[b]
        ok = lu.ok(xb, yb, pb) if pb < pa else lu.ok(xb, yb, pb + 1) if pb > pa else (lu.ok(xb, yb, pa) or lu.ok(xb, yb, pa + 1))
        if ok: compatible.append((a, b))
    done += 1
    if done % 25 == 0: print(f'  {done}/{len(A_)} compatible pairs so far {len(compatible)} {time.time()-t00:.0f}s', flush=True)
out = dict(meta=meta, rows={str(e): len(c) for e, c in rows.items()}, r1=r1, r2=r2, n1=len(A_), n2=len(B_), in_both=len(both),
           compatible_pairs=len(compatible), sample=[(CM[a][:3], CM[b][:3]) for a, b in compatible[:50]],
           singles_in_both=[CM[j][:3] for j in both],
           verdict=('PROOF: every cover pair is frame-infeasible' if not compatible and not both else 'not closed by the pair cover'),
           seconds=round(time.time() - t00, 1))
json.dump(out, open(outp, 'w'), indent=1); print('done', out['verdict'], 'compatible', len(compatible), 'both', len(both), out['seconds'], flush=True)
