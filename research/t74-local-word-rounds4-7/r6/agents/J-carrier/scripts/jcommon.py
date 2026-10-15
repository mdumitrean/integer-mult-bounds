"""J-carrier (r6) common code: q-free meet cover relaxation for never-written copy-window pivots.

Relaxation R_free(q) (a valid lower bound for the STAR family of exact re-deliveries: delete q's B reads, add any reads of
q, i.e. gates r += c*q in B or the early tail; every other gate unchanged):
  * every register y in dp (q's B+tail column change on non-full-end coordinates, as r3/r4) must receive q-content through
    dataflow from some new q-read (existing gates propagate it);
  * each new q-read is modelled as a node on r's chain only (q's chain participation dropped), with a constant lower frame
    Lq = lower[q's last node before the read] (any feasible frame of that q node contains it, so the true shared node does);
  * dropping q's chain nodes and any extra gates (restores, coefficient fixes) can only lower the optimal frame cost
    (subadditive concave jump costs, fewer constraints), so min over covers <= cost of every exact star re-delivery.
Positions: within a segment of r's chain (no gate involves r) the reach is constant; the least constrained position is used
(tail 0 if the segment reaches past the end of B, since end-of-B cone caps then do not apply to the meet node).
"""
import sys, os, json, time, collections
JC_DIR = os.path.dirname(os.path.abspath(__file__))
SCR = os.path.abspath(os.path.join(JC_DIR, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r4/agents/A-reroute/scripts'))
from awin import *          # H, F, inline, cone_caps, deadline, Timeout, sx, AWin, regs, gate, WORDS, PIVOTS
sys.path.insert(0, JC_DIR)
import frames_j as FJ
MARK = lambda r: ['scale', r, 1, 1, []]
def is_mark(g): return g[0] == 'scale' and g[2] == 1 and g[3] == 1

class Pivot:
    def __init__(self, wname, q):
        self.aw = aw = AWin(wname, q); self.q = q; w = aw.w
        self.w1 = w1 = H.compile_edits(w, dict(delete=aw.Breads))
        self.B1 = list(w1['B']); self.T1 = [w1['cleanup'][i] for i, U in w1['early_cleanup']]
        assert not any(is_mark(g) for g in self.B1 + self.T1)
        seq0B = list(w['B']) + aw.tail; self.seq1 = self.B1 + self.T1
        d = sx.addv(sx.col(seq0B, q), sx.col(self.seq1, q), -1)
        self.dp = sorted(k for k in d if not aw.full_end(k)); self.dfull = sorted(k for k in d if aw.full_end(k))
        self.caps = aw.P.caps; self.costs = aw.P.costs; self.base_cost = aw.P.base_cost
        g1 = FJ.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=self.caps, cut_equality=True)
        self.g1 = g1
        # q's nodes: last A node and tail nodes (q never written after A; its B reads are deleted)
        qn = [(k, g1.nodes[k][2], g1.nodes[k][3]) for k in g1.chains[q]]
        self.q_nodes = qn
        self.lastA = max(k for k, sec, idx in qn if sec == 'A')
        self.q_tail = [(idx, k) for k, sec, idx in qn if sec == 'tail']
        assert not any(sec == 'B' for k, sec, idx in qn), 'q has B nodes in the deleted word'
    def Lq(self, sec, pos):
        """lower frame of q's last node strictly before a meet inserted before (sec, pos)."""
        k = self.lastA
        if sec == 'tail':
            for idx, kk in self.q_tail:
                if idx < pos: k = kk
        return tuple(self.g1.lower[k])
    def candidates(self):
        """(sec, pos, r, mask) for every segment of every register r != q whose reach meets dp."""
        dp = self.dp; di = {y: i for i, y in enumerate(dp)}; nB = len(self.B1); L = len(self.seq1); seq = self.seq1
        Rm = collections.defaultdict(int)
        for y in dp: Rm[y] = 1 << di[y]
        involve = collections.defaultdict(list)
        for i, g in enumerate(seq):
            for r in regs(g): involve[r].append(i)
        # segment starts for r: p = 0 and p = i + 1 for each node i of r; record reach at those positions
        starts = collections.defaultdict(set)
        for r, ii in involve.items():
            starts[r].add(0)
            for i in ii: starts[r].add(i + 1)
        allregs = set(involve) | set(range(sx.nregs(self.aw.w)))
        for r in allregs: starts[r].add(0)
        at = collections.defaultdict(list)
        for r, ps in starts.items():
            for p in ps: at[p].append(r)
        rec = {}
        for p in range(L, -1, -1):
            for r in at.get(p, ()):
                if r != self.q and Rm[r]: rec[r, p] = Rm[r]
            if p > 0:
                g = seq[p - 1]
                if g[0] == 'add': Rm[g[2]] |= Rm[g[1]]
        out = []
        for (r, p), m in rec.items():
            nxt = next((i for i in involve.get(r, []) if i >= p), None)   # r's next node at/after p
            seg_end = nxt if nxt is not None else L                         # the segment is [p, seg_end]
            if p <= nB and seg_end >= nB and p < L:                         # segment reaches past the end of B: use tail 0
                sec, pos = ('tail', 0) if seg_end > nB or nxt is None or nxt >= nB else ('B', p)
            elif p >= nB: sec, pos = 'tail', p - nB
            else: sec, pos = 'B', p
            out.append((sec, pos, r, m))
        return sorted(set(out))
    def price(self, meets, timeout=240):
        """meets: iterable of (sec, pos, r) in deleted-word coordinates. Returns (status, cost)."""
        ins = [[p, MARK(r)] for sec, p, r in meets if sec == 'B']
        tl = [[p, MARK(r)] for sec, p, r in meets if sec == 'tail']
        w2 = H.compile_edits(self.w1, dict(insert=ins, tail=tl))
        ex = {}
        lqB = self.Lq('B', 0)
        for i, g in enumerate(w2['B']):
            if is_mark(g): ex['B', i] = lqB
        # tail markers: early_cleanup order; Lq depends on q's tail nodes before the marker (in the edited order)
        early = w2['early_cleanup']; qcount = 0
        for j, (ci, U) in enumerate(early):
            g = w2['cleanup'][ci]
            if is_mark(g):
                k = self.lastA
                tq = [kk for idx, kk in self.q_tail]
                ex['tail', j] = tuple(self.g1.lower[tq[qcount - 1]]) if qcount else tuple(self.g1.lower[self.lastA])
            elif self.q in regs(g): qcount += 1
        try:
            with deadline(timeout):
                g2 = FJ.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=self.caps, cut_equality=True, extra_lower=ex)
                r = FJ.optimal_frames(inline(w2, True), self.costs, check_literal=False, graph=g2)
            return ('ok' if r['certified'] else 'uncertified'), r['cost']
        except FJ.Infeasible: return 'infeasible', None
        except Timeout: return 'timeout', None
        except ValueError as e: return 'error:' + str(e)[:60], None

