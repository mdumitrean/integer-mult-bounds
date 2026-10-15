"""sk3.py: projected (compensation-aware) split-key kernel model, agent D-compsplit r5.  Extends r3 agent B's sk2.Round
(itself a refactoring of PR2142 / Ian Libanio's skkernel.py, which builds on PR1957 / Rohan Arun's abkernel.py).

Target T = base map - map(W) on the final rows (A-start coordinates).  The derived compensation cancels every entry
(port row, ORDINARY helper column), so those entries are projected out:
  non-port rows: full equality   sum_j lam_j colN_j (x) key_j       = TN
  port rows:     projected       sum_j lam_j colP_j (x) pi(key_j)   = pi(TP)
with one basis for the full keys (span of TN rows + key family) and one for projected keys (span of pi(TP rows) +
pi(key family)).  Inserts x += lam y may write ANY register in B or the early tail (no A inserts; no tail insert touching a
port; ports only feed ports); y's value must have full coordinates if x's column reaches a non-port row and projected
coordinates if it reaches a port row.  Cone-aware admission: r3 B's cone.LU.ok on the round word."""
import math
from collections import defaultdict
from sk2 import (H, F, Q, V, Round, Orc, compile_AB, cone_caps, diff, family_values, fullseq, inline, maps, sec_sizes,
                 write_back, word_seq_insert, hist_values, Basis, cones, cp_model)

def absorbable(w):
    n = 2 * V + w['report']['R']; ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
    return frozenset(k for k in range(2 * V, n) if k not in ent and k not in low)

def proj(v, ab): return {k: x for k, x in v.items() if k not in ab}
isport = lambda r: V <= r < 2 * V

def split_target(base_maps, W, ab):
    TF = diff(base_maps[0], maps(W)[0]); TN, TP = {}, {}
    for x, r in TF.items():
        if isport(x):
            pr = proj(r, ab)
            if pr: TP[x] = pr
        else: TN[x] = r
    return TN, TP

def exact_proj(base_maps, W, ab):
    TN, TP = split_target(base_maps, W, ab); return not TN and not TP

