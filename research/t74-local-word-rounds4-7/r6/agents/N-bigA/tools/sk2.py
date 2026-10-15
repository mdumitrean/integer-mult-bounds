"""sk2.py: residual-repair (second-order) split-key compensation search for helper-donor kernels (agent B-interact, r3).

Round model on a current word W (base word with deletions plus earlier-round inserts):
  target  T = base map - map(W), exact rationals, on the final rows (after A+cut+B+early tails) and on the port rows
          V..2V-1 of the A.cut.B map (the derived compensation reads them);
  insert  x += (l/2) y at a position where y's value lies in span(basis);  first-order effect (l/2) col_x(p) (x) val_y(p);
  basis   a basis of span(residual values + key family);  per-basis column equations as in PR2142 skkernel.py.
Ban modes for inserts of one round: 'none' (round 1 may interact; the residual goes to round 2), 'direct' (PR2142's
rule), 'exact' (lazy cuts on pairs whose interaction really occurs).  Every solution is checked exactly (rational maps)
and priced with exact optimal frames.  Builds on PR2142 (Ian Libanio) skkernel.py and PR1957 (Rohan Arun) tools.
"""
import json, math, os, sys, time
from collections import defaultdict
from fractions import Fraction as Q
from pathlib import Path
HERE = Path(__file__).resolve().parent
WORK = HERE.parent / 'work' / 'research'
sys.path.insert(0, str(WORK / 't74-k554-local-exhaustion' / 'tools'))
import _paths  # noqa: F401  (vendored PR1186 toolkit + PR1957 tools on sys.path)
import harness as H, frames as F
from word import inline
from writeback import write_back
from akernel import Orc, norm, coef
from abkernel import compile_AB, fullseq
from model import cone_caps
from ortools.sat.python import cp_model
V = 112

def sec_sizes(w): return len(w['A']), len(w['cut']), len(w['B'])

def maps(w):
    """exact final rows and A.cut.B port rows: {reg: {init_reg: Q}} (identity rows omitted)."""
    NA, NC, NB = sec_sizes(w); seq = fullseq(w); rows = {}; bt = None
    get = lambda x: rows.get(x, {x: Q(1)})
    for i, g in enumerate(seq):
        if i == NA + NC + NB: bt = {x: dict(rows[x]) for x in rows if V <= x < 2 * V}
        t = g[1]
        if g[0] == 'add':
            a = dict(get(t)); c = coef(g)
            for k, v in get(g[2]).items():
                a[k] = a.get(k, 0) + c * v
                if not a[k]: del a[k]
        else: a = {k: v * coef(g) for k, v in get(t).items()}
        rows[t] = a
    if bt is None: bt = {x: dict(rows[x]) for x in rows if V <= x < 2 * V}
    return rows, bt

def diff(base, cur):
    """base - cur per register row, nonzero entries only."""
    out = {}
    for x in set(base) | set(cur):
        b = base.get(x, {x: Q(1)}); c = cur.get(x, {x: Q(1)}); d = {}
        for k in set(b) | set(c):
            v = b.get(k, 0) - c.get(k, 0)
            if v: d[k] = v
        if d: out[x] = d
    return out

class Basis:
    def __init__(self): self.piv = []
    def reduce(self, v):
        v = dict(v); co = {}
        for bi, (pk, pv) in enumerate(self.piv):
            if v.get(pk):
                f = v[pk] / pv[pk]; co[bi] = co.get(bi, 0) + f
                for k, x in pv.items():
                    v[k] = v.get(k, 0) - f * x
                    if not v[k]: del v[k]
        return v, co
    def add(self, v):
        r, _ = self.reduce(v)
        if r: self.piv.append((min(r), r)); return True
        return False
    def coords(self, v):
        r, co = self.reduce(v)
        return None if r else {b: c for b, c in co.items() if c}

