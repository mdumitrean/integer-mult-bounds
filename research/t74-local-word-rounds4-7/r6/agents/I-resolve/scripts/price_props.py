"""price_props.py WORD BINDEX SYSTEM_DIR ROWGEN.json OUT.json: decode row-generation proposals and price each exactly with
sk2.price_word (exact map check + certified frames vs the base word)."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import lpcert
from fractions import Fraction as Q
import numpy as np
from sk2 import H, compile_AB, maps, cone_caps, price_word, word_seq_insert, fullseq, sec_sizes
from runjob import exact
word, bi, sd, rgp, outp = sys.argv[1:6]; bi = int(bi)
P = H.Pricer(word); base_maps = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
W1 = compile_AB(P.base, dict(delete=[('B', bi)])); cm = np.load(os.path.join(sd, 'system.npz'))['candmeta']
NA, NC, NB = sec_sizes(P.base); gg = fullseq(P.base)[NA + NC + bi]
rows = []
for k, pr in enumerate(json.load(open(rgp))['proposals']):
    terms = sorted((int(cm[int(j)][2]), int(cm[int(j)][0]), int(cm[int(j)][1]), Q(int(l), 4)) for j, l in pr['sol'].items())
    ins = [(p, ['add', x, y, lam.numerator, lam.denominator, []]) for p, x, y, lam in terms]
    W2 = compile_AB(W1, word_seq_insert(W1, ins)); ex = exact(base_maps, W2)
    rec = dict(k=k, terms=[f'{x} += {lam}*{y} @{p}' for p, x, y, lam in terms], exact=ex,
               relocation=all(x == gg[1] and y == gg[2] for p, x, y, lam in terms))
    if ex:
        pr_ = price_word(P, W2, base_comp); rec.update({kk: v for kk, v in pr_.items() if kk not in ('graph', 'assign')})
    rows.append(rec); print(json.dumps(rec, default=str), flush=True)
json.dump(dict(deleted=gg, proposals=rows), open(outp, 'w'), indent=1, default=str)
