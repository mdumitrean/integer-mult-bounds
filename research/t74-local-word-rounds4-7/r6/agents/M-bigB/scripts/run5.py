"""run5.py (agent M-bigB, r6): r5 D-compsplit run3.py with sk5.PRound5 (sentinel-cost inserts kept at cost 0, cone-tested).
Original docstring: run3.py: projected split-key kernel jobs (sk3.PRound) on one word.  usage: run3.py WORD SPEC.json OUT.json
SPEC: {"jobs": [[["B", 933]], ...], "maxterms": 12, "lamr": 16, "lam_den": 4, "K": 4, "tl": 120, "cap": 1.0, "depth": 1,
       "ban": "none", "cut_iters": 25, "known": {"<job index>": [[x, y, seqpos, lam], ...]}}
Every proposal: lazy cuts on really interacting pairs (no interactions in a returned kernel), the exact frame set test under
the base caps with minimal-conflict cuts, then the projected exactness check.  Exact proposals are written as rev3
compile_edits edits on the BASE word for pricing by price3.py (compensation re-derived)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "r5", "agents", "D-compsplit", "tools"))
from sk5 import PRound5 as PRound
from sk3 import (H, F, Q, V, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back,
                 word_seq_insert, absorbable, exact_proj, to_base_edit, to_base_edit_ab)
from cone import LU, feasible, minimal_conflict
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))

def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    o = dict(maxterms=12, lamr=16, lam_den=4, K=4, tl=120, cap=1.0, depth=1, ban='none', cut_iters=25)
    o.update({k: v for k, v in spec.items() if k not in ('jobs', 'known')})
    P = H.Pricer(word); base_maps = maps(P.base); ab = absorbable(P.base)
    print('base cost', P.base_cost, 'absorbable', len(ab), f'{time.time()-t00:.1f}s', flush=True); results = []
    for ji, dels in enumerate(spec['jobs']):
        dels = [tuple(d) for d in dels]; t0 = time.time(); rec = dict(dels=dels, opts=o, proposals=[], cuts=[])
        W1 = compile_AB(P.base, dict(delete=dels))
        g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
        orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1; rec['ddel'] = ddel
        NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
        for s, i in dels: gg = seq0[i if s == 'A' else NA + NC + i]; regs |= {gg[1], gg[2]}
        nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
        fam, famregs = family_values(fullseq(W1), regs, nreg, o['depth'])
        Rd = PRound(P, W1, base_maps, orc, lambda i: i, fam, o['cap'], bud, orc_secs=sec_sizes(W1), ab=ab); Rd.nobud = bool(o.get('nobud'))
        known = spec.get('known', {}).get(str(ji))
        Rd.lu = LU(P, W1); cand = Rd.candidates(force={(x, y, p) for x, y, p, l in (known or [])})
        if o.get('ban_reinsert'):   # diagnostic: forbid re-reading the deleted gate's source into its target
            dg = {(seq0[NA + NC + i][1], seq0[NA + NC + i][2]) for s_, i in dels if s_ == 'B'}
            Rd.cand = cand = [c for c in cand if (c[0], c[1]) not in dg]
        Rd.model(o['maxterms'], lamr=o['lamr'], ban=o['ban'], lam_den=o['lam_den'])
        rec.update(target_rank=Rd.nT, basisN=len(Rd.bN.piv), basisP=len(Rd.bP.piv), ncand=len(cand), cone_rejected=Rd.cone_rejected,
                   cost_rejected=Rd.cost_rejected, sentinel_kept=Rd.sentinel_kept, sentinel_cone_rejected=Rd.sentinel_cone_rejected, shape=Rd.shape, neqs=Rd.neqs, gates=[seq0[i if s == 'A' else NA + NC + i][:5] for s, i in dels])
        print('job', dels, rec['gates'], 'ddel', ddel, 'T rank', Rd.nT, 'basis', len(Rd.bN.piv), len(Rd.bP.piv), 'cand', len(cand),
              'cone-rej', Rd.cone_rejected, 'shape', Rd.shape, f'{time.time()-t0:.1f}s', flush=True)
        if known:
            fixj = []
            for x, y, p, l in known:
                js = [j for j, c in enumerate(cand) if c[0] == x and c[1] == y and c[2] == p]
                fixj.append((x, y, p, l, js[:1]))
            rec['known_in_candidates'] = [(x, y, p, l, bool(js)) for x, y, p, l, js in fixj]
            print('  known inserts present:', rec['known_in_candidates'], flush=True)
            if all(js for *_, js in fixj):
                Rk = PRound(P, W1, base_maps, orc, lambda i: i, fam, o['cap'], None, orc_secs=sec_sizes(W1), ab=ab); Rk.cand = cand
                Rk.model(o['maxterms'], lamr=o['lamr'], ban='none', lam_den=o['lam_den'], fix=[(js[0], Q(l)) for x, y, p, l, js in fixj])
                for x, y, p, l, js in fixj: Rk.m.Add(Rk.z[js[0]] == 1)
                Rk.m.Add(sum(Rk.z) == len(fixj))
                st, sol = Rk.solve(o['tl']); rec['known_fixed_status'] = st; print('  known solution fixed:', st, flush=True)
        if Rd.shape:
            got = cuts = 0
            while got < o['K'] and cuts <= o['cut_iters']:
                st, sol = Rd.solve(o['tl'])
                if sol is None: rec['stop'] = st; print('  stop', st, flush=True); break
                W2, ins = Rd.apply(sol); terms = [(Rd.cand[j][0], Rd.cand[j][1], Rd.cand[j][2], str(l)) for j, l in sol]
                if not exact_proj(base_maps, W2, ab):
                    # first-order solution broken by a real interaction: cut the interacting pairs (support is cut by solve)
                    inter = Rd.interacting_pairs(sol); cuts += 1
                    for a, b_ in inter: Rd.m.Add(Rd.z[a] + Rd.z[b_] <= 1)
                    rec['cuts'].append(dict(kind='inexact', pairs=len(inter), terms=terms)); print('  inexact cut', len(inter), terms, flush=True); continue
                ok, why = feasible(P, W2)
                if not ok:
                    mc = minimal_conflict(P, W1, ins, build); js = [sol[Rd.last_order[m]][0] for m in mc]
                    Rd.m.Add(sum(Rd.z[j] for j in js) <= len(js) - 1); cuts += 1
                    rec['cuts'].append(dict(kind='frames', why=str(why)[:200], conflict=[(Rd.cand[j][0], Rd.cand[j][1], Rd.cand[j][2]) for j in js]))
                    print('  frame cut', len(js), str(why)[:120], flush=True); continue
                ex = True; est = sum(Rd.cand[j][5] for j, _ in sol)
                e = dict(terms=terms, est=est, exact=ex)
                if ex:
                    try: e['edit_ab'] = to_base_edit_ab(P.base, dels, W1, ins)
                    except ValueError as err: e['edit_error'] = str(err)
                rec['proposals'].append(e); got += 1
                if o.get('pair_nogood'):   # M-bigB: next proposal must leave out at least one (x, y) pair of this one
                    bs = []
                    for x_, y_ in sorted({(Rd.cand[j][0], Rd.cand[j][1]) for j, _ in sol}):
                        b_ = Rd.m.NewBoolVar('')
                        for j2, c2 in enumerate(Rd.cand):
                            if c2[0] == x_ and c2[1] == y_: Rd.m.AddImplication(Rd.z[j2], b_)
                        bs.append(b_)
                    Rd.m.Add(sum(bs) <= len(bs) - 1)
                print(f'  proposal terms {len(sol)} est {est} exact {ex}', terms, flush=True)
        rec['seconds'] = round(time.time() - t0, 1); results.append(rec)
        json.dump(results, open(out_p, 'w'), default=str)
    print('done', f'{time.time()-t00:.1f}s', flush=True)

if __name__ == '__main__':
    main()