def word_seq_insert(W, ins):
    """ins: list of (seqpos, gate) on W; returns compile_AB edit (section-relative, tails sequential)."""
    NA, NC, NB = sec_sizes(W); ed = dict(delete=[], insert=[], tail=[]); tails = []
    for k, (p, g) in enumerate(ins):
        if p < NA: ed['insert'].append(('A', p, g))
        elif p < NA + NC: raise ValueError('insert inside cut')
        elif p < NA + NC + NB: ed['insert'].append(('B', p - NA - NC, g))
        else: tails.append((p - NA - NC - NB, k, g))
    for m, (j, k, g) in enumerate(sorted(tails)): ed['tail'].append((j + m, g))
    return ed

def hist_values(seq, nreg):
    """per register: list of (start_pos, end_pos, value) windows (value = exact row dict held on [start, end))."""
    rows = {}; get = lambda x: rows.get(x, {x: Q(1)}); start = {x: 0 for x in range(nreg)}; win = defaultdict(list)
    for i, g in enumerate(seq):
        t = g[1]
        if g[0] == 'add':
            a = dict(get(t)); c = coef(g)
            for k, v in get(g[2]).items():
                a[k] = a.get(k, 0) + c * v
                if not a[k]: del a[k]
        else: a = {k: v * coef(g) for k, v in get(t).items()}
        win[t].append((start[t], i + 1, get(t))); rows[t] = a; start[t] = i + 1
    L = len(seq)
    for x in range(nreg): win[x].append((start[x], L + 1, get(x)))
    return win

def family_values(seq, regs, nreg, depth=1):
    """values held by or added into the given registers (PR2142 family); depth 2 also recurses through every register
    added into them."""
    rows = {}; get = lambda x: rows.get(x, {x: Q(1)}); held = defaultdict(list); added_from = defaultdict(set)
    for x in range(nreg): held[x].append({x: Q(1)})
    addin = defaultdict(list)
    for i, g in enumerate(seq):
        t = g[1]
        if g[0] == 'add':
            addin[t].append(dict(get(g[2]))); added_from[t].add(g[2])
            a = dict(get(t)); c = coef(g)
            for k, v in get(g[2]).items():
                a[k] = a.get(k, 0) + c * v
                if not a[k]: del a[k]
        else: a = {k: v * coef(g) for k, v in get(t).items()}
        rows[t] = a; held[t].append(dict(a))
    regs = set(regs); level = set(regs)
    for _ in range(depth - 1):
        level = {s for r in level for s in added_from[r]} - regs; regs |= level
    vals = []
    for r in sorted(regs): vals += held[r] + addin[r]
    return vals, sorted(regs)

def cones(seq, pairs):
    """for each (y, p): {r: q} = latest gate index q < p at which register r's content flows into y at p (y: p)."""
    out = {}
    for (y, p) in pairs:
        q = {y: p}
        for i in range(p - 1, -1, -1):
            g = seq[i]
            if g[0] == 'add' and g[1] in q and g[2] not in q: q[g[2]] = i
        out[(y, p)] = q
    return out

