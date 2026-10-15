"""runjob2.py: runjob.py with the cone-cap aware filter (lead 1): every candidate insert must pass the exact single-insert
cone test on the round's word (cone.LU.ok), and every proposal word must pass the exact set test (Graph under the base
caps); a failing proposal is cut by a minimal conflicting subset (deletion filter) before anything is priced.
usage: runjob2.py WORD SPEC.json OUT.json"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import (H, F, Q, V, Round, Orc, compile_AB, cone_caps, diff, family_values, fullseq, inline, maps, price_word,
                 sec_sizes, write_back, word_seq_insert)
from runjob import shift_fn, exact
from cone import LU, feasible, minimal_conflict
build = lambda W, ins: compile_AB(W, word_seq_insert(W, sorted(ins, key=lambda t: t[0])))

def proposals(Rd, P, W0, maxk, max_cuts, tl, label, rec):
    """yield cone-feasible solutions of round Rd (on word W0): set-test each, cut minimal conflicts."""
    got = cuts = 0
    while got < maxk and cuts <= max_cuts:
        st, sol = Rd.solve(tl)
        if sol is None: rec[label + '_stop'] = st; print(f'    {label} stop', st, flush=True); return
        if label == 'r2':
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

def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    P = H.Pricer(word); base_maps = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
    print('base cost', P.base_cost, P.base_profile, f'{time.time()-t00:.1f}s', flush=True)
    o = dict(depth=1, r1_ban='none', K1=3, K2=3, maxterms1=12, maxterms2=12, tl1=60, tl2=60, cap1=1.0, cap2=1.0, cut_iters=12,
             lam_den=4, lamr=16, r1_diverse=True)
    o.update({k: v for k, v in spec.items() if k != 'jobs'}); results = []
    for dels in spec['jobs']:
        dels = [tuple(d) for d in dels]; t0 = time.time(); rec = dict(dels=dels, opts=o, round1=[])
        W1 = compile_AB(P.base, dict(delete=dels))
        g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
        orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1; rec['ddel'] = ddel
        NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base); regs = set()
        for s, i in dels: gg = seq0[i if s == 'A' else NA + NC + i]; regs |= {gg[1], gg[2]}
        nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
        fam, famregs = family_values(fullseq(W1), regs, nreg, o['depth'])
        R1 = Round(P, W1, base_maps, orc, lambda i: i, fam, o['cap1'], bud, orc_secs=sec_sizes(W1)); R1.lu = LU(P, W1)
        cand = R1.candidates(); R1.model(o['maxterms1'], lamr=o['lamr'], ban=o['r1_ban'], lam_den=o['lam_den'])
        rec.update(basis=len(R1.basis.piv), residual_rank=R1.nT, ncand1=len(cand), cone_rejected1=getattr(R1, 'cone_rejected', 0), shape1=R1.shape)
        print('job', dels, 'ddel', ddel, 'basis', len(R1.basis.piv), 'cand', len(cand), 'cone-rejected', rec['cone_rejected1'],
              'shape', R1.shape, f'{time.time()-t0:.1f}s', flush=True)
        if R1.shape:
            for sol, W2, ins1 in proposals(R1, P, W1, o['K1'], o['cut_iters'], o['tl1'], 'r1', rec):
                est1 = sum(R1.cand[j][5] for j, _ in sol); inter = R1.interacting_pairs(sol); ex = exact(base_maps, W2)
                if o.get('r1_diverse') and inter:
                    for a, _ in inter: R1.m.Add(R1.z[a] == 0)
                e1 = dict(terms=[(R1.cand[j][0], R1.cand[j][1], R1.cand[j][2], str(l)) for j, l in sol], est=est1,
                          interacting=len(inter), exact=ex, round2=[], ins1=ins1)
                print(f'  r1 terms {len(sol)} est {est1} interacting {len(inter)} exact {ex}', e1['terms'], flush=True)
                if ex:
                    pr = price_word(P, W2, base_comp); e1['price'] = {k: v for k, v in pr.items() if k not in ('graph', 'assign')}
                    print('    price', e1['price'], flush=True)
                elif bud - est1 > 0:
                    R2 = Round(P, W2, base_maps, orc, shift_fn(ins1), fam, o['cap2'], bud - est1, orc_secs=sec_sizes(W1)); R2.lu = LU(P, W2)
                    c2 = R2.candidates(); R2.model(o['maxterms2'], lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
                    e1.update(ncand2=len(c2), cone_rejected2=getattr(R2, 'cone_rejected', 0), shape2=R2.shape, residual_rank2=R2.nT)
                    print(f'    r2 cand {len(c2)} cone-rejected {e1["cone_rejected2"]} shape {R2.shape} T-rank {R2.nT}', flush=True)
                    if R2.shape:
                        for sol2, W3, ins2 in proposals(R2, P, W2, o['K2'], o['cut_iters'], o['tl2'], 'r2', e1):
                            ex3 = exact(base_maps, W3); est2 = sum(R2.cand[j][5] for j, _ in sol2)
                            e2 = dict(terms=[(R2.cand[j][0], R2.cand[j][1], R2.cand[j][2], str(l)) for j, l in sol2], est=est2, exact=ex3,
                                      ins1=ins1, ins2=ins2)
                            if ex3:
                                pr = price_word(P, W3, base_comp); e2['price'] = {k: v for k, v in pr.items() if k not in ('graph', 'assign')}
                            print(f'    r2 terms {len(sol2)} est {est2} exact {ex3}', e2.get('price'), e2['terms'], flush=True)
                            e1['round2'].append(e2)
                    else: e1['round2_stop'] = 'SHAPE_INFEASIBLE'
                rec['round1'].append(e1)
        rec['seconds'] = round(time.time() - t0, 1); results.append(rec)
        json.dump(results, open(out_p, 'w'), default=str)
    print('done', f'{time.time()-t00:.1f}s', flush=True)

if __name__ == '__main__':
    main()