# ---------------------------------------------------------------- r-free relaxation (q's chain only)
MARKQ = lambda q: ['scale', q, 1, 1, []]
def r_bounds(P, sec, pos, r):
    """deleted-word lower frame of r's last node before (sec,pos) and upper frame of r's first node at/after it
    (with r's end-of-B cone cap if that next node is in the tail or the end)."""
    g = P.g1; nB = len(P.B1)
    t = pos if sec == 'B' else nB + pos
    def tkey(k):
        s, i = g.nodes[k][2], g.nodes[k][3]
        return {'start': -2, 'A': -1, 'cut': -1}.get(s, None) if s in ('start', 'A', 'cut') else (i if s == 'B' else nB + i if s == 'tail' else 10 ** 9)
    ch = g.chains[r]; prevk = None; nextk = None
    for k in ch:
        tk = tkey(k)
        if tk is not None and tk < t: prevk = k
        elif tk is not None and tk >= t and nextk is None: nextk = k
        elif tk is None and prevk is None: prevk = k
    # A/start/cut nodes precede B: tkey<0
    L = tuple(g.lower[prevk]); U = set(G_span(g.upper[nextk]))
    if r in P.caps and g.nodes[nextk][2] in ('tail', 'end'): U &= set(G_span(P.caps[r]))
    return L, tuple(sorted(U)), nextk
