"""A-reroute common helpers (round r4).  Paths relative to scratchpad/ via R3/R4 roots."""
import sys, os, json, gzip
from fractions import Fraction as Q
SCR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', '..'))
R3 = os.path.join(SCR, 'r3'); R4 = os.path.join(SCR, 'r4')
TK = os.path.join(R3, 'toolkit-rev3')
if TK not in sys.path: sys.path.insert(0, TK)
os.environ.setdefault('IMB_ROOT', os.path.join(R3, 'main')); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout
WORDS = dict(base=os.path.join(R3, 'inputs/gauge44-word-566-554.json.gz'), extra=os.path.join(R3, 'inputs/extra-word-566-554.json.gz'))
CALLS = dict(base=249, extra=417)
V = 112
PIVOTS = [439, 444, 438, 226, 228, 230, 231, 232, 236, 238, 434, 436, 446]
def load(name): return json.load(gzip.open(WORDS[name]))
def coef(g): return Q(g[3], g[4]) if g[0] == 'add' else Q(g[2], g[3])
def regs(g): return g[1:3] if g[0] == 'add' else g[1:2]
def cls(r): return 'D' if r < V else ('P' if r < 2 * V else 'H')
def apply_rows(seq, rows=None):
    """rows: register -> {initial register: coefficient}; returns updated dict (absent = identity row)."""
    rows = {} if rows is None else rows
    for g in seq:
        t = g[1]
        if t not in rows: rows[t] = {t: Q(1)}
        c = coef(g)
        if g[0] == 'scale': rows[t] = {k: x * c for k, x in rows[t].items()}
        else:
            s = g[2]; src = rows.get(s, {s: Q(1)}); d = rows[t]
            for k, x in src.items():
                y = d.get(k, 0) + c * x
                if y: d[k] = y
                else: d.pop(k, None)
    return rows
def gate(t, s, c):
    c = Q(c); return ['add', t, s, c.numerator, c.denominator, []]
