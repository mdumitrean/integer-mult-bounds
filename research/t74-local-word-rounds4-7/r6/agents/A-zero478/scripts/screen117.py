"""screen117.py: for every frame-feasible (8,1,9) narrowing (q, u) of r5 C's NARROW-base.jsonl, test whether q's target
leak can be cancelled by free (or frame-compatible) copies taken while q is pure.
Holders: any register except targets, cold ends (helper_final) and q.  A holder c is compatible at copy time t (<= q's first
write) if c's frame at t is () or [u] and c's next frame contains u; it is free if that next frame is [u] or c is already at
[u] (the copy then takes over or repeats c's first rank-1 jump).  P_c(t) = target-row transfer of a unit placed in c at t.
Pass = -L_q in span{P_c} (exact rational elimination; free holders first).  3 workers, per-task alarm, RSS check.
usage: screen117.py WORD NARROW-base.jsonl OUT.json"""
import json, sys, os, signal, resource, multiprocessing as mp
from fractions import Fraction as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import traj as TJ
WORD, NARROW, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
w = TJ.load(WORD); v = w['report']['v']; R = w['report']['R']; n = 2 * v + R
low = set(map(int, w['helper_final']))
ent = {int(k): list(U) for k, U in w['start_extra'].items()}
main = [('A', i, g) for i, g in enumerate(w['A'])] + [('cut', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
coef = lambda g: F(g[3], g[4]) if g[0] == 'add' else F(g[2], g[3])
def span(fr):
    s = {0}
    for b in fr: s |= {x ^ b for x in s}
    return s
# per-register vertex list in main: (k, frame) for A/B gates (cut has no frames)
vert = {}
for k, (s, i, g) in enumerate(main):
    if s == 'cut': continue
    for r in TJ.regs(g): vert.setdefault(r, []).append((k, g[-1]))
startf = {r: ([] if r >= 2 * v else None) for r in range(n)}
for r in range(v): startf[r] = [w['ports'][r]]
for r, U in ent.items(): startf[r] = U
def transfer(c, start):
    col = {c: F(1)}
    for k in range(start, len(main)):
        s, i, g = main[k]
        if g[0] == 'add':
            t, src = g[1], g[2]; x = col.get(src)
            if x:
                a = col.get(t, F(0)) + coef(g) * x
                if a: col[t] = a
                else: col.pop(t)
        elif g[1] in col: col[g[1]] = col[g[1]] * coef(g)
    return {y: a for y, a in col.items() if v <= y < 2 * v}
def holder_times(c, t0, u):
    """all distinct copy positions t <= t0 with frame(c) subset [u] at t and every later frame containing u; (t, free) list"""
    f = startf[c] or []
    if f and not (len(f) == 1 and f[0] == u): return []
    vs = vert.get(c, []); opts = [0] if 0 <= t0 else []; cur = f
    first_big = None
    for k, fr in vs:
        if k >= t0: break
        if len(fr) > 1 or (fr and fr[0] != u): first_big = (k, fr); break
        opts.append(k + 1)
    if first_big is None:
        nxt = next((fr for k, fr in vs if k >= t0), None)
        if nxt is None or u not in span(nxt): return []
        limit = t0; nf = nxt
    else:
        if u not in span(first_big[1]): return []
        limit = first_big[0]; nf = first_big[1]
    opts = sorted({t for t in opts if t <= limit})
    out = []
    for t in opts:
        fr_t = [fr for k, fr in vs if k < t]; cur = fr_t[-1] if fr_t else f
        out.append((t, cur == [u] or len(nf) == 1))
    return out
def solve(cols, target):
    """exact elimination: find k with sum k_c cols[c] = target; cols ordered by preference; returns dict or None"""
    rows = sorted({y for c in cols for y in cols[c]} | set(target))
    names = list(cols); A = [[cols[c].get(y, F(0)) for c in names] + [target.get(y, F(0))] for y in rows]
    piv = []; r = 0
    for j in range(len(names)):
        p = next((i for i in range(r, len(A)) if A[i][j] != 0), None)
        if p is None: continue
        A[r], A[p] = A[p], A[r]; inv = 1 / A[r][j]; A[r] = [x * inv for x in A[r]]
        for i in range(len(A)):
            if i != r and A[i][j] != 0:
                f = A[i][j]; A[i] = [a - f * b for a, b in zip(A[i], A[r])]
        piv.append(j); r += 1
        if r == len(A): break
    if any(all(x == 0 for x in A[i][:-1]) and A[i][-1] != 0 for i in range(len(A))): return None
    return {names[j]: A[i][-1] for i, j in enumerate(piv) if A[i][-1] != 0}
def task(qu):
    q, u = qu
    signal.alarm(600)
    t0 = next(k for k, (s, i, g) in enumerate(main) if g[1] == q)
    Lq = transfer(q, 0)
    if not Lq: return dict(q=q, u=u, status='no-leak')
    hold = {}
    for c in range(n):
        if c == q or v <= c < 2 * v or c in low: continue
        seenP = []
        for t, fr in holder_times(c, t0, u):
            P = transfer(c, t)
            if P and P not in seenP: seenP.append(P); hold[f'{c}@{t}'] = (t, fr, P)
    tgt = {y: -a for y, a in Lq.items()}
    free = {c: h[2] for c, h in hold.items() if h[1]}
    comp = dict(free); comp.update({c: h[2] for c, h in hold.items() if not h[1]})
    sf = solve(free, tgt); sc = sf if sf is not None else solve(comp, tgt)
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3
    signal.alarm(0)
    enc = lambda s: None if s is None else {c: [str(k), hold[c][0], hold[c][1]] for c, k in s.items()}
    return dict(q=q, u=u, t0=t0, leak_targets=len(Lq), holders_compatible=len(hold), holders_free=len(free),
                pass_free=sf is not None, pass_compatible=sc is not None, solution_free=enc(sf), solution_compatible=enc(sc),
                holders=sorted(hold), rss_gib=round(rss, 2))
if __name__ == '__main__':
    seen = set(); tasks = []
    for l in open(NARROW):
        r = json.loads(l)
        if r['status'] == 'ok' and r['width'] == 9 and len(r['basis']) == 1:
            key = (r['q'], r['basis'][0])
            if key not in seen: seen.add(key); tasks.append(key)
    out = dict(word=os.path.basename(WORD), tasks=len(tasks), helpers=len({q for q, u in tasks}), results=[])
    def save():
        tmp = OUT + '.tmp'; json.dump(out, open(tmp, 'w'), indent=0); os.replace(tmp, OUT)
    def on_alarm(sig, frm): raise TimeoutError()
    with mp.get_context('fork').Pool(3, initializer=lambda: signal.signal(signal.SIGALRM, on_alarm), maxtasksperchild=20) as pool:
        for n_done, res in enumerate(pool.imap_unordered(task, tasks), 1):
            out['results'].append(res)
            out['passed_free'] = sorted({r['q'] for r in out['results'] if r.get('pass_free')})
            out['passed_compatible'] = sorted({r['q'] for r in out['results'] if r.get('pass_compatible')})
            save()
            if n_done % 20 == 0: print(n_done, '/', len(tasks), 'passed_free', out['passed_free'], 'passed_compatible', out['passed_compatible'], flush=True)
    out['complete'] = True; save()
    print('done', len(tasks), 'helpers', out['helpers'], 'passed_free', out['passed_free'], 'passed_compatible', out['passed_compatible'], flush=True)