def G_span(F): return FJ.span(tuple(F))
def price_rfree(P, meets, timeout=240):
    """meets: (sec, pos, r): q-only nodes at those positions with lower >= L_r(prev) and upper <= U_r(next)."""
    bounds = [(sec, pos) + r_bounds(P, sec, pos, r)[:2] for sec, pos, r in meets]
    ins = [[p, MARKQ(P.q)] for sec, p, r in meets if sec == 'B']
    tl = [[p, MARKQ(P.q)] for sec, p, r in meets if sec == 'tail']
    w2 = H.compile_edits(P.w1, dict(insert=ins, tail=tl))
    # map markers back to their meets in order of insertion position (B markers in B order, tail markers in tail order)
    exl = {}; exu = {}
    bm = [i for i, g in enumerate(w2['B']) if is_mark(g)]
    tm = [j for j, (ci, U) in enumerate(w2['early_cleanup']) if is_mark(w2['cleanup'][ci])]
    bb = sorted([b for b in bounds if b[0] == 'B'], key=lambda b: b[1]); tb = sorted([b for b in bounds if b[0] == 'tail'], key=lambda b: b[1])
    assert len(bm) == len(bb) and len(tm) == len(tb)
    for i, b in zip(bm, bb): exl['B', i] = b[2]; exu['B', i] = FJ.basis(tuple(b[3])) if b[3] else ()
    for j, b in zip(tm, tb): exl['tail', j] = b[2]; exu['tail', j] = FJ.basis(tuple(b[3])) if b[3] else ()
    try:
        with deadline(timeout):
            g2 = FJ.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True, extra_lower=exl, extra_upper=exu)
            r = FJ.optimal_frames(inline(w2, True), P.costs, check_literal=False, graph=g2)
        return ('ok' if r['certified'] else 'uncertified'), r['cost']
    except FJ.Infeasible: return 'infeasible', None
    except Timeout: return 'timeout', None
    except ValueError as e: return 'error:' + str(e)[:60], None

def price_real(P, meets, timeout=240):
    """actual reads r += q at the meet positions (q's and r's chains share the node), base cone caps."""
    ins = [[p, gate(r, P.q, 1)] for sec, p, r in meets if sec == 'B']
    tl = [[p, gate(r, P.q, 1)] for sec, p, r in meets if sec == 'tail']
    w2 = H.compile_edits(P.w1, dict(insert=ins, tail=tl))
    try:
        with deadline(timeout):
            g2 = FJ.Graph(inline(w2, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
            r = FJ.optimal_frames(inline(w2, True), P.costs, check_literal=False, graph=g2)
        return ('ok' if r['certified'] else 'uncertified'), r['cost'], dict(sorted(r['profile'].items()))
    except FJ.Infeasible as e: return 'infeasible', None, str(e.args[0][:4]) if e.args else ''
    except Timeout: return 'timeout', None, None

def candidates_latest(P, base=None):
    """same segments as Pivot.candidates, placed at the LATEST position of each segment (just before r's next node,
    or the end of the tail); reach is identical within a segment, only the order on q's chain and caps change."""
    base = base if base is not None else P.candidates(); nB = len(P.B1); L = len(P.seq1); seq = P.seq1
    involve = collections.defaultdict(list)
    for i, g in enumerate(seq):
        for r in regs(g): involve[r].append(i)
    out = []
    for sec, pos, r, m in base:
        p = pos if sec == 'B' else nB + pos
        nxt = next((i for i in involve.get(r, []) if i >= p), None)
        last = (nxt if nxt is not None else L)          # insert before r's next node (or at the end of the tail)
        out.append(('B', last, r, m) if last < nB else ('tail', last - nB, r, m))
    return sorted(set(out))
