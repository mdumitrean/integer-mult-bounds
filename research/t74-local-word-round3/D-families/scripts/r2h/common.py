"""common helpers (round-2 agent H, adapted for r3: toolkit rev3, compat.deadline, 566+554 words)."""
import sys, os, json, gzip
R = 'r3'
TK = R + '/toolkit-rev3'
if TK not in sys.path: sys.path.insert(0, TK)
os.environ.setdefault('IMB_ROOT', R + '/main'); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout
from fractions import Fraction as Q
WORDS = {'BASE': R + '/inputs/gauge44-word-566-554.json.gz', 'EXTRA': R + '/inputs/extra-word-566-554.json.gz'}

def price_raw(P, ed, timeout=300, base_caps=False):
    """optimal frames of the edited word WITHOUT the exactness screen (for bounds / diagnostics)."""
    w1 = H.compile_edits(P.base, ed)
    try:
        with deadline(timeout):
            caps = P.caps if base_caps else cone_caps(w1)[0]
            g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
            r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=g)
        return dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - P.base_cost, profile=dict(sorted(r['profile'].items())))
    except F.Infeasible as e: return dict(status='infeasible', why=str(e.args[0][:3]) if e.args else '')
    except Timeout: return dict(status='timeout')
    except ValueError as e: return dict(status='error:' + str(e)[:80])

def coef(g): return Q(g[3], g[4]) if g[0] == 'add' else Q(g[2], g[3])

def seg_seq(w):
    return list(w['B']) + [w['cleanup'][i] for i, U in w['early_cleanup']]

def full_map_fraction(seq, nreg):
    rows = {}
    for g in seq:
        t = g[1]
        if t not in rows: rows[t] = {t: Q(1)}
        c = coef(g)
        if g[0] == 'scale':
            rows[t] = {k: x * c for k, x in rows[t].items()}
        else:
            s = g[2]
            src = rows.get(s, {s: Q(1)}); d = rows[t]
            for k, x in src.items():
                y = d.get(k, 0) + c * x
                if y: d[k] = y
                else: d.pop(k, None)
    return rows

def exact_fraction_same(w0, ed):
    """exact Fraction check that B + early tail (+ prepends) map is unchanged by the edit."""
    w1 = H.compile_edits(w0, ed); npre = len(ed.get('prepend', []))
    s0 = seg_seq(w0); s1 = list(w1['B']) + [w1['cleanup'][i] for i, U in w1['early_cleanup']] + [g for g in w1['cleanup'][:npre]]
    nreg = 2 * 112 + w0['report']['R']
    a = full_map_fraction(s0, nreg); b = full_map_fraction(s1, nreg)
    keys = set(a) | set(b)
    return all(a.get(k, {k: Q(1)}) == b.get(k, {k: Q(1)}) for k in keys)

def gate(t, s, c):
    c = Q(c); return ['add', t, s, c.numerator, c.denominator, []]
