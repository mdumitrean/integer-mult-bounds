"""solve_test.py (agent F-cpsat, round r6): pick deliveries inside the screen's windows, solve the exact cancellation,
build the word (multi.build_multi), and test it with exact frames.

Strategies per (q,u): 'leak-earliest' (deliveries into the leak targets, earliest admissible column class), then
'all-earliest' (any windowed target, earliest classes), then 'all-classes' (every column class, earliest time in class).
Every built word: leak after == 0 (exact rationals), compensation must not read q, exact Graph + certified optimal frames.
usage: solve_test.py WORD OUT.jsonl SPEC [--calib]"""
import json, os, sys, time
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
import zcore as Z
import screen as SC
import multi as M
from compat import deadline, Timeout, peak_rss_gib
V = 112
BSTR = "0.001679754956125544"
C1 = 2116454


def solve_combo(cols, target):
    """cols: list of (label, vec dict). Return {label: coef} with sum coef*vec = target, or None (exact elimination)."""
    piv = {}   # pivot -> (row dict, combo dict)
    def reduce(v, combo):
        v = dict(v); combo = dict(combo)
        for p, (row, rc) in piv.items():
            f = v.get(p)
            if f:
                for k, x in row.items():
                    z = v.get(k, Q(0)) - f * x
                    if z: v[k] = z
                    else: v.pop(k, None)
                for k, x in rc.items():
                    z = combo.get(k, Q(0)) - f * x
                    if z: combo[k] = z
                    else: combo.pop(k, None)
        return v, combo
    for lab, vec in cols:
        r, rc = reduce(vec, {lab: Q(1)})
        if r:
            p = min(r); f = r[p]
            r = {k: x / f for k, x in r.items()}; rc = {k: x / f for k, x in rc.items()}
            for pp in list(piv):
                row, rcc = piv[pp]; g = row.get(p)
                if g:
                    for k, x in r.items():
                        z = row.get(k, Q(0)) - g * x
                        if z: row[k] = z
                        else: row.pop(k, None)
                    for k, x in rc.items():
                        z = rcc.get(k, Q(0)) - g * x
                        if z: rcc[k] = z
                        else: rcc.pop(k, None)
            piv[p] = (r, rc)
    # express target: target = sum over pivots target[p] * (row combo) after full reduction
    res, combo = reduce(target, {})
    if res: return None
    return {k: -x for k, x in combo.items() if x}


def classes(cols_j, lo, t_max):
    """cols_j: list of (t_i, key) in decreasing t (from screen.mixing_columns); returns [(t_earliest, t_latest, key)]."""
    out = []
    for n, (t_i, key) in enumerate(cols_j):
        t_next = cols_j[n + 1][0] if n + 1 < len(cols_j) else lo - 1
        out.append((max(lo, t_next + 1), t_i, key))
    return out


def move_limit(W, q, t_max):
    """largest t_last such that every write into q before t_last can be re-timed to t_last (sources not rewritten)."""
    A, C, B = W['A'], W['cut'], W['B']
    pre = [('A', i, e) for i, e in enumerate(A)] + [('cut', i, e) for i, e in enumerate(C)]
    lim = t_max
    for n, (sec, i, e) in enumerate(pre):
        if e[1] != q: continue
        if e[0] != 'add': return -1
        s = e[2]
        if any(e2[1] == s and e2[1] != q for _, _, e2 in pre[n + 1:]): return -1
        rw = [j for j, e2 in enumerate(B) if e2[1] == s]
        if rw: lim = min(lim, rw[0])
    changed = True
    while changed:
        changed = False
        for b, e in enumerate(B[:lim]):
            if e[1] != q: continue
            if e[0] != 'add': lim = b; changed = True; break
            s = e[2]; rw = [j for j in range(b + 1, len(B)) if B[j][1] == s]
            if rw and rw[0] < lim: lim = rw[0]; changed = True; break
    return lim


