"""diag_resid.py WORD DELS_JSON TERMS_JSON: rebuild W2 = base - dels + round-1 terms (x, y, W1pos, lam) and print the residual."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import *
from runjob import exact
from fractions import Fraction as Q
P = H.Pricer(sys.argv[1]); dels = [tuple(d) for d in json.loads(sys.argv[2])]; terms = json.loads(sys.argv[3])
bm = maps(P.base); W1 = compile_AB(P.base, dict(delete=dels))
ins = sorted([(p, k, ['add', x, y, Q(l).numerator, Q(l).denominator, []]) for k, (x, y, p, l) in enumerate(terms)])
W2 = compile_AB(W1, word_seq_insert(W1, [(p, g) for p, _, g in ins]))
cm = maps(W2); TF = diff(bm[0], cm[0]); TB = diff(bm[1], cm[1])
print('residual F rows', {k: {a: str(b) for a, b in v.items()} for k, v in TF.items()})
print('residual B rows', {k: {a: str(b) for a, b in v.items()} for k, v in TB.items()})
seq = fullseq(W1); NA, NC, NB = sec_sizes(W1); print('W1 sections', NA, NC, NB, 'L', len(seq))
for p in sorted({t[2] for t in terms}):
    print('pos', p, 'gate', seq[p] if p < len(seq) else None, 'section', 'A' if p < NA else ('cut' if p < NA + NC else ('B' if p < NA + NC + NB else 'tail')))
