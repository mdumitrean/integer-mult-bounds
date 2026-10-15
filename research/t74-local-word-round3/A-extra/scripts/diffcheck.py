"""Exact base-vs-extra identity test of #2142's split-key CP-SAT model for each deletion job.
Gates are identical, so keys, holders, positions, columns and equations coincide; the model can differ only through the
deletion price (budget) and the frame-cost oracle.  The oracle cost of a candidate (x, y, p) depends only on the frame
timelines of x and y in the deleted word with optimal frames.  Let S = registers whose timeline (start, every (position,
before, after) step, end) differs between the two deleted words.  Candidates with x, y outside S have equal costs.  This
tool enumerates exactly the S-involving candidates of skkernel's loop on both words; the models are identical iff the
budgets are equal and every S-involving candidate has equal cost or exceeds both caps.
usage: diffcheck.py BASE EXTRA JOBS.json OUT.json [--workers 3]"""
import argparse, json, os, sys, time, multiprocessing as mp
from fractions import Fraction as Q
from collections import defaultdict
ap = argparse.ArgumentParser(); ap.add_argument('base'); ap.add_argument('extra'); ap.add_argument('jobs'); ap.add_argument('out')
ap.add_argument('--workers', type=int, default=3); a = ap.parse_args()
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2
from sk2 import H, F, inline, write_back, Orc, norm, coef, compile_AB, fullseq, V
from compat_shim import deadline, Timeout, peak_rss_gib
PB = PE = None
def init():
    global PB, PE; PB = H.Pricer(a.base); PE = H.Pricer(a.extra)
def deleted_orc(P, dels):
    w1 = compile_AB(P.base, dict(delete=dels))
    gr = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
    r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=gr)
    w2 = write_back(w1, gr, r['assign']); return r['cost'] - P.base_cost, Orc(w2, P.costs.c)
def run(job):
    dels = [tuple(x) for x in job]; t0 = time.time(); out = dict(job=job)
    try:
        with deadline(600):
            db, ob = deleted_orc(PB, dels); de, oe = deleted_orc(PE, dels)
            regs = set(ob.g) | set(oe.g) | set(range(len(ob.start)))
            S = sorted(r for r in regs if ob.g.get(r) != oe.g.get(r) or ob.start[r] != oe.start[r] or ob.ends[r] != oe.ends[r])
            out.update(ddel_base=db, ddel_extra=de, S=S)
            bud_b, bud_e = -db - 1, -de - 1; cap_b, cap_e = sk2.CANDCAP * bud_b, sk2.CANDCAP * bud_e
            # skkernel's holders (deleted word, exact rationals), as in sk2.build
            w = PB.base; NA, NC, NB = len(w['A']), len(w['cut']), len(w['B']); seq = fullseq(w); L = len(seq)
            nreg = max(2 * V + w['report']['R'], 1 + max(max(g[1], g[2] if g[0] == 'add' else 0) for g in seq))
            gidx = lambda s, i: i if s == 'A' else (NA + NC + i if s == 'B' else NA + NC + NB + i)
            dg = {gidx(s, i) for s, i in dels}
            rows = {}; get = lambda x: rows.get(x, {x: Q(1)}); srcval = {}; hist = defaultdict(list); addin = defaultdict(list)
            cur_key = {x: norm({x: Q(1)}) for x in range(nreg)}; cur_start = {x: 0 for x in range(nreg)}; wins = defaultdict(list)
            for x in range(nreg): hist[x].append((0, {x: Q(1)}))
            for i, g in enumerate(seq):
                if i in dg: srcval[i] = dict(get(g[2])); continue
                t = g[1]
                if g[0] == 'add':
                    addin[t].append(dict(get(g[2]))); aa = dict(get(t)); c = coef(g)
                    for k, v in get(g[2]).items():
                        aa[k] = aa.get(k, 0) + c * v
                        if not aa[k]: del aa[k]
                else: aa = {k: v * coef(g) for k, v in get(t).items()}
                rows[t] = aa; nk = norm(aa); hist[t].append((i + 1, dict(aa)))
                if nk != cur_key[t]:
                    key, al = cur_key[t]
                    if key is not None: wins[key].append((t, cur_start[t], i + 1, al))
                    cur_key[t] = nk; cur_start[t] = i + 1
            for x in range(nreg):
                key, al = cur_key[x]
                if key is not None: wins[key].append((x, cur_start[x], L + 1, al))
            (i0,) = dg; g0 = seq[i0]; s0, t0r = g0[2], g0[1]; vkey, _ = norm(srcval[i0]); fam = [vkey]
            for r_ in (s0, t0r):
                for val in [val for _, val in hist[r_]] + addin[r_]:
                    k, _ = norm(val)
                    if k is not None and k not in fam: fam.append(k)
            holders = defaultdict(list)
            for ki, k in enumerate(fam):
                for y, a_, b_, al in wins[k]:
                    for p in range(a_, min(b_, L + 1)): holders[p].append((y, ki))
            dA = sorted(i for s, i in dels if s == 'A'); dB = sorted(i for s, i in dels if s == 'B')
            def orcpos(gi):
                if gi < NA: return gi - sum(1 for t in dA if t < gi)
                if gi < NA + NC: return None
                if gi < NA + NC + NB: return (NA - len(dA)) + (gi - NA - NC) - sum(1 for t in dB if t < gi - NA - NC)
                return (NA - len(dA)) + (NB - len(dB)) + (gi - NA - NC - NB)
            Sset = set(S); diffs = []; checked = 0
            for i, hl in holders.items():
                op = orcpos(i)
                if op is None: continue
                for y, ki in hl:
                    xs = range(nreg) if y in Sset else S
                    for x in xs:
                        if x == y or (V <= y < 2 * V and not (V <= x < 2 * V)): continue
                        cb = ob.cost(x, y, op); ce = oe.cost(x, y, op); checked += 1
                        if cb != ce and min(cb, ce) <= max(cap_b, cap_e): diffs.append((x, y, i, ki, cb, ce))
            out.update(status='ok', keys=len(fam), checked=checked, ndiff=len(diffs), diffs=diffs[:20],
                       identical=(db == de and not diffs), extra_cheaper=sum(1 for d_ in diffs if d_[5] < d_[4]))
    except Timeout: out['status'] = 'timeout'
    except Exception as e: out['status'] = 'err:' + repr(e)[:160]
    out['sec'] = round(time.time() - t0, 1); rss = peak_rss_gib()
    if rss is not None and rss > 6: out['rss_exit'] = True
    return out
if __name__ == '__main__':
    jobs = json.load(open(a.jobs)); res = []; t0 = time.time()
    with mp.get_context('fork').Pool(a.workers, initializer=init, maxtasksperchild=10) as pool:
        for n, r in enumerate(pool.imap_unordered(run, jobs), 1):
            res.append(r); print(n, len(jobs), f'{time.time()-t0:.0f}s', r['job'], r.get('status'), 'ddel', r.get('ddel_base'), r.get('ddel_extra'),
                                'S', len(r.get('S', [])), 'checked', r.get('checked'), 'ndiff', r.get('ndiff'), 'identical', r.get('identical'), r.get('sec'), flush=True)
            json.dump(res, open(a.out, 'w'))
    print('done', f'{time.time()-t0:.0f}s', flush=True)
