"""awin: A-window re-delivery for never-written copy-window pivots (r4 A-reroute).
For pivot q (never written after its last A write), delete q's B reads and re-deliver q's B+tail column d exactly with
<= K dyadic q-reads placed in the A window (after q's last A write, before the cut gates) and optionally in B/tail
(mixed), plus frame-free cleanup prepends for FULL-end coordinates (as r3 PFS).  Atoms are suffix vectors S_y(p) of
seqF = A + cut + B + tail.  Slots are screened with the deleted word's lower/upper frames (lucore semantics, A-aware
times).  Every candidate is then checked with a whole-program rational simulation and priced with exact optimal frames
(compensation and cone caps re-derived for the edited word)."""
import sys, os, json, itertools, bisect, collections, time, copy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import *
sys.path.insert(1, os.path.join(R3, 'agents/D-families/scripts/r2h'))
import sx
from lucore import lu
FULL9 = tuple(1 << i for i in range(9))

def prog(w, comp):
    early = [i for i, U in w['early_cleanup']]; es = set(early)
    return (list(w['precondition']) + comp + list(w['A']) + list(w['cut']) + list(w['B'])
            + [w['cleanup'][i] for i in early] + [g for i, g in enumerate(w['cleanup']) if i not in es])

def call_map(w):
    caps, comp = cone_caps(w)
    return apply_rows(prog(w, comp)), comp, caps

def build(w, a_ins, b_del, prepend):
    """a_ins: list of (A position p in base A indices, gate); b_del: base B indices; prepend: gates. -> new word."""
    w1 = H.compile_edits(w, dict(delete=sorted(b_del), insert=[], tail=[], prepend=prepend))
    A = list(w['A']); at = collections.defaultdict(list)
    for p, g in a_ins: at[p].append(list(g[:-1]) + [[]])
    A1 = []
    for i in range(len(A) + 1):
        A1.extend(at.get(i, []))
        if i < len(A): A1.append(list(A[i][:-1]) + [list(A[i][-1]) if A[i][-1] is not None else []])
    w1 = dict(w1); w1['A'] = A1
    return w1

def price(w1, costs, base_cost, timeout=300):
    try:
        with deadline(timeout):
            caps, comp = cone_caps(w1)
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), costs, check_literal=False, graph=g)
        return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - base_cost, profile=dict(sorted(r['profile'].items())), ncomp=len(comp))
    except F.Infeasible as e: return dict(status='infeasible', why=str(e.args[0][:3]) if e.args else '')
    except Timeout: return dict(status='timeout')
    except ValueError as e: return dict(status='error:' + str(e)[:80])

