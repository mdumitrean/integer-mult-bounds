"""sk5.py (agent M-bigB, r6): r5 D-compsplit's projected split-key model (sk3.PRound) with one change in candidate
generation: an insert whose #1957 oracle cost is the INF sentinel (the oracle cannot price it against the deleted word's
fixed frame timeline) is NOT pruned by cost.  If it passes the exact single-insert cone test it is kept at cost 0 (an
optimistic lower bound), outside the per-effect dedup.  The model stays a relaxation of the true one, so INFEASIBLE is still
a proof within the model; any proposal is priced exactly by the harness (price3.py), so cost 0 never reaches a result."""
import os, sys
from collections import defaultdict
HERE = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r5', 'agents', 'D-compsplit', 'tools'))
from sk3 import PRound, proj, isport, hist_values, Q
SENT = 1 << 59

class PRound5(PRound):
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
        seen = {}; cand = []; self.cone_rejected = 0; self.cost_rejected = 0; self.sentinel_kept = 0; self.sentinel_cone_rejected = 0
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
                    cst = self.orc.cost(x, y, op); sentinel = cst >= SENT
                    if not sentinel and self.bud is not None and cst > self.cap_mult * self.bud: self.cost_rejected += 1; continue
                    lu = getattr(self, 'lu', None)
                    if lu is not None and not lu.ok(x, y, i):
                        self.cone_rejected += 1; self.sentinel_cone_rejected += sentinel; continue
                    if sentinel:
                        cand.append((x, y, i, (coN if vN else None, coP if vP else None), (vN, vP), 0)); self.sentinel_kept += 1; continue
                    kk = (x, tuple(sorted((coN or {}).items())) if vN else (), tuple(sorted((coP or {}).items())) if vP else (),
                          tuple(sorted(vN.items())), tuple(sorted(vP.items())))
                    c_ = (x, y, i, (coN if vN else None, coP if vP else None), (vN, vP), cst)
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
        self.cand = [c for c in cand if c is not None]; return self.cand
