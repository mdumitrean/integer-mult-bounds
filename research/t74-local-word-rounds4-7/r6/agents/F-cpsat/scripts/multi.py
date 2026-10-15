"""multi.py (agent F-cpsat, round r6): exact in-B cancellation with deliveries at different B times per target.

build_multi(W, q, u, dels): dels = [(t, y, d)] with d a Fraction; delivery `y += d*q` is inserted before original B[t].
All writes into q before the last delivery (A-writes and B-writes) are re-timed to just after the last delivery; legal only
if q is not read before then and no moved write's source is rewritten between its old and new positions.  u=None keeps
q (9,0,9) (calibration); otherwise q's start frame becomes span(u)."""
import copy, os, sys
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
import zcore as Z
V = 112


def build_multi(W, q, u, dels):
    A, C, B = W['A'], W['cut'], W['B']
    t_last = max(t for t, y, d in dels)
    if any(e[0] == 'add' and e[2] == q for e in A + C + B[:t_last]): return None, 'q read before last delivery'
    seq = [('A', i) for i in range(len(A))] + [('cut', i) for i in range(len(C))] + [('B', i) for i in range(t_last)]
    pos = {k: n for n, k in enumerate(seq)}
    moved = [('A', i) for i, e in enumerate(A) if e[1] == q] + [('B', i) for i, e in enumerate(B[:t_last]) if e[1] == q]
    mset = set(moved)
    for sec, i in moved:
        e = W[sec][i]
        if e[0] != 'add': return None, 'scale write into q'
        s = e[2]
        for sec2, j in seq[pos[(sec, i)] + 1:]:
            e2 = W[sec2][j]
            if e2[1] == s and (sec2, j) not in mset: return None, 'source %d rewritten at %s%d' % (s, sec2, j)
    by_t = {}
    for t, y, d in dels: by_t.setdefault(t, []).append(['add', y, q, d.numerator, d.denominator, []])
    newB = []
    for i in range(len(B) + 1):
        newB += by_t.get(i, [])
        if i == t_last: newB += [list(W[sec][j][:-1]) + [[]] for sec, j in moved]
        if i < len(B) and ('B', i) not in mset: newB.append(B[i])
    w1 = copy.deepcopy(W)
    w1['A'] = [e for i, e in enumerate(A) if ('A', i) not in mset]
    w1['B'] = newB
    if u is not None:
        w1['start_extra'] = dict(W['start_extra']); w1['start_extra'][str(q)] = [u]
    return w1, 'built'


def price(w1, q, costs):
    caps, comp = cone_caps(w1)
    reads_q = sum(1 for e in comp if e[2] == q)
    g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w1, True), costs, check_literal=False, graph=g)
    return dict(cost=r['cost'], certified=r['certified'], profile=dict(sorted(r['profile'].items())), comp_gates=len(comp), comp_reads_q=reads_q), g, r