class PRound(Round):
    def __init__(self, P, W, base_maps, orc_word, orc_shift, fam_vals, cap_mult=1.0, budget=None, orc_secs=None, ab=None):
        self.P, self.W, self.orc_secs, self.ab = P, W, orc_secs, ab
        self.NA, self.NC, self.NB = sec_sizes(W); self.seq = fullseq(W); self.L = len(self.seq)
        self.nreg = max(2 * V + W['report']['R'], 1 + max(max(g[1], g[2] if g[0] == 'add' else 0) for g in self.seq))
        self.TN, self.TP = split_target(base_maps, W, ab)
        self.bN, self.bP = Basis(), Basis()
        for r in self.TN.values(): self.bN.add(r)
        for r in self.TP.values(): self.bP.add(r)
        self.nT = (len(self.bN.piv), len(self.bP.piv))
        for v in fam_vals:
            self.bN.add(v); pv = proj(v, ab)
            if pv: self.bP.add(pv)
        self.basis = self.bN
        self.orc, self.orc_shift, self.cap_mult, self.bud = orc_word, orc_shift, cap_mult, budget
    def candidates(self, first_pos=None, force=()):
        seq, L, nreg, ab = self.seq, self.L, self.nreg, self.ab
        lo = self.NA + self.NC if first_pos is None else first_pos; NAB = self.NA + self.NC + self.NB
        win = hist_values(seq, nreg); hold = defaultdict(list)
        for y, ws in win.items():
            for a, b, val in ws:
                if not val or b <= lo: continue
                coN = self.bN.coords(val); pv = proj(val, ab); coP = self.bP.coords(pv) if pv else None
                if not coN and not coP: continue
                for p in range(max(a, lo), min(b, L + 1)): hold[p].append((y, coN, coP))
        cols = {}; SF = lambda x: cols.get(x, {x: Q(1)}); split = {}
        def step(g):
            if g[0] == 'add':
                t, s = g[1], g[2]; c = Q(g[3], g[4]); a = dict(SF(s))
                for k, vv in SF(t).items():
                    a[k] = a.get(k, 0) + c * vv
                    if not a[k]: del a[k]
                cols[s] = a; split.pop(s, None)
            else:
                x = g[1]; cols[x] = {k: vv * Q(g[2], g[3]) for k, vv in SF(x).items()}; split.pop(x, None)
        def getsplit(x):
            r = split.get(x)
            if r is None:
                vf = SF(x); vN = {k: v for k, v in vf.items() if not isport(k)}; vP = {k: v for k, v in vf.items() if isport(k)}
                r = split[x] = (vN, vP)
            return r
        seen = {}; cand = []; self.cone_rejected = 0; self.cost_rejected = 0
        for i in range(L, lo - 1, -1):
            if i < L: step(seq[i])
            if i not in hold: continue
            op = self.orcpos(i)
            if op is None: continue
            tail = i >= NAB
            for y, coN, coP in hold[i]:
                for x in range(nreg):
                    if x == y or (isport(y) and not isport(x)): continue
                    if tail and (isport(x) or isport(y)): continue
                    vN, vP = getsplit(x)
                    if (vN and not coN) or (vP and not coP): continue
                    if not vN and not vP: continue
                    cst = self.orc.cost(x, y, op)
                    if self.bud is not None and cst > self.cap_mult * self.bud: self.cost_rejected += 1; continue
                    lu = getattr(self, 'lu', None)
                    if lu is not None and not lu.ok(x, y, i): self.cone_rejected += 1; continue
                    kk = (x, tuple(sorted((coN or {}).items())) if vN else (), tuple(sorted((coP or {}).items())) if vP else (),
                          tuple(sorted(vN.items())), tuple(sorted(vP.items())))
                    c_ = (x, y, i, (coN if vN else None, coP if vP else None), (vN, vP), cst)
                    if (x, y, i) in force: cand.append(c_); continue
                    # keep, per effect, the cheapest entries at the latest and at the earliest position of the window
                    js = seen.get(kk)
                    if js is None: seen[kk] = [len(cand)]; cand.append(c_); continue
                    best = cand[js[0]][5]
                    if cst < best:
                        cand[js[0]] = c_
                        if len(js) > 1: cand[js[1]] = None; js.pop()
                    elif cst == best:
                        if len(js) == 1: js.append(len(cand)); cand.append(c_)
                        else: cand[js[1]] = c_
        self.cand = [c for c in cand if c is not None]; return self.cand
    def model(self, maxterms, lamr=16, ban='none', extra_cuts=(), lam_den=4, fix=None):
        cand = self.cand; eqs = defaultdict(list); rhs = {}; self.lam_den = Dn = lam_den
        for j, (x, y, i, (coN, coP), (vN, vP), cst) in enumerate(cand):
            if coN:
                for b, cb in coN.items():
                    for rr, val in vN.items(): eqs[(b, 'N', rr)].append((j, cb * val))
            if coP:
                for b, cb in coP.items():
                    for rr, val in vP.items(): eqs[(b, 'P', rr)].append((j, cb * val))
        for tag, T, B_ in (('N', self.TN, self.bN), ('P', self.TP, self.bP)):
            for rr, row in T.items():
                co = B_.coords(row); assert co is not None
                for b, cb in co.items(): rhs[(b, tag, rr)] = cb
        keys = set(eqs) | set(rhs); self.shape = all(k in eqs for k, v in rhs.items() if v)
        lcm = 1
        for k in keys:
            for _, val in eqs.get(k, []): lcm = lcm * Q(val).denominator // math.gcd(lcm, Q(val).denominator)
            q = Q(rhs.get(k, 0)).denominator; lcm = lcm * q // math.gcd(lcm, q)
        SC = Dn * lcm; m = cp_model.CpModel(); lam, z = [], []
        for j in range(len(cand)):
            l = m.NewIntVar(-lamr, lamr, ''); b = m.NewBoolVar('')
            m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b); lam.append(l); z.append(b)
        for k in keys:
            terms = [lam[j] * int(Q(val) * SC) for j, val in eqs.get(k, [])]; r_ = Q(rhs.get(k, 0)) * Dn * SC
            assert r_.denominator == 1
            if not terms:
                if r_: m.AddBoolOr([])
                continue
            m.Add(sum(terms) == int(r_))
        if ban == 'direct':
            byx = defaultdict(list)
            for j, c_ in enumerate(cand): byx[c_[0]].append(j)
            for j2, c2 in enumerate(cand):
                ws = [z[j1] for j1 in byx.get(c2[1], []) if cand[j1][2] <= c2[2]]
                if ws: m.Add(sum(ws) == 0).OnlyEnforceIf(z[j2])
        for cut in extra_cuts: m.Add(sum(z[j] for j in cut) <= len(cut) - 1)
        if fix:
            for j, l in fix: m.Add(lam[j] == int(l * Dn))
        m.Add(sum(z) <= maxterms)
        if self.bud is not None and not getattr(self, 'nobud', False): m.Add(sum(z[j] * cand[j][5] for j in range(len(cand))) <= self.bud)
        m.Minimize(sum(z[j] * (cand[j][5] + 50) for j in range(len(cand))))
        self.m, self.lam, self.z = m, lam, z; self.neqs = len(keys)
        return m

def to_base_edit(base, dels, W1, ins):
    """inserts [(W1 seq pos, gate)] (sorted as applied) + B deletions -> rev3 harness.compile_edits edit on the BASE word."""
    if any(s != 'B' for s, i in dels): raise ValueError('A deletion: rev3 compile_edits cannot express it (use absorb.compile_full)')
    NA, NC, NB = len(W1['A']), len(W1['cut']), len(W1['B']); dB = sorted(i for s, i in dels if s == 'B')
    surv = [i for i in range(len(base['B'])) if i not in set(dB)]; ed = dict(delete=dB, insert=[], tail=[]); tails = []
    for k, (p, g) in enumerate(ins):
        if p < NA + NC: raise ValueError('A/cut insert not supported')
        q = p - NA - NC
        if q < NB: ed['insert'].append([surv[q] if q < len(surv) else len(base['B']), list(g)])
        else: tails.append((q - NB, k, list(g)))
    for m, (j, k, g) in enumerate(sorted(tails)): ed['tail'].append([j + m, g])
    return ed

def to_base_edit_ab(base, dels, W1, ins):
    """section-tagged edit (absorb.compile_ab) on the BASE word: deletions in A or B, inserts in B, tails."""
    NA, NC, NB = len(W1['A']), len(W1['cut']), len(W1['B']); dB = sorted(i for s, i in dels if s == 'B')
    surv = [i for i in range(len(base['B'])) if i not in set(dB)]; ed = dict(delete=[[s, i] for s, i in dels], insert=[], tail=[]); tails = []
    for k, (p, g) in enumerate(ins):
        if p < NA + NC: raise ValueError('A/cut insert not supported')
        q = p - NA - NC
        if q < NB: ed['insert'].append(['B', surv[q] if q < len(surv) else len(base['B']), list(g)])
        else: tails.append((q - NB, k, list(g)))
    for m, (j, k, g) in enumerate(sorted(tails)): ed['tail'].append([j + m, g])
    return ed
