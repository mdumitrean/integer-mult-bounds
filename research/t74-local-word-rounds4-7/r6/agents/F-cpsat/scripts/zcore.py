"""zcore: exact construction of "in-B compensation" words for one width-9 helper q (agent B-zero502, round r6).

Idea (re-timing route): the derived compensation cancels q's initial-value leak with frame-0 gates `y -= a*q` run before A,
while q still holds q_init.  If every A-write into q is re-timed to after the cut (legal when q is not read in between and
each source is not rewritten in between), q still holds q_init at the start of B, so the same cancellation can be done by
priced B gates `y += d_y*q` at B-start, with d solving M d = -L (M = B's target-only mixing, L = q's raw target leak).  The
A+cut+B map then has a zero q column on target rows, the re-derived compensation no longer reads q, and q can be narrowed
to an entering (8,1,9) helper.  Only target rows change (targets are read only by targets), so helpers/data are untouched.
"""
import copy, gzip, json
from fractions import Fraction as Q
V = 112
def regs(e): return e[1:3] if e[0] == 'add' else e[1:2]
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
def load(p): return json.load(gzip.open(p))
def target_leak(w, q):
    col = {q: Q(1)}
    for e in w['A'] + w['cut'] + w['B']:
        t = e[1]; c = coef(e)
        if e[0] == 'add':
            x = col.get(e[2])
            if x:
                y = col.get(t, Q(0)) + c * x
                if y: col[t] = y
                else: col.pop(t, None)
        elif t in col: col[t] = col[t] * c
    return {y: a for y, a in col.items() if V <= y < 2 * V}, col
def b_mixing(w):
    """comp[y] = final coefficients (over B-start injection labels) of target y after B; only target-target gates matter."""
    comp = {y: {y: Q(1)} for y in range(V, 2 * V)}
    for e in w['B']:
        t = e[1]
        if not (V <= t < 2 * V): continue
        c = coef(e)
        if e[0] == 'add':
            s = e[2]
            if V <= s < 2 * V:
                d = comp[t]
                for k, x in comp[s].items():
                    y = d.get(k, Q(0)) + c * x
                    if y: d[k] = y
                    else: d.pop(k, None)
        else: comp[t] = {k: c * x for k, x in comp[t].items()}
    return comp
def solve(comp, L):
    """find d (dict label->Q) with sum_j comp[y][j] d_j = -L_y for every target y (exact Gaussian elimination)."""
    ys = list(range(V, 2 * V)); rows = []
    for y in ys:
        r = dict(comp[y]); r['rhs'] = -L.get(y, Q(0)); rows.append(r)
    piv = {}; order = []
    for r in rows:
        for j, (pr) in list(piv.items()):
            if j in r and r[j]:
                f = r[j]
                for k, x in pr.items():
                    v = r.get(k, Q(0)) - f * x
                    if v: r[k] = v
                    else: r.pop(k, None)
        cols = [k for k in r if k != 'rhs' and r[k]]
        if not cols:
            if r.get('rhs', 0): raise ValueError('inconsistent')
            continue
        j = min(cols); f = r[j]; r = {k: x / f for k, x in r.items()}
        for jj, pr in piv.items():
            if j in pr and pr[j]:
                g = pr[j]
                for k, x in r.items():
                    v = pr.get(k, Q(0)) - g * x
                    if v: pr[k] = v
                    else: pr.pop(k, None)
        piv[j] = r
    return {j: pr.get('rhs', Q(0)) for j, pr in piv.items() if pr.get('rhs', Q(0))}
def movable_A_writes(w, q):
    """A-writes into q, each with a check that it can be re-timed to B-start."""
    A = w['A']; writes = [i for i, e in enumerate(A) if e[1] == q]; bad = []
    tail_after = lambda i: A[i + 1:] + w['cut']
    for i in writes:
        e = A[i]
        if e[0] != 'add': bad.append((i, 'scale')); continue
        s = e[2]
        for e2 in tail_after(i):
            if e2[0] == 'add' and e2[2] == q: bad.append((i, 'q read later in A/cut')); break
            if e2[1] == s and not (e2 in [A[j] for j in writes]): bad.append((i, 'source rewritten', e2[:5])); break
    return writes, bad
