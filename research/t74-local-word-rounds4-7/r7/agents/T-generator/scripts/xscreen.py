"""xscreen.py: frame-free dirt-routing exchange screen (gauge44 change-A style) on a T74 local word.
An exchange swaps two non-target registers a, b that hold the SAME clean value (sources X and targets Y columns) and
have the SAME frame span at time t (4 gates at that frame: no climb). It changes only where helper dirt flows.
Effect on the A+cut+B target dirt response: dR = -u_T (x) delta, u_T = Tadj[a]-Tadj[b] (target rows), delta = val[a]-val[b].
Constraints kept: entering and ended (helper_final) helpers' columns of delta are 0 (their responses / identities unchanged),
and the exchange must not change any ended helper's final row (u_K = 0, adjoint over A+cut+B+tail).
For each narrowable full-c1 helper q (r5 C NARROW-base.jsonl), report exchanges with u_T * delta_q == L_q (zeroes q's leak).
usage: xscreen.py WORD NARROW.jsonl TOOLKIT OUT.json"""
import json, gzip, sys, collections
from fractions import Fraction as Fr
word_p, narrow_p, tk, out_p = sys.argv[1:5]
sys.path.insert(0, tk)
import frames as F
W = json.load(gzip.open(word_p)); V = 112; R = W['report']['R']; n = 2 * V + R
E = set(map(int, W.get('start_extra', {}))); K = set(map(int, W.get('helper_final', {})))
rows = [json.loads(l) for l in open(narrow_p) if l.strip()]
Q = sorted({r['q'] for r in rows if r.get('status') == 'ok' and r.get('delta') == -2116454})
Qs = set(Q)
def coef(e): return Fr(e[3], e[4]) if e[0] == 'add' else Fr(e[2], e[3])
main = [('A', i, g) for i, g in enumerate(W['A'])] + [('cut', i, g) for i, g in enumerate(W['cut'])] + [('B', i, g) for i, g in enumerate(W['B'])]
tail = [('T', j, W['cleanup'][ci]) for j, (ci, U) in enumerate(W['early_cleanup'])]
start = [[p] for p in W['ports']] + [[] for _ in range(V + R)]
for q, U in W.get('start_extra', {}).items(): start[int(q)] = list(U)
frame = [F.span(tuple(s)) for s in start]
val = [{x: Fr(1)} for x in range(n)]
targets = set(range(V, 2 * V))
def clean_key(x): return tuple(sorted((k, v) for k, v in val[x].items() if k < 2 * V))
groups = collections.defaultdict(set); key = [None] * n
for x in range(n):
    if x in targets: continue
    key[x] = (clean_key(x), frame[x]); groups[key[x]].add(x)
cands = []   # (t_after_index, a, b, delta_on_Q, flags)
def delta(a, b):
    d = {}
    for k in set(val[a]) | set(val[b]):
        if k < 2 * V: continue
        x = val[a].get(k, 0) - val[b].get(k, 0)
        if x: d[k] = x
    return d
def consider(t, a, b):
    d = delta(a, b)
    if not d: return
    if any(k in E or k in K for k in d): return
    dq = {k: v for k, v in d.items() if k in Qs}
    if not dq: return
    cands.append((t, a, b, dq))
reads_since = collections.defaultdict(int)
for t, (sec, i, g) in enumerate(main):
    x = g[1]
    if g[0] == 'add':
        s = g[2]; c = coef(g); dst = val[x]
        for k, v in val[s].items():
            y = dst.get(k, 0) + c * v
            if y: dst[k] = y
            else: dst.pop(k, None)
    else:
        c = coef(g); val[x] = {k: c * v for k, v in val[x].items()}
    if g[-1] is not None: frame[x] = F.span(tuple(g[-1]))
    if x in targets: continue
    groups[key[x]].discard(x); key[x] = (clean_key(x), frame[x]); groups[key[x]].add(x)
    for b in groups[key[x]]:
        if b != x and b not in targets: consider(t, x, b)
    if g[0] == 'add' and g[2] not in targets:   # a read of s changes its adjoint: re-offer s's pairs (capped)
        s = g[2]
        if reads_since[s] < 6:
            reads_since[s] += 1
            for b in list(groups[key[s]])[:40]:
                if b != s and b not in targets: consider(t, s, b)