class Round:
    def __init__(self, P, W, base_maps, orc_word, orc_shift, fam_vals, cap_mult=1.0, budget=None, orc_secs=None):
        self.P, self.W = P, W; self.orc_secs = orc_secs
        self.NA, self.NC, self.NB = sec_sizes(W); self.seq = fullseq(W); self.L = len(self.seq)
        self.nreg = max(2 * V + W['report']['R'], 1 + max(max(g[1], g[2] if g[0] == 'add' else 0) for g in self.seq))
        cur = maps(W); self.TF = diff(base_maps[0], cur[0]); self.TB = diff(base_maps[1], cur[1])
        self.basis = Basis()
        for row in list(self.TF.values()) + list(self.TB.values()): self.basis.add(row)
        self.nT = len(self.basis.piv)
        for v in fam_vals: self.basis.add(v)
        self.orc, self.orc_shift, self.cap_mult, self.bud = orc_word, orc_shift, cap_mult, budget
    def orcpos(self, i):
        """seq insertion point i of W -> oracle timeline position (oracle word = W minus earlier-round inserts)."""
        j = self.orc_shift(i)
        if j is None: return None
        NA, NC, NB = self.orc_secs
        if j < NA: return j
        if j < NA + NC: return None
        return j - NC
    def candidates(self):
        seq, L, nreg = self.seq, self.L, self.nreg
        win = hist_values(seq, nreg); hold = defaultdict(list)
        for y, ws in win.items():
            for a, b, val in ws:
                if not val: continue
                co = self.basis.coords(val)
                if not co: continue
                for p in range(a, min(b, L + 1)): hold[p].append((y, co))
        colsF, colsB = {}, {}; SF = lambda x: colsF.get(x, {x: Q(1)}); SB = lambda x: colsB.get(x, {x: Q(1)})
        def step(cols, Sf, g):
            if g[0] == 'add':
                t, s = g[1], g[2]; c = coef(g); a = dict(Sf(s))
                for k, vv in Sf(t).items():
                    a[k] = a.get(k, 0) + c * vv
                    if not a[k]: del a[k]
                cols[s] = a
            else:
                x = g[1]; cols[x] = {k: vv * coef(g) for k, vv in Sf(x).items()}
        NAB = self.NA + self.NC + self.NB; seen = {}; cand = []
        for i in range(L, -1, -1):
            g = seq[i] if i < L else None
            if g is not None:
                step(colsF, SF, g)
                if i < NAB: step(colsB, SB, g)
            if i not in hold: continue
            op = self.orcpos(i)
            if op is None: continue
            inAB = i < NAB
            for y, co in hold[i]:
                for x in range(nreg):
                    if x == y or (V <= y < 2 * V and not (V <= x < 2 * V)): continue
                    cst = self.orc.cost(x, y, op)
                    if self.bud is not None and cst > self.cap_mult * self.bud: continue
                    lu = getattr(self, 'lu', None)
                    if lu is not None and not lu.ok(x, y, i): self.cone_rejected = getattr(self, 'cone_rejected', 0) + 1; continue
                    vf = SF(x); vb = {k: vv for k, vv in SB(x).items() if V <= k < 2 * V} if inAB else {}
                    kk = (x, tuple(sorted(co.items())), tuple(sorted(vf.items())), tuple(sorted(vb.items())))
                    if kk in seen and cand[seen[kk]][5] <= cst: continue
                    c_ = (x, y, i, co, (vf, vb), cst)
                    if kk in seen: cand[seen[kk]] = c_
                    else: seen[kk] = len(cand); cand.append(c_)
        self.cand = cand; return cand
    def model(self, maxterms, lamr=8, ban='none', extra_cuts=(), lam_den=2):
        cand = self.cand; eqs = defaultdict(list); rhs = {}; self.lam_den = D = lam_den
        for j, (x, y, i, co, (vf, vb), cst) in enumerate(cand):
            for b, cb in co.items():
                for rr, val in vf.items(): eqs[(b, 'F', rr)].append((j, cb * val))
                for rr, val in vb.items(): eqs[(b, 'B', rr)].append((j, cb * val))
        for tag, T in (('F', self.TF), ('B', self.TB)):
            for rr, row in T.items():
                co = self.basis.coords(row)
                assert co is not None
                for b, cb in co.items(): rhs[(b, tag, rr)] = cb
        keys = set(eqs) | set(rhs)
        self.shape = all(k in eqs for k, v in rhs.items() if v)
        lcm = 1
        for k in keys:
            for _, val in eqs.get(k, []): lcm = lcm * Q(val).denominator // math.gcd(lcm, Q(val).denominator)
            q = Q(rhs.get(k, 0)).denominator; lcm = lcm * q // math.gcd(lcm, q)
        SC = D * lcm; m = cp_model.CpModel(); lam, z = [], []
        for j in range(len(cand)):
            l = m.NewIntVar(-lamr, lamr, ''); b = m.NewBoolVar('')
            m.Add(l == 0).OnlyEnforceIf(b.Not()); m.Add(l != 0).OnlyEnforceIf(b); lam.append(l); z.append(b)
        for k in keys:
            terms = [lam[j] * int(Q(val) * SC) for j, val in eqs.get(k, [])]; r_ = Q(rhs.get(k, 0)) * D * SC
            assert r_.denominator == 1
            if not terms:
                if r_: m.AddBoolOr([])  # unsatisfiable row
                continue
            m.Add(sum(terms) == int(r_))
        if ban == 'direct':
            byx = defaultdict(list)
            for j, c_ in enumerate(cand): byx[c_[0]].append(j)
            for j2, c2 in enumerate(cand):
                ws = [z[j1] for j1 in byx.get(c2[1], []) if cand[j1][2] <= c2[2]]
                if ws: m.Add(sum(ws) == 0).OnlyEnforceIf(z[j2])
        for cut in extra_cuts: m.Add(sum(z[j] for j in cut) <= len(cut) - 1)
        m.Add(sum(z) <= maxterms)
        if self.bud is not None and not getattr(self, 'nobud', False): m.Add(sum(z[j] * cand[j][5] for j in range(len(cand))) <= self.bud)
        m.Minimize(sum(z[j] * (cand[j][5] + 50) for j in range(len(cand))))
        self.m, self.lam, self.z = m, lam, z
        return m
    def solve(self, tl, workers=None):
        workers = workers or int(os.environ.get('SK2_WORKERS', '1'))
        s = cp_model.CpSolver(); s.parameters.max_time_in_seconds = tl; s.parameters.num_workers = workers
        st = s.Solve(self.m)
        if st not in (cp_model.OPTIMAL, cp_model.FEASIBLE): return s.StatusName(st), None
        supp = [j for j in range(len(self.cand)) if s.Value(self.z[j])]
        sol = [(j, Q(s.Value(self.lam[j]), self.lam_den)) for j in supp]
        self.m.Add(sum(self.z[j] for j in supp) <= len(supp) - 1)   # next call: a different support
        return s.StatusName(st), sol
    def interacting_pairs(self, sol):
        """pairs (j1, j2) of a solution whose interaction really occurs (x1's content after p1 flows into y2 at p2)."""
        items = [(self.cand[j][2], k, j) for k, (j, l) in enumerate(sol)]; out = []
        cn = cones(self.seq, {(self.cand[j][1], self.cand[j][2]) for j, _ in sol})
        for p2, k2, j2 in items:
            y2 = self.cand[j2][1]; q = cn[(y2, p2)]
            for p1, k1, j1 in items:
                if j1 == j2: continue
                x1 = self.cand[j1][0]
                if (p1 < p2 or (p1 == p2 and k1 < k2)) and q.get(x1, -1) >= p1: out.append((j1, j2))
        return out
    def apply(self, sol):
        ins = sorted(((self.cand[j][2], k, ['add', self.cand[j][0], self.cand[j][1], l.numerator, l.denominator, []])
                      for k, (j, l) in enumerate(sol)), key=lambda t: (t[0], t[1]))
        ed = word_seq_insert(self.W, [(p, g) for p, _, g in ins]); self.last_order = [k for _, k, _ in ins]
        return compile_AB(self.W, ed), [(p, g) for p, _, g in ins]

def price_word(P, w1, base_comp, timeout=300):
    """exact optimal frames of a (map-exact) word; derived compensation must equal the base word's."""
    from compat_shim import deadline, Timeout
    try:
        with deadline(timeout):
            caps, comp = cone_caps(w1)
            if [list(e[:5]) for e in comp] != base_comp: return dict(status='compensation-changed')
            ent = set(map(int, w1['start_extra'])); low = set(map(int, w1['helper_final']))
            if any(e[2] in ent | low for e in comp): return dict(status='compensation-touches-residual')
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=g)
    except F.Infeasible: return dict(status='infeasible')
    except Timeout: return dict(status='timeout')
    except Exception as e: return dict(status='err:' + repr(e)[:100])
    return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - P.base_cost,
                profile=dict(sorted(r['profile'].items())), graph=g, assign=r['assign'])
