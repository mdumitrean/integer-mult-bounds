"""sentinel.py WORD BINDEX DEPTH OUT.json: agent I-resolve (r6).
Lists the cone-valid round-1 candidates that #1957's per-insert oracle prices at the 2^60 sentinel (D-depth2's per-insert
cap = budget silently drops them) and prices each one EXACTLY as a standalone insert (lambda = 1) into the deleted word W1:
exact optimal frames of W1 + insert (P.caps, tail-mutable, cut equality) minus the exact cost of W1."""
import json, os, sys, time
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lpcert
from lpcert import gen2u, SENT, H, F, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back, V, LU
from sk2 import word_seq_insert
sys.path.insert(0, os.path.join(lpcert.DSCR, '..', '..', '..', '..', 'r3', 'agents', 'B-interact', 'tools'))
from compat_shim import deadline, Timeout
word, bi, depth, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
t00 = time.time(); P = H.Pricer(word); base_maps = maps(P.base); dels = [('B', bi)]
W1 = compile_AB(P.base, dict(delete=dels))
g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); c1 = r['cost']; ddel = c1 - P.base_cost
orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1
NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); gg = seq0[NA + NC + bi]; regs = {gg[1], gg[2]}
nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
fam, famregs = family_values(fullseq(W1), regs, nreg, depth)
R = gen2u.FastRound(P, W1, base_maps, orc, lambda i: i, fam, 1.0, bud, orc_secs=sec_sizes(W1)); R.lu = LU(P, W1)
cand = R.candidates(); sent = [c for c in cand if c[5] >= SENT]
print('ddel', ddel, 'bud', bud, 'cand', len(cand), 'sentinel', len(sent), f'{time.time()-t00:.1f}s', flush=True)
deleted = gg
rows = []
for k, (x, y, p, co, (vf, vb), cst) in enumerate(sent):
    rec = dict(x=x, y=y, p=p, coords={str(a): str(b) for a, b in co.items()},
               relocation=(x == deleted[1] and y == deleted[2]))
    t0 = time.time()
    try:
        with deadline(120):
            W2 = compile_AB(W1, word_seq_insert(W1, [(p, ['add', x, y, 1, 1, []])]))
            g2 = F.Graph(inline(W2, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
            r2 = F.optimal_frames(inline(W2, True), P.costs, check_literal=False, graph=g2)
            gap = 0
            for part in r2['parts']:
                if part[0] == 'dd': gap += part[2] - part[4]          # primal - exact dual bound of the component
            lower = r2['cost'] - gap
            rec.update(status='ok' if r2['certified'] else 'uncertified', cost=r2['cost'] - c1, lower=float(lower - c1),
                       w1_certified=bool(r['certified']))
    except F.Infeasible: rec['status'] = 'infeasible'
    except Timeout: rec['status'] = 'timeout'
    except Exception as e: rec['status'] = 'err:' + repr(e)[:120]
    rec['seconds'] = round(time.time() - t0, 1); rec['within_budget'] = rec.get('cost') is not None and rec['cost'] <= bud
    rec['provably_over_budget'] = rec['status'] == 'infeasible' or (rec.get('lower') is not None and rec['lower'] > bud)
    rows.append(rec); print(k, rec['x'], rec['y'], rec['p'], rec['status'], rec.get('cost'), rec.get('lower'), 'reloc' if rec['relocation'] else '', flush=True)
summ = dict(word=os.path.basename(word), bindex=bi, depth=depth, ddel=ddel, bud=bud, ncand_U=len(cand), n_sentinel=len(sent),
            status_counts={}, within_budget=sum(1 for r_ in rows if r_['within_budget']), min_cost=min((r_['cost'] for r_ in rows if r_.get('cost') is not None), default=None),
            relocations=sum(1 for r_ in rows if r_['relocation']), provably_over_budget=sum(1 for r_ in rows if r_['provably_over_budget']),
            w1_certified=bool(r['certified']), seconds=round(time.time() - t00, 1), rows=rows)
for r_ in rows: summ['status_counts'][r_['status']] = summ['status_counts'].get(r_['status'], 0) + 1
json.dump(summ, open(out, 'w'), indent=1)
print('summary', json.dumps({k: v for k, v in summ.items() if k != 'rows'}), flush=True)
