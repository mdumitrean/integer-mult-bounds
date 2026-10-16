#!/usr/bin/env python3
"""Lane B grounding: Parikh vectors, climb strings, the kappa price table, unit moves and ceilings.

Reads only the #2802 package inputs (WORD-base/WORD2751-base, PROFILE) and reproduces the
certified root with Decimal bisection (same method as $S/r10/mine/root.py).  Nothing heavy.
Run:  python -I parikh_kappa.py > OUT.txt
"""
import gzip, json, collections, sys
from decimal import Decimal as D, getcontext
getcontext().prec = 60

import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
PKG = str(_ROOT / 'research/t74-joint-twelve-retired7') + '/'
M_DIM, W_LIVE, N_CALLS = 73, 66304, 666
CERT = D('0.001717794984118634663827')

# ---------------------------------------------------------------- moment / root / prices
def moment(prof, k):
    return sum(D(c) * D(r) / D(M_DIM) * (k * (D(M_DIM) / D(r)).ln()).exp() for r, c in prof.items() if c)

def root(prof, lo=D(0), hi=D('0.05'), it=200):
    for _ in range(it):
        mid = (lo + hi) / 2
        if moment(prof, mid) < D(W_LIVE): lo = mid
        else: hi = mid
    return lo

def dM_dk(prof, k):
    return sum(D(c) * D(r) / D(M_DIM) * (k * (D(M_DIM) / D(r)).ln()).exp() * (D(M_DIM) / D(r)).ln()
               for r, c in prof.items() if c)

def price(r, k, Dk):
    """d kappa / d c_r  (one more child of rank r, mass not held fixed) = -(r/73)^(1-k) / dM/dk."""
    return -(D(r) / D(M_DIM) * (k * (D(M_DIM) / D(r)).ln()).exp()) / Dk

def mass(prof): return sum(r * c for r, c in prof.items())

def apply(prof, delta):
    out = collections.Counter({r: c for r, c in prof.items()})
    for r, d in delta.items(): out[r] += d
    assert all(v >= 0 for v in out.values()), (prof, delta)
    return {r: c for r, c in out.items() if c}

def fmt(x, n=12): return f'{float(x):+.{n - 7}e}' if isinstance(x, D) else str(x)

# ---------------------------------------------------------------- climb strings
def dim(f): return 0 if f in (None, []) else len(f)

def climb_strings(word, end_full=9):
    """Per-register climb string over the forward sections A, cut, B.

    Rules (all read from the word): a register's frame timeline is the list of dims of the frames of the gates it
    touches (target or source), skipping unpaid (dim-0) incidences; it starts at dim(start_extra) (0 if absent) and,
    for helper registers (224..703, not removed), ends at dim(helper_final) or at the full dim 9.  Centres are one
    rank-8 child each (their centre_frames).  Positive differences are the paid children (ranks)."""
    tl = collections.defaultdict(list)
    for s in ('A', 'cut', 'B'):
        for g in word[s]:
            d = dim(g[-1])
            if d == 0: continue
            regs = [g[1]] if g[0] == 'scale' else [g[1], g[2]]
            for r in regs: tl[r].append(d)
    start = {int(k): len(v) for k, v in word['start_extra'].items()}
    final = {int(k): len(v) for k, v in word['helper_final'].items()}
    removed = set(word['removed'])
    out = {}
    for r, seq in tl.items():
        prev = start.get(r, 0); js = []
        for d in seq:
            if d > prev: js.append(d - prev); prev = d
        if 224 <= r < 704 and r not in removed:
            end = final.get(r, end_full)
            if end > prev: js.append(end - prev)
        out[r] = tuple(js)
    for c, f in zip(word['centers'], word['center_frames']):
        out[('centre', c)] = (len(f),)
    return out

def parikh(cs):
    h = collections.Counter()
    for js in cs.values():
        for j in js: h[j] += 1
    return dict(sorted(h.items()))