Lq = {q: {y: val[y].get(q, 0) for y in range(V, 2 * V) if val[y].get(q, 0)} for q in Q}
print('word', word_p.split('/')[-1], 'Q', len(Q), 'candidates', len(cands), flush=True)
# backward adjoints: target rows over A+cut+B; ended rows over A+cut+B+tail
need = collections.defaultdict(set)
for (t, a, b, dq) in cands: need[t].update((a, b))
def adjoint(seq, rowset, keep_times):
    Tc = [dict() for _ in range(n)]
    for r in rowset: Tc[r] = {r: Fr(1)}
    snap = {}
    for t in range(len(seq) - 1, -1, -1):
        if t in keep_times: snap[t] = {r: dict(Tc[r]) for r in keep_times[t]}
        g = seq[t][2]; x = g[1]
        if g[0] == 'add':
            s = g[2]; c = coef(g)
            if Tc[x]:
                dst = Tc[s]
                for k, v in Tc[x].items():
                    y = dst.get(k, 0) + c * v
                    if y: dst[k] = y
                    else: dst.pop(k, None)
        else:
            c = coef(g); Tc[x] = {k: c * v for k, v in Tc[x].items()}
    return snap
# snapshot "after gate t" = state before gate t+1 during the backward sweep: record at index t+1
keepT = collections.defaultdict(set)
for t, regs in need.items(): keepT[t + 1].update(regs)
snapT = adjoint(main, targets, keepT)
full = main + tail
snapK = adjoint(full, K, keepT)
def diff(d1, d2):
    out = {}
    for k in set(d1) | set(d2):
        x = d1.get(k, 0) - d2.get(k, 0)
        if x: out[k] = x
    return out
endT = {r: ({r: Fr(1)} if r in targets else {}) for r in range(n)}
endK = {r: ({r: Fr(1)} if r in K else {}) for r in range(n)}
hits, stats = [], collections.Counter()
span_vecs = collections.defaultdict(list)
for (t, a, b, dq) in cands:
    sT = snapT.get(t + 1, endT); sK = snapK.get(t + 1, endK)
    uT = diff(sT.get(a, {}), sT.get(b, {})); uK = diff(sK.get(a, {}), sK.get(b, {}))
    if uK: stats['ended-row-change'] += 1; continue
    if not uT: stats['no-target-effect'] += 1; continue
    stats['admissible'] += 1
    for q, c in dq.items():
        span_vecs[q].append({y: c * v for y, v in uT.items()})
        L = Lq[q]
        if not L: continue
        # need c*uT == L exactly
        if set(uT) == set(L) and all(c * uT[y] == L[y] for y in L):
            hits.append(dict(t=t, at=list(main[t][:2]), a=a, b=b, q=q, coef=str(c), leak_rows=len(L)))
            stats['zeroes-a-leak'] += 1
def in_span(vecs, L):
    # exact rational elimination: is L in span(vecs)? also return rank
    piv = {}   # pivot row -> reduced vector
    def reduce(v):
        v = dict(v)
        changed = True
        while v:
            k = min(v)
            if k in piv:
                pv = piv[k]; f = v[k] / pv[k]
                for kk, xx in pv.items():
                    y = v.get(kk, 0) - f * xx
                    if y: v[kk] = y
                    else: v.pop(kk, None)
            else:
                return v
        return v
    for v in vecs:
        r = reduce(v)
        if r: piv[min(r)] = r
    rest = reduce(L)
    return (not rest), len(piv)
span_res = {}
for q in Q:
    L = Lq[q]
    if not L: continue
    ok, rank = in_span(span_vecs.get(q, []), L)
    span_res[q] = dict(in_span=ok, rank=rank, vectors=len(span_vecs.get(q, [])), leak_rows=len(L))
res_span = dict(helpers=len(span_res), in_span=sorted(q for q, r in span_res.items() if r['in_span']), max_rank=max((r['rank'] for r in span_res.values()), default=0))
print('SPAN', json.dumps(res_span), flush=True)
res = dict(span=span_res, span_summary=res_span, word=word_p.split('/')[-1], Q=len(Q), candidates=len(cands), stats=dict(stats), hits=hits[:200], nhits=len(hits))
json.dump(res, open(out_p, 'w'), indent=1); print(json.dumps({k: v for k, v in res.items() if k != 'hits'}), flush=True)
for h in hits[:10]: print('HIT', h)