class AWin:
    def __init__(self, wname, q, mixed=True):
        self.P = H.Pricer(WORDS[wname], b=os.environ['IMB_B'], check_literal=True); w = self.w = self.P.base; self.q = q
        self.nA, self.nC, self.nB = len(w['A']), len(w['cut']), len(w['B'])
        self.tail = [w['cleanup'][i] for i, U in w['early_cleanup']]
        self.seqF = list(w['A']) + list(w['cut']) + list(w['B']) + self.tail; self.L = len(self.seqF)
        self.NREG = sx.nregs(w); self.mixed = mixed
        self.lastW = max(i for i, g in enumerate(w['A']) if g[1] == q)
        assert not any(g[1] == q for g in w['cut'] + w['B']), 'pivot is written after A'
        self.Breads = [i for i, g in enumerate(w['B']) if g[0] == 'add' and g[2] == q]
        self.full_end = lambda r: (r < 112 or r >= 224) and str(r) not in w['helper_final']
        assert self.full_end(q)
        self.map0, self.comp0, self.caps0 = call_map(w)
    def run(self, K=4, maxsets=40, maxsols=400, require_A=True, budget=None):
        w = self.w; q = self.q; nA, nC, nB = self.nA, self.nC, self.nB; off = nA + nC
        w1 = H.compile_edits(w, dict(delete=self.Breads))            # deleted word (q's B reads removed)
        seq1F = list(w1['A']) + list(w1['cut']) + list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']]
        seq0B = list(w['B']) + self.tail; seq1B = list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']]
        d = sx.addv(sx.col(seq0B, q), sx.col(seq1B, q), -1)
        fe = self.full_end; dp = {k: v for k, v in d.items() if not fe(k)}
        S = sx.Suffix(seq1F, self.NREG)
        caps1, comp1 = cone_caps(w1)
        res = lu(inline(w1, True), caps1)
        if res['bad']: return dict(status='deleted-word-infeasible', d=sx.fstr(d))
        nodes, chains, lower, upper = res['nodes'], res['chains'], res['lower'], res['upper']
        def tkey(k):
            sec, idx = nodes[k][2], nodes[k][3]
            if sec == 'start': return -1
            if sec == 'A': return idx
            if sec == 'cut': return nA + 0.5
            if sec == 'B': return off + idx
            if sec == 'tail': return off + nB + idx
            return 10 ** 9
        sp = lambda X: F.span(tuple(X)); leq = lambda a, b: sp(a) <= sp(b)
        qch = chains[q]; qt = [tkey(k) for k in qch]
        def slot_ok(y, p):
            """insert a meet of y and q before seqF position p (A window: p <= nA; B/tail: p >= off)."""
            if nA < p < off: return None
            ch = chains[y]; ts = [tkey(k) for k in ch]; j = bisect.bisect_left(ts, p)
            a, b = ch[j - 1], ch[j]
            jq = bisect.bisect_left(qt, p); qa, qb = qch[jq - 1], qch[jq]
            Ly, Uy, Lq, Uq = lower[a], upper[b], lower[qa], upper[qb]
            if nodes[b][2] in ('tail', 'end') and y in caps1 and p <= off + nB: Uy = F.basis(tuple(x for x in sp(Uy) if x in sp(caps1[y])))
            if nodes[qb][2] in ('tail', 'end') and q in caps1 and p <= off + nB: Uq = F.basis(tuple(x for x in sp(Uq) if x in sp(caps1[q])))
            Lnew = F.basis(tuple(Ly) + tuple(Lq))
            if nodes[b][2] == 'cut': Lnew = F.basis(tuple(Lnew) + tuple(nodes[b][1]))
            return (leq(Lnew, Uy) and leq(Lnew, Uq)), Ly, Uy
        events = collections.defaultdict(list)
        for i, g in enumerate(seq1F):
            for r in regs(g): events[r].append(i)
        atoms = []
        lo_win = self.lastW + 1
        for y in range(self.NREG):
            if y == q: continue
            for lo, hi, v in S.intervals(y):
                vp = {k: c for k, c in v.items() if not fe(k)}
                if not vp: continue
                cand_p = set()
                for (a0, b0) in ((lo_win, nA), (off, self.L)) if self.mixed else ((lo_win, nA),):
                    l2, h2 = max(lo, a0), min(hi, b0)
                    if l2 > h2: continue
                    ev = sorted(set(e for r in (y, q) for e in events.get(r, []) if l2 <= e < h2))
                    cand_p.update([l2] + [e + 1 for e in ev if e + 1 <= h2])
                slots = []
                for p in sorted(cand_p):
                    si = slot_ok(y, p)
                    if si and si[0]: slots.append((p, si[1], si[2]))
                if slots: atoms.append(dict(y=y, lo=lo, hi=hi, v=v, vp=vp, slots=slots, inA=any(s[0] <= nA for s in slots)))
        mask = lambda vec: sum(1 << k for k in vec); Dm = mask(dp)
        for a in atoms: a['m'] = mask(a['vp'])
        inv = collections.defaultdict(list)
        for i, a in enumerate(atoms):
            m = a['m']
            while m:
                b = (m & -m).bit_length() - 1; inv[b].append(i); m &= m - 1
        def solve(idx):
            keys = sorted(set(dp).union(*[atoms[i]['vp'].keys() for i in idx])); kk = len(idx)
            rows = [[atoms[i]['vp'].get(c, Q(0)) for i in idx] + [dp.get(c, Q(0))] for c in keys]; r = 0
            for cidx in range(kk):
                pv = next((i for i in range(r, len(rows)) if rows[i][cidx] != 0), None)
                if pv is None: return None
                rows[r], rows[pv] = rows[pv], rows[r]; x = rows[r][cidx]; rows[r] = [z / x for z in rows[r]]
                for i in range(len(rows)):
                    if i != r and rows[i][cidx] != 0:
                        f = rows[i][cidx]; rows[i] = [z - f * yv for z, yv in zip(rows[i], rows[r])]
                r += 1
            if any(rows[i][kk] != 0 for i in range(r, len(rows))): return None
            sol = [rows[i][kk] for i in range(kk)]
            if any(b == 0 or not sx.dyadic(b) for b in sol): return None
            return sol
        sols = []; seen = set(); t_end = (time.time() + budget) if budget else None; self.budget_hit = False; self.dfs_nodes = 0
        def dfs(chosen, cover, oc):
            self.dfs_nodes += 1
            if t_end and time.time() > t_end: self.budget_hit = True; return
            if len(sols) >= maxsols: return
            if chosen and (cover & Dm) == Dm and all(c >= 2 for c in oc.values()):
                key = tuple(sorted(chosen))
                if key not in seen and (not require_A or any(atoms[i]['inA'] for i in key)):
                    seen.add(key); s = solve(list(key))
                    if s: sols.append((key, s))
            if len(chosen) >= K: return
            need = [b for b in sorted(dp) if not (cover >> b) & 1]; once = sorted(b for b, c in oc.items() if c == 1)
            b = need[0] if need else (once[0] if once else None)
            if b is None: return
            for i in inv.get(b, []):
                if i in chosen: continue
                o2 = dict(oc); m = atoms[i]['m'] & ~Dm
                while m:
                    bb = (m & -m).bit_length() - 1; o2[bb] = o2.get(bb, 0) + 1; m &= m - 1
                dfs(chosen + [i], cover | atoms[i]['m'], o2)
        if dp: dfs([], 0, {})
        cands = []; seen_ed = set()
        for key, sol in sols:
            opts = [[s for s in atoms[i]['slots']] for i in key]; got = 0
            for combo in itertools.product(*opts):
                if require_A and not any(c[0] <= nA for c in combo): continue
                order = sorted(range(len(key)), key=lambda j: combo[j][0])
                if any(not leq(combo[order[x]][1], combo[order[yy]][2]) for x in range(len(order)) for yy in range(x + 1, len(order))): continue
                a_ins = []; b_ins = []; t_ins = []; pre_vec = dict(d)
                for j in order:
                    a = atoms[key[j]]; c = sol[j]; p = combo[j][0]; g = gate(a['y'], q, c)
                    if p <= nA: a_ins.append((p, g))
                    elif p <= off + nB: b_ins.append((p - off, g))
                    else: t_ins.append((p - off - nB, g))
                    pre_vec = sx.addv(pre_vec, a['v'], -c)
                assert all(fe(k) for k in pre_vec), pre_vec
                prepend = [gate(k, q, c) for k, c in sorted(pre_vec.items())]
                ed = dict(a_ins=[[p, g] for p, g in a_ins], b_ins=[[p, g] for p, g in b_ins], t_ins=[[p, g] for p, g in t_ins], prepend=prepend)
                kk = json.dumps(ed, sort_keys=True, default=str)
                if kk in seen_ed: continue
                seen_ed.add(kk)
                cands.append(dict(atoms=[[atoms[i]['y'], atoms[i]['lo'], atoms[i]['hi'], str(sol[j])] for j, i in enumerate(key)],
                                  slots=[combo[j][0] for j in range(len(key))], ed=ed))
                got += 1
                if got >= maxsets: break
        cov = {str(k): [sum(1 for a in atoms if a['inA'] and k in a['vp']), sum(1 for a in atoms if k in a['vp'])] for k in sorted(dp)}
        return dict(status='ok', d=sx.fstr(d), dp=sx.fstr(dp), natoms=len(atoms), natomsA=sum(a['inA'] for a in atoms), nsols=len(sols), cands=cands, budget_hit=self.budget_hit, dfs_nodes=self.dfs_nodes, coverage=cov)
    def materialize(self, ed):
        w = self.w; nB = self.nB
        # B inserts / tail inserts relative to the base word (deleted reads removed): use harness compile with B indices
        if ed['b_ins'] or ed['t_ins']:
            base_ed = dict(delete=self.Breads, insert=[[p_map, g] for p_map, g in self._b_positions(ed['b_ins'])], tail=[[j, g] for j, g in ed['t_ins']], prepend=ed['prepend'])
        else:
            base_ed = dict(delete=self.Breads, insert=[], tail=[], prepend=ed['prepend'])
        w1 = H.compile_edits(w, base_ed)
        A = list(w['A']); at = collections.defaultdict(list)
        for p, g in ed['a_ins']: at[p].append(list(g[:-1]) + [[]])
        A1 = []
        for i in range(len(A) + 1):
            A1.extend(at.get(i, []))
            if i < len(A): A1.append(list(A[i][:-1]) + [list(A[i][-1]) if A[i][-1] is not None else []])
        w1 = dict(w1); w1['A'] = A1
        return w1
    def _b_positions(self, b_ins):
        """b_ins positions are in the DELETED word's B indexing; map to base B indices for compile_edits."""
        keep = [i for i in range(self.nB) if i not in set(self.Breads)]
        out = []
        for p, g in b_ins:
            out.append([keep[p] if p < len(keep) else self.nB, g])
        return out
    def check(self, w1):
        m1, comp1, caps1 = call_map(w1)
        keys = set(self.map0) | set(m1)
        same = all(self.map0.get(k, {k: Q(1)}) == m1.get(k, {k: Q(1)}) for k in keys)
        return same, comp1 == self.comp0, len(comp1)
