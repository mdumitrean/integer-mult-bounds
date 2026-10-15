"""gen_cmove: compensated single-crossing re-timings ("two-column" moves) of B gates.
Move g = (y += c*s) at base index i forward past its FIRST non-commuting gate h (or backward before the last one), with the
one compensating gate that the exact adjacent-swap identity requires (cases F1-F4 / B1-B4 below), placed adjacent to h.
New positions: immediately past h, and the far end of the free interval (just before the next non-commuting gate).
Exact by construction (local identity, all values/suffix effects constant on the free interval); the harness re-screens.
Gate format: ['add', t, s, num, den, frame] (t += num/den * s), ['scale', t, num, den, frame]."""
import json, sys
from fractions import Fraction as Q
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import common
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
def gate(t, s, c): c = Q(c); return ['add', t, s, c.numerator, c.denominator, []]
def interacts(g, h):
    """None if h commutes with g = (y += c s); else (case, data). Blocking pairs return ('block', None)."""
    y, s = g[1], g[2]
    if h[0] == 'scale':
        if h[1] == s: return ('S', coef(h))           # scale s
        if h[1] == y: return ('Y', coef(h))           # scale y
        return None
    t, u = h[1], h[2]
    if t == s and u == y: return ('block', None)      # s += c' y
    if t == s: return ('W', (u, coef(h)))             # s += c' u (u != y)
    if u == y: return ('R', (t, coef(h)))             # z += c'' y (z != s)
    if t == y and u == s: return None
    return None
def gen(w):
    B = w['B']; n = len(B); out = []
    def edit(i, newpos, comp_pos, comp):
        g = list(B[i][:5]) + [[]]
        return dict(delete=[i], insert=[[newpos, g], [comp_pos, comp]])
    for i, g in enumerate(B):
        if g[0] != 'add': continue
        y, s, c = g[1], g[2], coef(g)
        # forward
        k = next((k for k in range(i + 1, n) if interacts(g, B[k])), None)
        if k is not None:
            kind, d = interacts(g, B[k])
            if kind != 'block':
                k2 = next((m for m in range(k + 1, n) if interacts(g, B[m])), n)
                if kind == 'W': u, c1 = d; comp, cp = gate(y, u, -c * c1), k + 1            # F1
                elif kind == 'S': comp, cp = gate(y, s, -c * (d - 1)), k                    # F2 (before h)
                elif kind == 'R': z, c2 = d; comp, cp = gate(z, s, c2 * c), k + 1           # F3
                else: comp, cp = gate(y, s, (d - 1) * c), k + 1                             # F4
                if comp[3] != 0 and comp[1] != comp[2]:
                    for p in sorted({k + 1, k2}):
                        out.append(dict(id=f'F{kind}-{i}-past{k}-to{p}', g=i, h=k, dir='F', kind=kind, ed=edit(i, p, cp, comp)))
        # backward
        k = next((k for k in range(i - 1, -1, -1) if interacts(g, B[k])), None)
        if k is not None:
            kind, d = interacts(g, B[k])
            if kind != 'block':
                k0 = next((m for m in range(k - 1, -1, -1) if interacts(g, B[m])), -1)
                if kind == 'W': u, c1 = d; comp, cp = gate(y, u, c * c1), k + 1             # B1
                elif kind == 'S': comp, cp = gate(y, s, c * (d - 1)), k                     # B2 (before h)
                elif kind == 'R': z, c2 = d; comp, cp = gate(z, s, -c2 * c), k + 1          # B3
                else: comp, cp = gate(y, s, -(d - 1) * c), k + 1                            # B4
                if comp[3] != 0 and comp[1] != comp[2]:
                    for p in sorted({k, k0 + 1}):
                        out.append(dict(id=f'B{kind}-{i}-before{k}-to{p}', g=i, h=k, dir='B', kind=kind, ed=edit(i, p, cp, comp)))
    return out
if __name__ == '__main__':
    w = common.load('base'); c = gen(w)
    import collections
    print(len(c), collections.Counter(x['dir'] + x['kind'] for x in c))
    json.dump(c, open(sys.argv[1], 'w'))
