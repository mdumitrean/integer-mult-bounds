"""screen.py (agent F-cpsat, round r6): exact delivery-window screen for narrowing a width-9 helper q to (8,1,9).

Model.  The leak of q's initial value into the target rows (A+cut+B map) is cancelled by priced deliveries
`y += d*q` inserted in B while q still holds q_init (q's writes are re-timed to after the last delivery, before q's first
read).  A delivery is one frame node shared by y and q, so the start vector u of the narrowed q enters y's chain at the
delivery and propagates forward along every chain-successor link (frames.Graph: lower = join of predecessors).  Upper frames
are meets of successors' uppers (end frames, cone caps), so a delivery before B[t] can be frame-feasible only if every node in
the forward closure of y's successor node accepts u (u in span(upper)).  Closures shrink as t grows, so each target y has a
window [tau_y, t_max] of admissible delivery times (empty if y's own end frame or tail excludes u).  This is a sound necessary
condition: adding nodes can only enlarge closures and tighten uppers.

Exactness.  A delivery of d*q_init into target j before B[t] reaches the final target rows as d * M_t e_j (M_t = target-only
mixing of B[t:]).  The leak L is cancellable within the windows iff -L lies in span{M_t e_j : t in window(j)}.

usage: screen.py WORD OUT.jsonl SPEC   (SPEC = q:u,q:u,...)"""
import copy, gzip, json, os, sys, time
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from word import inline
from model import cone_caps
import zcore as Z
V = 112


def graph(w, caps):
    return F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)


def bad_nodes(g, u):
    n = len(g.nodes); bad = [False] * n
    for k in range(n - 1, -1, -1):
        regs = g.nodes[k][0]
        b = u not in F.span(g.upper[k])
        if not b:
            for r in regs:
                j = g.nxt.get((k, r))
                if j is not None and bad[j]: b = True; break
        bad[k] = b
    return bad


def windows(g, bad, t_max, nB):
    """per target y: earliest B index t (0..t_max) such that the first y-node at or after B[t] is clean; None if none."""
    out = {}
    for y in range(V, 2 * V):
        ch = g.chains[y]; tau = None
        # candidate insertion points t = 0..t_max; successor = first node in chain with (sec=='B' and idx>=t) or sec in tail/end
        succ_list = [(k, g.nodes[k][2], g.nodes[k][3]) for k in ch]
        Bpos = [(idx, k) for k, sec, idx in succ_list if sec == 'B']
        after = [k for k, sec, idx in succ_list if sec in ('tail', 'end')]
        first_after = after[0] if after else None
        # scan t from t_max down: successor changes only at y's B nodes
        # the clean region is a suffix of the chain, so find the first clean successor
        cands = [(idx, k) for idx, k in Bpos if idx <= t_max]
        # successor of insertion before B[t] = first B node with idx >= t, else first_after
        # the smallest t whose successor is clean: walk B nodes in order
        prev_idx = -1
        for idx, k in Bpos:
            if idx > t_max: break
            if not bad[k]:
                tau = prev_idx + 1; break
            prev_idx = idx
        if tau is None:
            # all B nodes up to t_max are bad (or none); successor beyond is the next B node > t_max or tail/end
            nxt_nodes = [k for idx, k in Bpos if idx > prev_idx]
            k2 = nxt_nodes[0] if nxt_nodes else first_after
            if k2 is not None and not bad[k2] and prev_idx + 1 <= t_max: tau = prev_idx + 1
        out[y] = tau
    return out


def mixing_columns(w, t_lo, t_max):
    """for every target j, the distinct columns M_t e_j for t in [t_lo[j], t_max] (t_lo None -> skip)."""
    B = w['B']; n = len(B)
    # reverse sweep: R[j] = column j of M_t as dict y->coef; start at t=n (identity)
    R = {j: {j: Q(1)} for j in range(V, 2 * V)}
    cols = {j: [] for j in range(V, 2 * V)}
    def record(t):
        for j in range(V, 2 * V):
            lo = t_lo.get(j)
            if lo is None or t < lo or t > t_max: continue
            c = R[j]; key = tuple(sorted(c.items()))
            if not cols[j] or cols[j][-1][1] != key: cols[j].append((t, key))
    for t in range(n, -1, -1):
        if t < n:
            e = B[t]; tt = e[1]
            if V <= tt < 2 * V:
                c = Z.coef(e)
                if e[0] == 'add':
                    s = e[2]
                    if V <= s < 2 * V:
                        # M_t = M_{t+1} G_t ; G_t = I + c E_{tt,s}: column s += c * column tt
                        new = dict(R[s])
                        for y, x in R[tt].items():
                            v = new.get(y, Q(0)) + c * x
                            if v: new[y] = v
                            else: new.pop(y, None)
                        R[s] = new
                else:
                    R[tt] = {y: c * x for y, x in R[tt].items()}
        record(t)
    return cols


