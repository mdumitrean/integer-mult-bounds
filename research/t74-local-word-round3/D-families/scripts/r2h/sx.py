"""sx.py: exact suffix-effect machinery on seq = B + early tail (Fractions, stdlib only).
Positions p in [0, L] (L = len(seq)): 'insert before seq gate p'.  p <= len(B): B insert at base index p (p == len(B) appends
to B); p >= len(B): tail insert at early index p - len(B) (p == L: end of tail).  p == len(B) is both (two placements).
S_x(p) = effect on the final registers of the segment of x's value just before position p.
Events: for register x, S_x is constant on intervals J_0=[0,i_1], J_1=[i_1+1,i_2], ..., J_k=[i_k+1, L] where i_j are the
gates reading x (as source) or scaling x."""
import gzip, json
from fractions import Fraction as Q

def load(path):
    return json.loads(gzip.decompress(open(path, 'rb').read()))

def coef(g):
    return Q(g[3], g[4]) if g[0] == 'add' else Q(g[2], g[3])

def dyadic(c):
    c = Q(c); return c.denominator & (c.denominator - 1) == 0

def build_seq(w):
    B = w['B']; tail = [w['cleanup'][i] for i, U in w['early_cleanup']]
    return B, tail, B + tail

def addv(a, b, c=1):
    d = dict(a)
    for k, v in b.items():
        x = d.get(k, 0) + c * v
        if x: d[k] = x
        else: d.pop(k, None)
    return d

def scalev(a, c):
    return {k: c * v for k, v in a.items()} if c else {}

def col(seq, q):
    """census.py's col: forward column of the initial value of q."""
    r = {q: Q(1)}
    for g in seq:
        t = g[1]
        if g[0] == 'add':
            if g[2] in r:
                x = r.get(t, 0) + coef(g) * r[g[2]]
                if x: r[t] = x
                else: r.pop(t, None)
        elif t in r:
            r[t] = r[t] * coef(g)
    return r

class Suffix:
    """per-register piecewise-constant suffix effects of the base seq (gates in `skip` are ignored, e.g. deleted q reads;
    skipping reads of q never changes S_x for x != q)."""
    def __init__(self, seq, nreg, skip=()):
        self.seq = seq; self.L = L = len(seq); skip = set(skip)
        cur = {}            # x -> current vector (absent: e_x)
        self.change = [[] for _ in range(nreg)]   # x -> list of gate indices (ascending) where S_x changes
        self.vecs = [None] * nreg                 # x -> list of vectors per interval (J_0..J_k)
        rev = [[] for _ in range(nreg)]           # x -> vectors from the end backwards
        for x in range(nreg): rev[x].append({x: Q(1)})
        for i in range(L - 1, -1, -1):
            if i in skip: continue
            g = seq[i]
            if g[0] == 'add':
                t, s = g[1], g[2]; c = coef(g)
                St = cur.get(t, {t: Q(1)}); Ss = cur.get(s, {s: Q(1)})
                cur[s] = addv(Ss, St, c)
                self.change[s].append(i); rev[s].append(cur[s])
            else:
                t = g[1]; c = coef(g)
                cur[t] = scalev(cur.get(t, {t: Q(1)}), c)
                self.change[t].append(i); rev[t].append(cur[t])
        for x in range(nreg):
            self.change[x].reverse(); self.vecs[x] = list(reversed(rev[x]))
    def intervals(self, x):
        """list of (lo, hi, vec): S_x(p) == vec for lo <= p <= hi."""
        ch = self.change[x]; out = []; lo = 0
        for j, i in enumerate(ch):
            out.append((lo, i, self.vecs[x][j])); lo = i + 1
        out.append((lo, self.L, self.vecs[x][len(ch)]))
        return out
    def at(self, x, p):
        import bisect
        j = bisect.bisect_left(self.change[x], p)   # number of change gates with index < p
        return self.vecs[x][j]
    def interval_index(self, x, p):
        import bisect
        return bisect.bisect_left(self.change[x], p)

def nregs(w):
    return 2 * 112 + w['report']['R']

def deletion_d(seq, S, reads):
    """d = sum_{r in reads} c_r * S_{t_r}(r+1) for deleted reads (seq indices)."""
    d = {}
    for r in reads:
        g = seq[r]; d = addv(d, S.at(g[1], r + 1), coef(g))
    return d

def mask(v):
    m = 0
    for k in v: m |= 1 << k
    return m

def fstr(v):
    return {str(k): str(x) for k, x in sorted(v.items())}