# ---------------------------------------------------------------- main
def main():
    w2802 = json.load(gzip.open(PKG + 'inputs/WORD-base.json.gz'))
    w2751 = json.load(gzip.open(PKG + 'inputs/WORD2751-base.json.gz'))
    prof = {int(k): v for k, v in json.load(open(PKG + 'PROFILE.json')).items()}
    idle = {1: 17316, 3: 6594, 5: 9878, 32: 1, 48: 26558}
    local = {r: (prof[r] - idle.get(r, 0)) // N_CALLS for r in prof if prof[r] != idle.get(r, 0)}
    print('# 1. climb strings vs reported local profile')
    for name, w in (('2751', w2751), ('2802', w2802)):
        cs = climb_strings(w); h = parikh(cs); rep = {int(k): v for k, v in w['report']['local_profile'].items()}
        helpers = [r for r in cs if isinstance(r, int) and 224 <= r < 704]
        widths = collections.Counter(sum(cs[r]) for r in helpers)
        print(f'word {name}: climb histogram {h} mass {sum(k*v for k,v in h.items())}; reported {rep} mass {mass(rep)};'
              f' match={h == rep}; helpers {len(helpers)} width inventory {dict(sorted(widths.items()))}')
        ports = [r for r in cs if isinstance(r, int) and r < 224 and r not in w['centers']]
        pm = collections.Counter(sum(cs[r]) for r in ports)
        print(f'   non-helper, non-centre registers: {len(ports)}; climb-sum histogram {dict(sorted(pm.items()))}')
    print(f'complete-profile decomposition: local {local} x666 + idle {idle}; mass {mass(prof)}'
          f' = 72*{W_LIVE} + 64*{N_CALLS} = {72*W_LIVE + 64*N_CALLS}')
    print('\n# 2. register-level Parikh derivation #2751 -> #2802 (forward sections)')
    a, b = climb_strings(w2751), climb_strings(w2802)
    changed = sorted(set(a) | set(b), key=str)
    dloc = collections.Counter()
    for r in changed:
        if a.get(r) != b.get(r):
            print(f'   reg {r}: {a.get(r)} -> {b.get(r)}')
            for j in a.get(r, ()): dloc[j] -= 1
            for j in b.get(r, ()): dloc[j] += 1
    dloc = {k: v for k, v in sorted(dloc.items()) if v}
    print(f'   local Parikh delta per call {dloc} (mass {sum(k*v for k,v in dloc.items())});'
          f' reported delta {{1:-4,2:+6,3:-6}} mass -10; idle delta {{5:+1332}} = +10/call')

    print('\n# 3. root, derivative and the linear price table')
    k = root(prof); Dk = dM_dk(prof, k)
    print(f'   root kappa = {str(k)[:30]}  (certified endpoint {CERT}; agree to {abs(k-CERT) < D("1e-23")})')
    print(f'   M(0) = mass/73 = {float(moment(prof, D(0))):.3f} < 66304 (root exists iff mass < 73*66304 = {73*W_LIVE})')
    print(f'   dM/dkappa at root = {float(Dk):.6f}')
    pr = {r: price(r, k, Dk) for r in (1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 32, 48, 51, 73)}
    print('   price(r) = dkappa per ADDED rank-r child (mass not fixed); price per unit mass = price(r)/r')
    for r, p in pr.items(): print(f'     r={r:2d}  price {fmt(p)}   per unit mass {fmt(p / r)}')
    print('   mass-fixed merge gain  g(r1,r2) = kappa(c - e_r1 - e_r2 + e_(r1+r2)) - kappa(c)  (exact, one child):')
    lam = k / (D(M_DIM) * Dk)
    print(f'   first-order law for mass-neutral deltas: dkappa ~ (kappa/(73 dM/dk)) * dPhi, Phi(c) = sum_r r c_r ln r;'
          f' kappa/(73 dM/dk) = {float(lam):.6e} per unit of Phi')
    for r1, r2 in ((1, 1), (1, 2), (2, 2), (4, 4), (3, 5), (8, 8), (48, 3)):
        d = collections.Counter(); d[r1] -= 1; d[r2] -= 1; d[r1 + r2] += 1
        ex = root(apply(prof, dict(d))) - k
        lin = sum(D(v) * price(r, k, Dk) for r, v in d.items())
        phi = sum(D(r * v) * D(r).ln() for r, v in d.items())
        print(f'     ({r1},{r2})->{r1+r2}: exact {fmt(ex)}  linear(price) {fmt(lin)}  log-rank law {fmt(lam * phi)}')

    print('\n# 4. unit Parikh moves on the real #2802 profile (exact roots; x666 = once per call)')
    moves = {
        'merge two rank-4 -> rank-8, once per call':           {4: -2 * N_CALLS, 8: +N_CALLS},
        'split one idle 48 -> 32+16':                          {48: -1, 32: +1, 16: +1},
        'split one idle 48 -> 6 x 8':                          {48: -1, 8: +6},
        'split one idle 48 -> 48 x 1':                         {48: -1, 1: +48},
        'merge idle 48+3 -> 51 (halving guard max), once':     {48: -1, 3: -1, 51: +1},
        'merge idle 48+3 -> 51, all 6594 rank-3 idles':        {48: -6594, 3: -6594, 51: +6594},
        'refit PR2766 kind: {1:-2,2:+1} per call':             {1: -2 * N_CALLS, 2: +N_CALLS},
        'remove width-8 helper (1,1,1,1,1,1,1,1) -> one rank-8 idle, per call':
            {1: -8 * N_CALLS, 8: +N_CALLS},
        'remove width-8 helper (1,2,2,3) -> one rank-8 idle, per call':
            {1: -N_CALLS, 2: -2 * N_CALLS, 3: -N_CALLS, 8: +N_CALLS},
        'remove width-8 helper (1,2,2,3) -> 8 rank-1 idles (worst packing), per call':
            {2: -2 * N_CALLS, 3: -N_CALLS, 1: +7 * N_CALLS},
        'remove width-8 helper (1,2,2,3) -> absorbed in a 48-bin remainder 0->8, per call':
            {1: -N_CALLS, 2: -2 * N_CALLS, 3: -N_CALLS, 8: +N_CALLS},
        'remove width-5 follower (2,1,1,1) -> one rank-5 idle, per call':
            {2: -N_CALLS, 1: -3 * N_CALLS, 5: +N_CALLS},
        'the #2751->#2802 step as recorded: local {1:-4,2:+6,3:-6}/call, idle {5:+1332}':
            {1: -4 * N_CALLS, 2: +6 * N_CALLS, 3: -6 * N_CALLS, 5: +1332},
    }
    moves['cold-host (4,8)->7 "-H3-H2": local {3:-1,2:-1}/call, freed 5 cells as one rank-5 remainder per call'] = \
        {3: -N_CALLS, 2: -N_CALLS, 5: +N_CALLS}
    relax_idle = {1: 16648, 3: 6558, 5: 10381, 39: 1, 48: 26591}   # out/RELAX-host7.json, key "1:-H3-H2"
    loc7 = apply(local, {3: -1, 2: -1})
    prof7 = apply({r: N_CALLS * c for r, c in loc7.items()}, relax_idle)
    moves['cold-host "-H3-H2" with the RECORDED relaxed fill (RELAX-host7 idle histogram; reported +8.7032532e-7)'] = \
        {r: prof7.get(r, 0) - prof.get(r, 0) for r in set(prof) | set(prof7)}
    for name, d in moves.items():
        d = {r: v for r, v in d.items() if v}
        if not d:
            print(f'   {name}: identity (mass-neutral, no profile change)'); continue
        newp = apply(prof, d)
        dm = mass(newp) - mass(prof)
        phi = sum(D(r * v) * D(r).ln() for r, v in d.items())
        print(f'   {name}: dkappa {fmt(root(newp) - k)}  (mass change {dm:+d}; log-rank law {fmt(lam * phi)})')

    print('\n# 5. ceiling ladder (each row: a relaxation of the reachable set; roots by the same bisection)')
    idle_mass = sum(r * c for r, c in idle.items())
    local_mass = mass(local)
    rows = {
        'A. actual #2802': prof,
        'B. idle mass all in rank-48 children (integral count rounded down, rest rank-1)':
            apply({r: N_CALLS * c for r, c in local.items()}, {48: idle_mass // 48, 1: idle_mass % 48}),
        'C. idle mass all in rank-51 children (packing cap of packing_cap.py, fractional allowed here as 51*x)':
            None,
        'D. local helper mass (3332/call) + idle all at rank 51; ports/centres fixed':
            None,
        'E. all local children merged to rank 9 (h=9 bound) + idle at 51':
            None,
        'F. everything at rank 73 (no root: M(k)=mass/73 for all k)': None,
        'G. uniform manuscript model: every unit of mass a rank-1 child (kappa = log_73(73 W / mass))': {1: mass(prof)},
    }
    print(f'   local mass/call {local_mass}; idle mass/call {idle_mass // N_CALLS} (= 7232 - {local_mass}); helpers 3332 + centres 64 + ports 1792 = 5188')
    for name, p in rows.items():
        if p is not None:
            print(f'   {name}: kappa {str(root(p))[:22]}  (delta vs actual {fmt(root(p) - k)})')
    # fractional rows: use Decimal counts directly in moment()
    def root_frac(p):
        return root(p)
    pc = {r: D(N_CALLS * c) for r, c in local.items()}; pc[51] = D(idle_mass) / D(51)
    print(f'   C. idle -> fractional rank-51: kappa {str(root_frac(pc))[:22]}  (packing_cap.py reports ~0.00175808593463)')
    pd_ = {r: D(N_CALLS * c) for r, c in local.items()}
    # remove helper climbs: keep ports (112 x 16 units as actual children?) - we only know ports+centres mass 1856/call;
    # relax: ports/centres children kept as the actual local children of the centre/port registers is not separable here,
    # so bound it by moving ALL helper mass (3332/call) out of ranks <=5 proportionally: show the cruder bound instead.
    pdx = {51: (D(idle_mass) + D(3332 * N_CALLS)) / D(51), 8: D(8 * N_CALLS)}
    pdx[9] = D(1792 * N_CALLS) / D(9)
    print(f'   D. helper mass + idle at rank 51, ports at rank 9, centres 8: kappa {str(root_frac(pdx))[:22]}')
    pe = {9: D(local_mass * N_CALLS) / D(9), 51: D(idle_mass) / D(51)}
    print(f'   E. local at rank 9 + idle at 51: kappa {str(root_frac(pe))[:22]}')
    print(f'   F. all at 73: M = {float(moment({73: D(mass(prof)) / D(73)}, D(0))):.1f} < 66304 at every kappa -> no root (needs r<=51 guard / r<=9 frames)')
    print(f'   G check: log_73(73*66304/mass) = {float((D(73*W_LIVE)/D(mass(prof))).ln()/D(73).ln()):.9f}')

    print('\n# 6a. lineage as a Parikh derivation with complete profiles (exact roots vs the log-rank law)')
    P2751 = {1: 1593072, 2: 430236, 3: 204396, 4: 79920, 5: 22532, 8: 5328, 32: 1, 48: 26558}
    P2766 = {1: 1591740, 2: 430902, 3: 204396, 4: 79920, 5: 22532, 8: 5328, 32: 1, 48: 26558}
    PR5 = {1: 1606392, 2: 427572, 3: 189078, 4: 85248, 5: 25862, 8: 5328, 32: 1, 48: 26558}
    chain = [('#2751', P2751), ('#2766 refit', P2766), ('retired5 (5 aliases)', PR5), ('#2802 (2 moves + 2 aliases)', prof)]
    for (na, pa), (nb, pb) in zip(chain, chain[1:]):
        ka, kb = root(pa), root(pb)
        d = {r: pb.get(r, 0) - pa.get(r, 0) for r in set(pa) | set(pb) if pb.get(r, 0) != pa.get(r, 0)}
        phi = sum(D(r * v) * D(r).ln() for r, v in d.items())
        print(f'   {na} -> {nb}: delta {dict(sorted(d.items()))} mass {sum(r*v for r,v in d.items()):+d};'
              f' exact dkappa {fmt(kb - ka)}  log-rank law {fmt(lam * phi)}  Phi/call {float(phi)/N_CALLS:+.3f}')
    wr5 = json.load(gzip.open(str(_ROOT / 'research/styles-r11/data/words/retired5-WORD-base.json.gz')))
    c1, c5, c7 = climb_strings(w2751), climb_strings(wr5), climb_strings(w2802)
    for (na, ca), (nb, cb) in ((('#2751', c1), ('retired5', c5)), (('retired5', c5), ('#2802', c7))):
        ch = [r for r in set(ca) | set(cb) if ca.get(r) != cb.get(r)]
        dl = collections.Counter()
        for r in ch:
            for j in ca.get(r, ()): dl[j] -= 1
            for j in cb.get(r, ()): dl[j] += 1
        print(f'   climb-string diff {na} -> {nb}: {len(ch)} registers changed, local Parikh delta/call {dict(sorted((k, v) for k, v in dl.items() if v))}')
    print('   centre registers gate-climbs (diagnostic for the fixed offset):',
          {c: c7.get(c) for c in w2802['centers']})
    print('   target_levels registers gate-climbs:', {int(t): c7.get(int(t)) for t in w2802['target_levels']})
    print('\n# 6b. lineage kappa steps (values from CLAIM.json / README / digest)')
    lineage = [('#2751 joint twelve-source', D('0.001717141586348426338109')),
               ('#2766 refit B1151 6->5 (per call {1:-2,2:+1})', D('0.001717256973467002308270')),
               ('retired5: five retired-lender aliases', D('0.001717409316335491643448')),
               ('#2802: two hostee moves + two aliases + refits', CERT),
               ('#2843 T124 composition (other machine)', D('0.00171865827784172')),
               ('#2853 philippeVV dirt-entry A-phase', D('0.0017193776587'))]
    prev = None
    for name, v in lineage:
        print(f'   {name}: {v}  step {fmt(v - prev) if prev is not None else "-"}')
        prev = v
    print('   ceilings: PR2679 ceil74 class-level (every fill of the 415-helper inventory) 0.00171514043461 -- exceeded by #2751 onwards (inventory left the class);'
          ' packing cap (fixed #2802 local word, idle at <=51) 0.001758086 -- not exceeded by any PR on this word.')

if __name__ == '__main__':
    main()