def attempt(W, q, u, base_cost, costs, strategy, calib=False):
    B = W['B']
    reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]; t_max0 = min(reads) if reads else len(B)
    t_max = move_limit(W, q, t_max0)
    if t_max < 0: return dict(strategy=strategy, status='q writes not movable')
    w0, info = Z.build_at(W, q, [u], 0)
    from model import cone_caps
    caps, comp = cone_caps(w0)
    import copy
    wn = copy.deepcopy(W); wn['start_extra'] = dict(W['start_extra']); wn['start_extra'][str(q)] = [u]
    g = SC.graph(wn, caps); bad = SC.bad_nodes(g, u); win = SC.windows(g, bad, t_max, len(B))
    lo = {y: t for y, t in win.items() if t is not None and t <= t_max}
    cols = SC.mixing_columns(W, lo, t_max)
    L, _ = Z.target_leak(W, q)
    if strategy == 'b0':
        d0 = Z.solve(Z.b_mixing_from(W, 0), L)
        dels = sorted((0, j, d) for j, d in d0.items())
    else:
        cand = []
        for j, cj in cols.items():
            if not cj: continue
            cl = classes(cj, lo[j], t_max)
            if strategy == 'leak-earliest' and j not in L: continue
            use = cl[-1:] if strategy in ('leak-earliest', 'all-earliest') else cl
            for t_e, t_l, key in use:
                cand.append(((j, t_l if strategy == 'all-latest' else t_e), dict(key)))
        sol = solve_combo(cand, {y: -x for y, x in L.items()})
        if sol is None: return dict(strategy=strategy, status='no-solution', candidates=len(cand), t_lim=t_max, windowed=len(lo))
        dels = sorted((t, j, d) for (j, t), d in sol.items())
    w1, msg = M.build_multi(W, q, None if calib else u, dels)
    out = dict(strategy=strategy, deliveries=[[t, j, str(d)] for t, j, d in dels], t_lim=t_max, q_first_read=t_max0)
    if w1 is None: out.update(status='not-buildable:' + msg); return out
    L1, _ = Z.target_leak(w1, q)
    out['leak_after'] = len(L1)
    if L1: out['status'] = 'inexact'; return out
    try:
        with deadline(240):
            res, g1, r = M.price(w1, q, costs)
        out.update(res)
        ref = base_cost if calib else base_cost - C1
        out['delta_vs_narrowed_baseline' if not calib else 'delta_vs_base'] = res['cost'] - ref
        out['status'] = 'ok' if res['certified'] else 'uncertified'
        out['_word'] = w1
    except F.Infeasible as e: out.update(status='infeasible', why=list(map(str, e.args[0][:4])) if e.args else None)
    except Timeout: out.update(status='timeout')
    return out


if __name__ == '__main__':
    WORD, OUT, SPEC = sys.argv[1], sys.argv[2], sys.argv[3]; calib = '--calib' in sys.argv
    W = Z.load(WORD); costs = F.Costs(BSTR)
    from model import cone_caps
    caps, comp = cone_caps(W)
    from word import inline
    gb = F.Graph(inline(W, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    base_cost = F.optimal_frames(inline(W, True), costs, check_literal=False, graph=gb)['cost']
    print('base cost', base_cost, flush=True)
    tasks = [tuple(map(int, p.split(':')[:2])) for p in SPEC.split(',')]
    import multiprocessing as mp, gzip
    os.makedirs(os.path.join(os.path.dirname(OUT), '..', 'words'), exist_ok=True)
    def job(task):
        q, u = task; rows = []
        for strat in (('b0', 'all-earliest', 'all-latest') if calib else ('leak-earliest', 'all-earliest', 'all-classes', 'all-latest')):
            t0 = time.time()
            try: r = attempt(W, q, u, base_cost, costs, strat, calib)
            except Exception as e: r = dict(strategy=strat, status='error:' + repr(e)[:160])
            r.update(q=q, u=u, calib=calib, seconds=round(time.time() - t0, 2))
            wd = r.pop('_word', None)
            if wd is not None and r.get('status') == 'ok':
                p = os.path.join(os.path.dirname(OUT), '..', 'words', 'F-%s-%d-%d-%s.json.gz' % ('calib' if calib else 'narrow', q, u, strat))
                with gzip.open(p, 'wt') as f: json.dump(wd, f)
                r['word_file'] = os.path.relpath(p, os.path.join(HERE, '..', '..', '..', '..'))
            rows.append(r)
            if r.get('status') == 'ok' and not calib: break
        rss = peak_rss_gib()
        if rss is not None and rss > 6: rows[-1]['rss_exit'] = True
        return rows
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, maxtasksperchild=4) as pool:
        for rows in pool.imap_unordered(job, tasks):
            for r in rows:
                f.write(json.dumps(r, sort_keys=True) + '\n'); f.flush()
                print(r['q'], r['u'], r['strategy'], r.get('status'), r.get('delta_vs_narrowed_baseline', r.get('delta_vs_base')), r.get('why', ''), r.get('seconds'), flush=True)