def in_span(vectors, target):
    """exact: is target in span(vectors)? vectors: list of dict y->Q. returns (bool, rank)."""
    piv = {}
    def reduce(v):
        v = dict(v)
        for p, row in piv.items():
            if p in v and v[p]:
                f = v[p]
                for k, x in row.items():
                    z = v.get(k, Q(0)) - f * x
                    if z: v[k] = z
                    else: v.pop(k, None)
        return v
    for vec in vectors:
        r = reduce(vec)
        if r:
            p = min(r); f = r[p]; r = {k: x / f for k, x in r.items()}
            for pp, row in piv.items():
                if p in row and row[p]:
                    g = row[p]
                    for k, x in r.items():
                        z = row.get(k, Q(0)) - g * x
                        if z: row[k] = z
                        else: row.pop(k, None)
            piv[p] = r
    return (not reduce(target)), len(piv)


def run(W, q, u):
    t0 = time.time(); out = dict(q=q, u=u)
    B = W['B']
    reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]
    t_max = min(reads) if reads else len(B)
    out['q_first_read_B'] = t_max
    if any(e[0] == 'add' and e[2] == q for e in W['A'] + W['cut']):
        out['status'] = 'q read in A/cut'; return out
    w0, info = Z.build_at(W, q, [u], 0)
    if w0 is None: out.update(status='construction-t0:' + info.get('status', '?')); return out
    caps, comp = cone_caps(w0)
    out['comp_gates'] = len(comp); out['comp_reads_q'] = sum(1 for e in comp if e[2] == q)
    wn = copy.deepcopy(W); wn['start_extra'] = dict(W['start_extra']); wn['start_extra'][str(q)] = [u]
    try:
        g = graph(wn, caps)
    except F.Infeasible as e:
        out.update(status='narrowed-word-infeasible', why=list(map(str, e.args[0][:4]))); return out
    bad = bad_nodes(g, u)
    win = windows(g, bad, t_max, len(B))
    L, _ = Z.target_leak(W, q)
    out['leak'] = {str(k): str(v) for k, v in L.items()}
    end_ok = {y: (u in F.span(g.nodes[g.chains[y][-1]][1])) for y in range(V, 2 * V)}
    out['targets_end_accept_u'] = sum(end_ok.values())
    out['targets_with_window'] = sum(1 for y, t in win.items() if t is not None)
    out['windows'] = {str(y): t for y, t in win.items() if t is not None}
    cols = mixing_columns(W, {y: t for y, t in win.items() if t is not None}, t_max)
    vecs = [dict(c[1]) for j in cols for c in cols[j]]
    out['candidate_columns'] = len(vecs)
    ok, rank = in_span(vecs, {y: -x for y, x in L.items()})
    out['span_rank'] = rank; out['leak_cancellable'] = ok
    out['status'] = 'cancellable-within-windows' if ok else 'blocked'
    out['seconds'] = round(time.time() - t0, 2)
    return out


if __name__ == '__main__':
    WORD, OUT, SPEC = sys.argv[1], sys.argv[2], sys.argv[3]
    W = Z.load(WORD)
    tasks = [tuple(map(int, p.split(':')[:2])) for p in SPEC.split(',')]
    import multiprocessing as mp
    from compat import deadline, Timeout, peak_rss_gib
    def job(task):
        q, u = task
        try:
            with deadline(600):
                r = run(W, q, u)
        except Timeout: r = dict(q=q, u=u, status='timeout')
        except Exception as e: r = dict(q=q, u=u, status='error:' + repr(e)[:120])
        rss = peak_rss_gib()
        if rss is not None and rss > 6: r['rss_exit'] = True
        return r
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, maxtasksperchild=4) as pool:
        for r in pool.imap_unordered(job, tasks):
            f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
            print(r['q'], r['u'], r.get('status'), r.get('targets_with_window'), r.get('leak_cancellable'), r.get('seconds'), flush=True)
