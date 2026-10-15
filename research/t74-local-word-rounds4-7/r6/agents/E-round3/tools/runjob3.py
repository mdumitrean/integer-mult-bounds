"""runjob3.py: k-round residual-repair helper-donor kernel search (agent E-round3, r6).

Generalises r3 B-interact's runjob2.py (cone-aware single-insert admission, exact set test with minimal-conflict cuts,
PR2142 per-basis column equations; built on PR2142 skkernel.py by Ian Libanio and PR1957 tools by Rohan Arun) from two
rounds to up to R rounds.  Round k+1 is solved on the current word W_k for the exact residual base - map(W_k), so an
inexact (interacting) repair can itself be repaired.  Rounds 1..R-1 may interact; round R cuts interacting pairs lazily,
because an inexact last round cannot be repaired.  Exactness is checked after every round and every exact word is priced
(derived compensation must be unchanged, as in r3).  The oracle budget is summed over all rounds: total oracle cost
<= -ddel - 1; the per-insert cap of each round is the remaining budget.

Options (SPEC): rounds, K (proposals per round, list), maxterms, tl, lam_den, lamr, cut_iters, r1_diverse,
merge_cuts (canonical form for every round: inserts with the same (x, y) whose insertion points are separated by no base
gate that writes x, reads x or writes y form a segment; at most one of them may be selected unless another selected insert
in the segment's range touches x or writes y.  Two such inserts merge into one insert x += (l1+l2) y with the same exact
map, a subset of the frame constraints and a concave (never larger) frame cost, so the cut loses no improving kernel),
diag (classify an infeasible round: drop the summed budget; then allow 24 terms; then rebuild candidates without the
per-insert cap), exact_nogood (after each solution exclude exactly that support, sum_supp z - sum_rest z <= |supp|-1,
instead of r3's cut sum_supp z <= |supp|-1, which also excludes every superset of the support).
usage: runjob3.py WORD SPEC.json OUT.json"""
import bisect, json, os, sys, time
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import (H, F, Q, V, Round, Orc, compile_AB, cone_caps, diff, family_values, fullseq, inline, maps, price_word,
                 sec_sizes, write_back, word_seq_insert)
from runjob import shift_fn, exact
from cone import LU, feasible, minimal_conflict
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))


def compose(f, g):
    return lambda i: f(g(i))


def merge_cuts(Rd):
    """canonical-form cuts (see module doc); returns the number of segment constraints added."""
    seq, cand = Rd.seq, Rd.cand
    wr, rd = defaultdict(list), defaultdict(list)
    for p, g in enumerate(seq):
        wr[g[1]].append(p)
        if g[0] == 'add': rd[g[2]].append(p)
    groups = defaultdict(list)
    for j, c in enumerate(cand): groups[(c[0], c[1])].append(j)
    touch = defaultdict(list)                       # register r -> candidates that write r or read r
    for j, c in enumerate(cand): touch[c[0]].append(j); touch[c[1]].append(j)
    n = 0
    for (x, y), js in groups.items():
        if len(js) < 2: continue
        block = sorted(set(wr[x]) | set(rd[x]) | set(wr[y]))
        seg = defaultdict(list)
        for j in js: seg[bisect.bisect_right(block, cand[j][2] - 1)].append(j)   # gates at index < i precede point i
        for s, members in seg.items():
            if len(members) < 2: continue
            lo = min(cand[j][2] for j in members); hi = max(cand[j][2] for j in members); mem = set(members)
            others = [c for c in set(touch[x]) | set(j2 for j2 in touch[y] if cand[j2][0] == y)
                      if c not in mem and lo <= cand[c][2] <= hi]
            Rd.m.Add(sum(Rd.z[j] for j in members) - sum(Rd.z[c] for c in others) <= 1); n += 1
    return n


