"""conelu.py (copy of r3 agent B-interact tools/cone.py, unchanged logic): cone-cap aware frame feasibility for compensating inserts (agent B-interact, lead 1).

The frame model (PR1186 frames.Graph) is a nested-subspace lattice: lower frames join forward along register chains,
upper frames meet backward, and the end-of-B cone cap meets the upper frame of a register's last B (or tail) vertex.
Both are monotone along the DAG, so for ONE insert v (x += c y before seq position p) into a feasible word W:
    W + v feasible  <=>  L_a v L_c  <=  U_b ^ U_d ^ caps(x if b is tail/end) ^ caps(y if d is tail/end)
where a, b (c, d) are x's (y's) chain neighbours of p in W, plus the cut-equality term when v becomes x's or y's last A
vertex.  (Every downstream lower only gains L_v <= U_v <= U_b <= U_k; every upstream upper only meets U_v >= L_v >= L_k.)
For sets of inserts the exact test is Graph construction itself (Infeasible), with the BASE word's caps (an exact final
word has the base map, hence the base derived compensation and cones)."""
import bisect
import frames as F
from word import inline
END = 10 ** 9

class LU:
    def __init__(self, P, W):
        self.NA, self.NC, self.NB = len(W['A']), len(W['cut']), len(W['B']); NA, NC, NB = self.NA, self.NC, self.NB
        self.g = g = F.Graph(inline(W, True), check_literal=False, tail_mutable=True, caps=P.caps, cut_equality=True)
        pos = []
        for regs, Fr, sec, idx in g.nodes:
            pos.append(-1 if sec == 'start' else idx if sec == 'A' else NA if sec == 'cut' else
                       NA + NC + idx if sec == 'B' else NA + NC + NB + idx if sec == 'tail' else END)
        self.pos = pos; self.cpos = [[pos[k] for k in ch] for ch in g.chains]
        self.span = {}
    def S(self, Fr):
        k = tuple(Fr); s = self.span.get(k)
        if s is None: s = self.span[k] = F.span(Fr)
        return s
    def nb(self, r, p):
        ch = self.g.chains[r]; j = bisect.bisect_left(self.cpos[r], p); return ch[j - 1], ch[j]
    def ok(self, x, y, p):
        g = self.g; a, b = self.nb(x, p); c, d = self.nb(y, p)
        L = tuple(g.lower[a]) + tuple(g.lower[c])
        if p < self.NA:
            for nbk in (b, d):
                if g.nodes[nbk][2] == 'cut': L = L + tuple(g.nodes[nbk][1])
        U = self.S(g.upper[b]) & self.S(g.upper[d])
        for r, nbk in ((x, b), (y, d)):
            if r in g.caps and g.nodes[nbk][2] in ('tail', 'end'): U = U & self.S(g.caps[r])
        return F.span(F.basis(L)) <= U

def feasible(P, W):
    try: LU(P, W); return True, None
    except F.Infeasible as e: return False, (e.args[0] if e.args else None)

def minimal_conflict(P, W0, ins, build):
    """deletion filter: a minimal subset of ins (list of (pos, gate) on W0) whose insertion is frame-infeasible."""
    S = list(range(len(ins)))
    for k in list(S):
        T = [j for j in S if j != k]
        if T and not feasible(P, build(W0, [ins[j] for j in T]))[0]: S = T
    return S
