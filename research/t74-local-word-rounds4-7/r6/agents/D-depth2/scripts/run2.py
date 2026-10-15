"""run2.py WORD SPEC.json OUT.json: r3 B-interact's runjob2 (cone-aware residual-repair split-key search) with the
vectorised generator (gen2.FastRound) and a key-family depth option.  SPEC = {"jobs": [[["B",822]], ...], options}."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen2
from sk2 import (H, F, Q, V, Orc, compile_AB, cone_caps, family_values, fullseq, inline, maps, price_word, sec_sizes,
                 write_back, word_seq_insert)
from runjob import shift_fn, exact
from cone import LU, feasible
from runjob2 import proposals
R = gen2.FastRound

def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    P = H.Pricer(word); base_maps = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
    print('base cost', P.base_cost, P.base_profile, f'{time.time()-t00:.1f}s', flush=True)
    o = dict(depth=2, r1_ban='none', K1=3, K2=3, maxterms1=12, maxterms2=12, tl1=120, tl2=90, cap1=1.0, cap2=1.0, cut_iters=12,
             lam_den=4, lamr=16, r1_diverse=True, round2=True)
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
        R1 = R(P, W1, base_maps, orc, lambda i: i, fam, o['cap1'], bud, orc_secs=sec_sizes(W1)); R1.lu = LU(P, W1)
        tg = time.time(); cand = R1.candidates(); tg = time.time() - tg
        R1.model(o['maxterms1'], lamr=o['lamr'], ban=o['r1_ban'], lam_den=o['lam_den'])
        rec.update(family_regs=famregs, basis=len(R1.basis.piv), residual_rank=R1.nT, ncand1=len(cand),
                   cone_rejected1=R1.cone_rejected, shape1=R1.shape, gen_seconds1=round(tg, 1),
                   presolve_removed=getattr(R1, 'presolve_removed', 0), n_terms=getattr(R1, 'n_terms', None))
        print('job', dels, 'ddel', ddel, 'depth', o['depth'], 'famregs', len(famregs), 'basis', len(R1.basis.piv), 'cand', len(cand),
              'shape', R1.shape, 'presolve_removed', getattr(R1, 'presolve_removed', 0), 'terms', getattr(R1, 'n_terms', None), f'gen {tg:.1f}s', flush=True)
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
                elif o.get('round2', True) and bud - est1 > 0:
                    R2 = R(P, W2, base_maps, orc, shift_fn(ins1), fam, o['cap2'], bud - est1, orc_secs=sec_sizes(W1)); R2.lu = LU(P, W2)
                    c2 = R2.candidates(); R2.model(o['maxterms2'], lamr=o['lamr'], ban='none', lam_den=o['lam_den'])
                    e1.update(ncand2=len(c2), cone_rejected2=R2.cone_rejected, shape2=R2.shape, residual_rank2=R2.nT)
                    print(f'    r2 cand {len(c2)} shape {R2.shape} T-rank {R2.nT}', flush=True)
                    if R2.shape:
                        for sol2, W3, ins2 in proposals(R2, P, W2, o['K2'], o['cut_iters'], o['tl2'], 'r2', e1):
                            ex3 = exact(base_maps, W3); est2 = sum(R2.cand[j][5] for j, _ in sol2)
                            e2 = dict(terms=[(R2.cand[j][0], R2.cand[j][1], R2.cand[j][2], str(l)) for j, l in sol2], est=est2,
                                      exact=ex3, ins1=ins1, ins2=ins2)
                            if ex3: pr = price_word(P, W3, base_comp); e2['price'] = {k: v for k, v in pr.items() if k not in ('graph', 'assign')}
                            print(f'    r2 terms {len(sol2)} est {est2} exact {ex3}', e2.get('price'), flush=True)
                            e1['round2'].append(e2)
                    else: e1['round2_stop'] = 'SHAPE_INFEASIBLE'
                rec['round1'].append(e1)
        rec['seconds'] = round(time.time() - t0, 1); results.append(rec)
        json.dump(results, open(out_p, 'w'), default=str)
    print('done', f'{time.time()-t00:.1f}s', flush=True)

if __name__ == '__main__':
    main()
