"""explore.py (agent F-cpsat, round r6): randomized exploration of the exact cancellation solution space inside the
screen's windows, each candidate tested with exact frames (frames.Graph L/U propagation, then pricing if feasible).

Candidates: every (target j, column class, time in {earliest, latest} of the class) inside [tau_j, t_lim].  A trial orders
the candidates (by dim of the target's lower frame just before the delivery, with random noise, or uniformly), solves the
exact system greedily in that order (a different particular solution per order), builds the word with multi.build_multi and
runs the exact frame test.  usage: explore.py WORD OUT.jsonl q:u[,...] TRIALS SEED"""
import copy, json, os, random, sys, time
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'toolkit')); sys.path.insert(0, HERE)
import frames as F
from model import cone_caps
import zcore as Z, screen as SC, multi as M, solve_test as ST
from compat import deadline, Timeout, peak_rss_gib
V = 112


def lower_before(g, j, t):
    """lower frame of target j's last node strictly before insertion point B[t] (start/cut/B nodes)."""
    best = None
    for k in g.chains[j]:
        regs, F0, sec, idx = g.nodes[k]
        if sec in ('start', 'cut') or (sec == 'B' and idx < t): best = k
        else: break
    return g.lower[best] if best is not None else ()


def setup(W, q, u):
    B = W['B']
    reads = [i for i, e in enumerate(B) if e[0] == 'add' and e[2] == q]; t0 = min(reads) if reads else len(B)
    t_lim = ST.move_limit(W, q, t0)
    w0, _ = Z.build_at(W, q, [u], 0); caps, comp = cone_caps(w0)
    wn = copy.deepcopy(W); wn['start_extra'] = dict(W['start_extra']); wn['start_extra'][str(q)] = [u]
    g = SC.graph(wn, caps); bad = SC.bad_nodes(g, u); win = SC.windows(g, bad, t_lim, len(B))
    lo = {y: t for y, t in win.items() if t is not None and t <= t_lim}
    cols = SC.mixing_columns(W, lo, t_lim)
    L, _ = Z.target_leak(W, q)
    cand = []
    for j, cj in cols.items():
        if not cj: continue
        for t_e, t_l, key in ST.classes(cj, lo[j], t_lim):
            for t in sorted({t_e, t_l}):
                dimL = len(F.basis(tuple(lower_before(g, j, t)) + (u,)))
                cand.append(((j, t), dict(key), dimL))
    return dict(L=L, cand=cand, t_lim=t_lim, g=g)


def trial(W, q, u, S, costs, base_cost, rng, mode):
    cand = list(S['cand'])
    if mode == 'dim': cand.sort(key=lambda c: (c[2] + rng.random() * 2, rng.random()))
    else: rng.shuffle(cand)
    sol = ST.solve_combo([(lab, vec) for lab, vec, d in cand], {y: -x for y, x in S['L'].items()})
    if sol is None: return dict(status='no-solution')
    dels = sorted((t, j, d) for (j, t), d in sol.items())
    key = tuple((t, j, str(d)) for t, j, d in dels)
    w1, msg = M.build_multi(W, q, u, dels)
    if w1 is None: return dict(status='not-buildable:' + msg, key=key)
    L1, _ = Z.target_leak(w1, q)
    if L1: return dict(status='inexact', key=key)
    try:
        with deadline(120):
            caps, comp = cone_caps(w1)
            from word import inline
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    except F.Infeasible as e: return dict(status='infeasible', why=list(map(str, e.args[0][:4])), key=key, ndel=len(dels))
    except Timeout: return dict(status='timeout', key=key)
    res, g1, r = M.price(w1, q, costs)
    return dict(status='ok' if res['certified'] else 'uncertified', key=key, ndel=len(dels), **res,
                extra_vs_narrowed=res['cost'] - (base_cost - ST.C1), _word=w1)


if __name__ == '__main__':
    WORD, OUT, SPEC, TRIALS, SEED = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    W = Z.load(WORD); costs = F.Costs(ST.BSTR)
    from word import inline
    caps, comp = cone_caps(W)
    gb = F.Graph(inline(W, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    base_cost = F.optimal_frames(inline(W, True), costs, check_literal=False, graph=gb)['cost']
    tasks = [tuple(map(int, p.split(':')[:2])) for p in SPEC.split(',')]
    import multiprocessing as mp, gzip, collections
    def job(task):
        q, u = task; rng = random.Random(SEED * 1000003 + q); t0 = time.time()
        S = setup(W, q, u); seen = set(); stats = collections.Counter(); why = collections.Counter(); best = None; found = None
        for n in range(TRIALS):
            r = trial(W, q, u, S, costs, base_cost, rng, 'dim' if n % 2 == 0 else 'uniform')
            k = r.get('key')
            if k is not None and k in seen: stats['duplicate'] += 1; continue
            if k is not None: seen.add(k)
            stats[r['status'].split(':')[0]] += 1
            if r['status'] == 'infeasible': why[(r['why'][2], r['why'][3])] += 1
            if r['status'] == 'ok':
                wd = r.pop('_word')
                p = os.path.join(os.path.dirname(OUT), '..', 'words', 'F-narrow-%d-%d-trial%d.json.gz' % (q, u, n))
                with gzip.open(p, 'wt') as f: json.dump(wd, f)
                r['word_file'] = p; found = r; break
            if time.time() - t0 > 900: stats['time_cap'] += 1; break
        rss = peak_rss_gib()
        return dict(q=q, u=u, t_lim=S['t_lim'], candidates=len(S['cand']), trials=sum(stats.values()), distinct=len(seen),
                    stats=dict(stats), infeasible_at=[[a, b, c] for (a, b), c in why.most_common(8)], found=found,
                    seconds=round(time.time() - t0, 1), rss_flag=bool(rss and rss > 6))
    with open(OUT, 'w') as f, mp.get_context('fork').Pool(3, maxtasksperchild=2) as pool:
        for r in pool.imap_unordered(job, tasks):
            if r.get('found') and 'key' in r['found']: r['found']['key'] = [list(x) for x in r['found']['key']]
            f.write(json.dumps(r, sort_keys=True, default=str) + '\n'); f.flush()
            print(r['q'], r['u'], 'cands', r['candidates'], 'trials', r['trials'], 'distinct', r['distinct'], r['stats'], r['infeasible_at'][:3], 'FOUND' if r['found'] else '', r['seconds'], flush=True)