def build(w, q, u, move=True, place='start'):
    """return the edited word (frames of new gates = []), plus info.  place='start': deliveries at B index 0."""
    w1 = copy.deepcopy(w)
    writes, bad = movable_A_writes(w, q)
    if bad: return None, dict(status='not-movable', bad=bad)
    moved = [w['A'][i] for i in writes]
    w1['A'] = [e for i, e in enumerate(w['A']) if i not in set(writes)]
    L, _ = target_leak(w, q)
    comp = b_mixing(w)
    d = solve(comp, L)
    dels = [['add', y, q, x.numerator, x.denominator, []] for y, x in sorted(d.items())]
    w1['B'] = dels + [list(e[:-1]) + [[]] for e in moved] + w['B']
    w1['start_extra'] = dict(w['start_extra']); w1['start_extra'][str(q)] = list(u)
    L1, _ = target_leak(w1, q)
    return w1, dict(status='built', moved_A=writes, deliveries=[e[:5] for e in dels], leak_before={str(k): str(v) for k, v in L.items()},
                    leak_after={str(k): str(v) for k, v in L1.items()})
def b_mixing_from(w, t):
    """target-only mixing of B from index t (deliveries placed before original B[t])."""
    comp = {y: {y: Q(1)} for y in range(V, 2 * V)}
    for e in w['B'][t:]:
        tt = e[1]
        if not (V <= tt < 2 * V): continue
        c = coef(e)
        if e[0] == 'add':
            s = e[2]
            if V <= s < 2 * V:
                d = comp[tt]
                for k, x in comp[s].items():
                    y = d.get(k, Q(0)) + c * x
                    if y: d[k] = y
                    else: d.pop(k, None)
        else: comp[tt] = {k: c * x for k, x in comp[tt].items()}
    return comp
def build_at(w, q, u, t):
    """in-B compensation with deliveries placed before original B[t]; q's A-writes and any B-writes before t are moved to
    just after the deliveries (requires: q not read before t, each moved write's source not rewritten before its new slot)."""
    A, Bs = w['A'], w['B']
    if any(e[0] == 'add' and e[2] == q for e in A + w['cut'] + Bs[:t]): return None, dict(status='q read before t')
    wa = [i for i, e in enumerate(A) if e[1] == q]; wb = [i for i, e in enumerate(Bs[:t]) if e[1] == q]
    seq = [('A', i) for i in range(len(A))] + [('cut', i) for i in range(len(w['cut']))] + [('B', i) for i in range(t)]
    pos = {k: n for n, k in enumerate(seq)}
    def get(sec, i): return w[sec][i]
    moved = [('A', i) for i in wa] + [('B', i) for i in wb]
    for sec, i in moved:
        e = get(sec, i)
        if e[0] != 'add': return None, dict(status='scale write')
        s = e[2]
        for sec2, j in seq[pos[(sec, i)] + 1:]:
            e2 = get(sec2, j)
            if e2[1] == s and (sec2, j) not in moved: return None, dict(status='source rewritten', at=[sec2, j])
    L, _ = target_leak(w, q)
    d = solve(b_mixing_from(w, t), L)
    dels = [['add', y, q, x.numerator, x.denominator, []] for y, x in sorted(d.items())]
    w1 = copy.deepcopy(w)
    w1['A'] = [e for i, e in enumerate(A) if i not in set(wa)]
    keepB = [e for i, e in enumerate(Bs[:t]) if i not in set(wb)]
    w1['B'] = keepB + dels + [list(get(s, i)[:-1]) + [[]] for s, i in moved] + Bs[t:]
    w1['start_extra'] = dict(w['start_extra']); w1['start_extra'][str(q)] = list(u)
    L1, _ = target_leak(w1, q)
    return w1, dict(status='built', t=t, moved=[[s, i] for s, i in moved], deliveries=[e[:5] for e in dels], leak_after=len(L1))
