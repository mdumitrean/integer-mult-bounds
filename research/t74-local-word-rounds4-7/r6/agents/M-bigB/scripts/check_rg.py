"""check_rg.py WORD BINDEX SYSDIR RG.json OUT.json (agent M-bigB, r6): take rowgen's first-order proposals (exact on all
projected rows), map them to inserts via candmeta, check full projected exactness (exact_proj: interactions included) and
frame feasibility (cone.feasible), and write the passing ones as a run5-format RUN file (OUT.json) for r5 D's price3.py
(separate process: sk3 loads #1957's vendored harness, absorb.py needs the rev3 one)."""
import json, os, sys
import numpy as np
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); TOOLS = os.path.join(HERE, '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'); sys.path.insert(0, TOOLS)
from sk3 import H, F, compile_AB, maps, word_seq_insert, absorbable, exact_proj, to_base_edit_ab, inline
from cone import feasible
word, bi, sysd, rgp, outp = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5]
cm = np.load(os.path.join(sysd, 'system.npz'))['candmeta'].tolist(); rg = json.load(open(rgp))
P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base); dels = [('B', bi)]
W1 = compile_AB(P.base, dict(delete=dels)); out = []; props = []
for k, pr in enumerate(rg['proposals']):
    ins = []
    for j, l in pr['sol'].items():
        x, y, p, c = cm[int(j)]; lam = Q(int(l), 4)
        ins.append((p, ['add', x, y, lam.numerator, lam.denominator, []]))
    ins.sort(key=lambda t: t[0]); W2 = compile_AB(W1, word_seq_insert(W1, ins))
    rec = dict(k=k, inserts=[(p, g[1], g[2], f'{g[3]}/{g[4]}') for p, g in ins], first_order_est=pr.get('est'))
    rec['exact'] = bool(exact_proj(base_maps, W2, ab))
    if rec['exact']:
        ok, why = feasible(P, W2); rec['frames_ok'] = bool(ok); rec['why'] = None if ok else str(why)[:160]
        if ok:
            props.append(dict(terms=rec['inserts'], est=pr.get('est'), exact=True, edit_ab=to_base_edit_ab(P.base, dels, W1, ins)))
    out.append(rec); print(k, rec.get('exact'), rec.get('frames_ok'), rec.get('why') or '', flush=True)
json.dump(out, open(outp.replace('.json', '-checks.json'), 'w'), indent=1, default=str)
json.dump([dict(dels=dels, proposals=props, source='rowgen ' + os.path.basename(rgp))], open(outp, 'w'), default=str)
print('checked', len(out), 'exact+frames', len(props))