def exact_nogood_solve(Rd):
    """Round.solve with an exact no-good: only the found support is excluded (not its supersets)."""
    from sk2 import cp_model
    def solve(tl, workers=None):
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_workers = workers or 1
        st = s.Solve(Rd.m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return s.StatusName(st), None
        supp = [j for j in range(len(Rd.cand)) if s.Value(Rd.z[j])]; ss = set(supp)
        sol = [(j, Q(s.Value(Rd.lam[j]), Rd.lam_den)) for j in supp]
        Rd.m.Add(sum(Rd.z[j] for j in supp) - sum(Rd.z[j] for j in range(len(Rd.cand)) if j not in ss) <= len(supp) - 1)
        return s.StatusName(st), sol
    Rd.solve = solve


def proposals(Rd, P, W0, maxk, max_cuts, tl, label, rec, final):
    got = cuts = 0
    while got < maxk and cuts <= max_cuts:
        st, sol = Rd.solve(tl)
        if sol is None: rec[label + '_stop'] = st; print(f'    {label} stop', st, flush=True); return
        if final:
            inter = Rd.interacting_pairs(sol)
            if inter:
                cuts += 1
                for a, b_ in inter: Rd.m.Add(Rd.z[a] + Rd.z[b_] <= 1)
                continue
        Wn, ins = Rd.apply(sol); ok, why = feasible(P, Wn)
        if not ok:
            mc = minimal_conflict(P, W0, ins, build); js = [sol[Rd.last_order[m]][0] for m in mc]
            Rd.m.Add(sum(Rd.z[j] for j in js) <= len(js) - 1); cuts += 1
            rec.setdefault(label + '_cone_cuts', []).append(dict(why=str(why), conflict=[(Rd.cand[j][0], Rd.cand[j][1], Rd.cand[j][2]) for j in js]))
            print(f'    {label} cone cut {len(js)} inserts', why, flush=True); continue
        got += 1; yield sol, Wn, ins


def diagnose(Rd, P, W, base_maps, orc, shift, fam, o, W1secs, tl):
    """classify why round Rd has no first-order solution."""
    out = {}
    Rd.nobud = True; Rd.model(o['maxterms'], lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
    st, sol = Rd.solve(tl); out['no_summed_budget'] = st if sol is None else 'FEASIBLE'
    Rd.model(24, lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
    st, sol = Rd.solve(tl); out['no_summed_budget_24_terms'] = st if sol is None else 'FEASIBLE'
    if o.get('diag_nocap'):
        R0 = Round(P, W, base_maps, orc, shift, fam, 1.0, None, orc_secs=W1secs); R0.lu = LU(P, W)
        c0 = R0.candidates(); n_all = len(c0)
        R0.cand = [c for c in c0 if c[5] < 10 ** 15]   # the oracle returns INF for frame-impossible inserts
        R0.nobud = True; R0.model(24, lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
        out['no_cap_candidates'] = len(R0.cand); out['no_cap_inf_dropped'] = n_all - len(R0.cand); out['no_cap_shape'] = R0.shape
        if R0.shape:
            st, sol = R0.solve(o.get('diag_nocap_tl', tl)); out['no_cap_no_budget_24_terms'] = st if sol is None else 'FEASIBLE'
            if sol is not None:
                out['no_cap_solution_cost'] = sum(R0.cand[j][5] for j, _ in sol)
                out['no_cap_solution_terms'] = [(R0.cand[j][0], R0.cand[j][1], R0.cand[j][2], str(l)) for j, l in sol]
        else: out['no_cap_no_budget_24_terms'] = 'SHAPE_INFEASIBLE'
    return out


def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    P = H.Pricer(word); base_maps = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
    print('base cost', P.base_cost, P.base_profile, f'{time.time()-t00:.1f}s', flush=True)
    o = dict(depth=1, rounds=4, K=[3, 2, 2, 1], maxterms=12, tl=60, cut_iters=12, lam_den=4, lamr=16, r1_diverse=True,
             merge_cuts=False, diag=True, diag_nocap=False, diag_tl=60)
    o.update({k: v for k, v in spec.items() if k != 'jobs'}); results = []
    stats = defaultdict(int)
    for dels in spec['jobs']:
        dels = [tuple(d) for d in dels]; t0 = time.time(); rec = dict(dels=dels, opts=o)
        W1 = compile_AB(P.base, dict(delete=dels)); W1secs = sec_sizes(W1)
        g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
        orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1; rec['ddel'] = ddel
        NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
        for s, i in dels: gg = seq0[i if s == 'A' else NA + NC + i]; regs |= {gg[1], gg[2]}
        nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
        fam, famregs = family_values(fullseq(W1), regs, nreg, o['depth'])
        print('job', dels, 'ddel', ddel, 'budget', bud, flush=True)
        diag_done = set()

        def search(k, W, shift, spent, node):
            Rd = Round(P, W, base_maps, orc, shift, fam, 1.0, bud - spent, orc_secs=W1secs); Rd.lu = LU(P, W)
            tg = time.time(); cand = Rd.candidates()
            Rd.model(o['maxterms'], lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
            node.update(round=k, ncand=len(cand), cone_rejected=getattr(Rd, 'cone_rejected', 0), shape=Rd.shape,
                        residual_rank=Rd.nT, budget_left=bud - spent, gen_s=round(time.time() - tg, 1), children=[])
            if o['merge_cuts']: node['merge_segments'] = merge_cuts(Rd)
            if o.get('exact_nogood'): exact_nogood_solve(Rd)
            stats[f'round{k}_models'] += 1
            print(f'  {"  " * (k - 1)}r{k} cand {len(cand)} cone-rejected {node["cone_rejected"]} shape {Rd.shape} '
                  f'T-rank {Rd.nT} budget {bud - spent} segs {node.get("merge_segments")} {node["gen_s"]}s', flush=True)
            if not Rd.shape: node['stop'] = 'SHAPE_INFEASIBLE'; return
            final = k == o['rounds']; nprop = 0
            Kk = o['K'][k - 1] if k - 1 < len(o['K']) else 1
            for sol, Wn, ins in proposals(Rd, P, W, Kk, o['cut_iters'], o['tl'], f'r{k}', node, final):
                nprop += 1; stats[f'round{k}_proposals'] += 1
                est = sum(Rd.cand[j][5] for j, _ in sol); inter = Rd.interacting_pairs(sol); ex = exact(base_maps, Wn)
                if k == 1 and o['r1_diverse'] and inter:
                    for a, _ in inter: Rd.m.Add(Rd.z[a] == 0)
                ch = dict(terms=[(Rd.cand[j][0], Rd.cand[j][1], Rd.cand[j][2], str(l)) for j, l in sol], est=est,
                          interacting=len(inter), exact=ex, ins=ins)
                print(f'  {"  " * (k - 1)}r{k} terms {len(sol)} est {est} interacting {len(inter)} exact {ex}', ch['terms'], flush=True)
                if ex:
                    pr = price_word(P, Wn, base_comp); ch['price'] = {kk: v for kk, v in pr.items() if kk not in ('graph', 'assign')}
                    stats['exact_priced'] += 1
                    if isinstance(ch['price'].get('delta'), int) and ch['price']['delta'] < 0: stats['GAINS'] += 1
                    print(f'  {"  " * (k - 1)}  price', ch['price'], flush=True)
                elif k < o['rounds'] and bud - spent - est > 0:
                    sub = dict(); ch['next'] = sub
                    search(k + 1, Wn, compose(shift, shift_fn(ins)), spent + est, sub)
                else: ch['stop'] = 'no rounds or budget left'
                node['children'].append(ch)
            node['proposals'] = nprop
            if nprop == 0 and o['diag'] and k >= 2 and k not in diag_done:
                diag_done.add(k); node['diagnosis'] = diagnose(Rd, P, W, base_maps, orc, shift, fam, o, W1secs, o['diag_tl'])
                print(f'  {"  " * (k - 1)}r{k} diagnosis', node['diagnosis'], flush=True)

        root = dict(); rec['tree'] = root
        search(1, W1, lambda i: i, 0, root)
        rec['seconds'] = round(time.time() - t0, 1); results.append(rec)
        json.dump(dict(results=results, stats=dict(stats)), open(out_p, 'w'), default=str)
    print('done', dict(stats), f'{time.time()-t00:.1f}s', flush=True)


if __name__ == '__main__':
    main()
