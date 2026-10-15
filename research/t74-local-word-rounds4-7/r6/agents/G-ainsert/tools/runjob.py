"""runjob.py: residual-repair helper-donor kernel jobs on one word (agent B-interact, r3).
usage: runjob.py WORD SPEC.json OUT.json      SPEC = {"jobs": [[["B",783]], ...], options...}
options: depth (key-family depth, 1 = PR2142), r1_ban (none|direct), K1, K2, maxterms1, maxterms2, tl1, tl2, cap1, cap2,
cut_iters (lazy exact-interaction cuts per round-2 search), round2 (bool)."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sk2
from sk2 import (H, F, Q, V, Round, Orc, compile_AB, cone_caps, diff, family_values, fullseq, inline, maps, price_word,
                 sec_sizes, write_back)

def shift_fn(ins):
    """W2 insertion point -> W1 insertion point, for inserts ins = [(W1 pos, gate)] sorted as applied."""
    w2idx = sorted(p + k for k, (p, _) in enumerate(ins))
    def f(i): return i - sum(1 for t in w2idx if t < i)
    return f

def exact(base_maps, W):
    cm = maps(W); return not diff(base_maps[0], cm[0]) and not diff(base_maps[1], cm[1])

def main():
    word, spec_p, out_p = sys.argv[1:4]; spec = json.load(open(spec_p)); t00 = time.time()
    P = H.Pricer(word); base_maps = maps(P.base); base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
    print('base cost', P.base_cost, P.base_profile, 'comp', len(base_comp), f'{time.time()-t00:.1f}s', flush=True)
    o = dict(depth=1, r1_ban='none', K1=6, K2=4, maxterms1=12, maxterms2=12, tl1=60, tl2=60, cap1=1.0, cap2=1.0, cut_iters=6, round2=True)
    o.update({k: v for k, v in spec.items() if k != 'jobs'}); results = []
    for dels in spec['jobs']:
        dels = [tuple(d) for d in dels]; t0 = time.time(); rec = dict(dels=dels, opts=o, round1=[])
        W1 = compile_AB(P.base, dict(delete=dels))
        g = F.Graph(inline(W1, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        r = F.optimal_frames(inline(W1, True), P.costs, check_literal=False, graph=g); ddel = r['cost'] - P.base_cost
        orc = Orc(write_back(W1, g, r['assign']), P.costs.c); bud = -ddel - 1; rec['ddel'] = ddel
        NA, NC, NB = sec_sizes(P.base); seq0 = fullseq(P.base)
        gi = [i if s == 'A' else NA + NC + i for s, i in dels]
        regs = set()
        for i in gi: regs |= {seq0[i][1], seq0[i][2]}
        nreg = max(2 * V + P.base['report']['R'], 1 + max(max(x[1], x[2] if x[0] == 'add' else 0) for x in seq0))
        fam, famregs = family_values(fullseq(W1), regs, nreg, o['depth'])
        R1 = Round(P, W1, base_maps, orc, lambda i: i, fam, o['cap1'], bud, orc_secs=sec_sizes(W1))
        R1.nobud = bool(o.get('r1_nobud')); cand = R1.candidates(); R1.model(o['maxterms1'], lamr=o.get('lamr', 8), ban=o['r1_ban'], lam_den=o.get('lam_den', 2))
        rec.update(family_regs=famregs, basis=len(R1.basis.piv), residual_rank=R1.nT, ncand1=len(cand), shape1=R1.shape)
        print('job', dels, 'ddel', ddel, 'famregs', len(famregs), 'basis', len(R1.basis.piv), 'T-rank', R1.nT, 'cand', len(cand),
              'shape', R1.shape, f'{time.time()-t0:.1f}s', flush=True)
        for it in range(o['K1'] if R1.shape else 0):
            st, sol = R1.solve(o['tl1'])
            if sol is None: rec['round1_stop'] = st; print('  r1 stop', st, flush=True); break
            est1 = sum(R1.cand[j][5] for j, _ in sol); W2, ins1 = R1.apply(sol)
            inter = R1.interacting_pairs(sol); ex = exact(base_maps, W2)
            if o.get('r1_diverse') and inter:
                for a, _ in inter: R1.m.Add(R1.z[a] == 0)   # next proposal: a different interacting writer
            e1 = dict(terms=[(R1.cand[j][0], R1.cand[j][1], R1.cand[j][2], str(l)) for j, l in sol], est=est1,
                      interacting=len(inter), exact=ex, round2=[])
            print(f'  r1 #{it} terms {len(sol)} est {est1} interacting {len(inter)} exact {ex}', e1['terms'], flush=True)
            if ex:
                pr = price_word(P, W2, base_comp); e1['price'] = {k: v for k, v in pr.items() if k not in ('graph', 'assign')}
                print('    price', e1['price'], flush=True)
            elif o['round2'] and bud - est1 > 0:
                R2 = Round(P, W2, base_maps, orc, shift_fn(ins1), fam, o['cap2'], bud - est1, orc_secs=sec_sizes(W1))
                R2.nobud = bool(o.get('r2_nobud')); c2 = R2.candidates(); R2.model(o['maxterms2'], lamr=o.get('lamr', 8), ban='none', lam_den=o.get('lam_den', 2))
                e1.update(ncand2=len(c2), shape2=R2.shape, residual_rank2=R2.nT, basis2=len(R2.basis.piv))
                print(f'    r2 cand {len(c2)} shape {R2.shape} T-rank {R2.nT} basis {len(R2.basis.piv)}', flush=True)
                got = 0; cuts = 0
                while R2.shape and got < o['K2'] and cuts <= o['cut_iters']:
                    st2, sol2 = R2.solve(o['tl2'])
                    if sol2 is None: e1['round2_stop'] = st2; print('    r2 stop', st2, flush=True); break
                    inter2 = R2.interacting_pairs(sol2)
                    if inter2:
                        cuts += 1
                        for a, b_ in inter2: R2.m.Add(R2.z[a] + R2.z[b_] <= 1)
                        continue
                    got += 1; W3, ins2 = R2.apply(sol2); ex3 = exact(base_maps, W3); est2 = sum(R2.cand[j][5] for j, _ in sol2)
                    e2 = dict(terms=[(R2.cand[j][0], R2.cand[j][1], R2.cand[j][2], str(l)) for j, l in sol2], est=est2, exact=ex3)
                    if ex3:
                        pr = price_word(P, W3, base_comp); e2['price'] = {k: v for k, v in pr.items() if k not in ('graph', 'assign')}
                        e2['ins1'] = [(p, gg) for p, gg in ins1]; e2['ins2'] = [(p, gg) for p, gg in ins2]
                    print(f'    r2 #{got} terms {len(sol2)} est {est2} exact {ex3}', e2.get('price'), e2['terms'], flush=True)
                    e1['round2'].append(e2)
            rec['round1'].append(e1)
        rec['seconds'] = round(time.time() - t0, 1); results.append(rec)
        json.dump(results, open(out_p, 'w'), default=str)
    print('done', f'{time.time()-t00:.1f}s', flush=True)

if __name__ == '__main__':
    main()
