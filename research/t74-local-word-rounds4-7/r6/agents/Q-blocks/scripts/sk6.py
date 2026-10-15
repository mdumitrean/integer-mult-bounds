"""sk6.py (agent Q-blocks, r6): agent G-ainsert's sk4.PRound4 (A-window + B/tail inserts; itself extending r5 D-compsplit's
sk3 projected split-key model, r3 B's sk2, PR2142 Ian Libanio's skkernel.py and PR1957 Rohan Arun's abkernel.py) with agent
M-bigB's sentinel rule: an insert the #1957 oracle prices at its 2^60 sentinel is never pruned by cost; if it passes the exact
single-insert cone test it is kept at cost 0 (optimistic), so INFEASIBLE stays a proof within the model."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'N-bigA', 'tools'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..', 'r5', 'agents', 'D-compsplit', 'tools'))

from collections import defaultdict
from sk3 import (H, F, Q, V, PRound, Orc, compile_AB, family_values, fullseq, inline, maps, sec_sizes, write_back,
                 word_seq_insert, absorbable, exact_proj, hist_values, proj, isport)

SENT = 1 << 59

class PRound6(PRound):
    a_windows = ()          # list of (lo, hi) seq positions inside A (W coordinates); empty = no A inserts
    def candidates(self, first_pos=None, force=()):
        seq, L, nreg, ab = self.seq, self.L, self.nreg, self.ab
        NA, NC = self.NA, self.NC; NAB = NA + NC + self.NB
        lo = min([a for a, b in self.a_windows] + [NA + NC])
        inA = lambda i: any(a <= i < b for a, b in self.a_windows)
        win = hist_values(seq, nreg); hold = defaultdict(list)
        for y, ws in win.items():
            for a, b, val in ws:
                if not val or b <= lo: continue
                coN = self.bN.coords(val); pv = proj(val, ab); coP = self.bP.coords(pv) if pv else None
                if not coN and not coP: continue
                for p in range(max(a, lo), min(b, L + 1)):
                    if p >= NA + NC or inA(p): hold[p].append((y, coN, coP))
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
        seen = {}; cand = []; self.cone_rejected = 0; self.cost_rejected = 0; self.a_cands = 0; self.sentinel_kept = 0
        for i in range(L, lo - 1, -1):
            if i < L: step(seq[i])
            if i not in hold: continue
            op = self.orcpos(i)
            if op is None: continue
            tail = i >= NAB; posA = i < NA
            for y, coN, coP in hold[i]:
                if posA and isport(y): continue
                for x in range(nreg):
                    if x == y or (isport(y) and not isport(x)): continue
                    if (tail or posA) and (isport(x) or isport(y)): continue
                    vN, vP = getsplit(x)
                    if (vN and not coN) or (vP and not coP): continue
                    if not vN and not vP: continue
                    cst = self.orc.cost(x, y, op); sentinel = cst >= SENT
                    if not sentinel and self.bud is not None and cst > self.cap_mult * self.bud: self.cost_rejected += 1; continue
                    if sentinel and getattr(self, 'drop_sentinels', False): self.sentinel_dropped = getattr(self, 'sentinel_dropped', 0) + 1; continue
                    lu = getattr(self, 'lu', None)
                    if lu is not None and not lu.ok(x, y, i): self.cone_rejected += 1; continue
                    if sentinel:
                        cand.append((x, y, i, (coN if vN else None, coP if vP else None), (vN, vP), 0)); self.sentinel_kept += 1
                        if posA: self.a_cands += 1
                        continue
                    kk = (x, tuple(sorted((coN or {}).items())) if vN else (), tuple(sorted((coP or {}).items())) if vP else (),
                          tuple(sorted(vN.items())), tuple(sorted(vP.items())))
                    c_ = (x, y, i, (coN if vN else None, coP if vP else None), (vN, vP), cst)
                    if posA: self.a_cands += 1
                    if (x, y, i) in force: cand.append(c_); continue
                    js = seen.get(kk)
                    if js is None: seen[kk] = [len(cand)]; cand.append(c_); continue
                    best = cand[js[0]][5]
                    if cst < best:
                        cand[js[0]] = c_
                        if len(js) > 1: cand[js[1]] = None; js.pop()
                    elif cst == best:
                        if len(js) == 1: js.append(len(cand)); cand.append(c_)
                        else: cand[js[1]] = c_
        self.cand = [c for c in cand if c is not None]
        self.a_kept = sum(1 for c in self.cand if c[2] < NA)
        return self.cand

def to_base_edit_ab4(base, dels, W1, ins):
    """section-tagged edit (absorb.compile_ab) on the BASE word: deletions in A or B; inserts in A, B; tails."""
    NA1, NC, NB1 = len(W1['A']), len(W1['cut']), len(W1['B'])
    dA = {i for s, i in dels if s == 'A'}; dB = {i for s, i in dels if s == 'B'}
    survA = [i for i in range(len(base['A'])) if i not in dA]; survB = [i for i in range(len(base['B'])) if i not in dB]
    ed = dict(delete=[[s, i] for s, i in dels], insert=[], tail=[]); tails = []
    for k, (p, g) in enumerate(ins):
        if p < NA1: ed['insert'].append(['A', survA[p] if p < len(survA) else len(base['A']), list(g)])
        elif p < NA1 + NC: raise ValueError('cut insert not supported')
        else:
            q = p - NA1 - NC
            if q < NB1: ed['insert'].append(['B', survB[q] if q < len(survB) else len(base['B']), list(g)])
            else: tails.append((q - NB1, k, list(g)))
    for m, (j, k, g) in enumerate(sorted(tails)): ed['tail'].append([j + m, g])
    return ed
