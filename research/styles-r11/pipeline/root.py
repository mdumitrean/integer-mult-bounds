# Independent root of sum_r c_r (r/73) (73/r)^k = 66304 (decimal, 90 digits, bisection).
import json, sys
from decimal import Decimal as D, getcontext
getcontext().prec = 90
def M(prof, k, wires=66304, dimension=73):
    return sum(D(c) * D(r) / D(dimension) * (k * (D(dimension) / D(r)).ln()).exp() for r, c in prof.items())
def root(prof, wires=66304, dimension=73):
    prof = {int(r): c for r, c in prof.items() if c}
    terms = [(D(c) * D(r) / D(dimension), (D(dimension) / D(r)).ln())
             for r, c in prof.items()]
    def value(k):
        return sum(a * (k * delay).exp() for a, delay in terms)
    lo, hi = D(0), D('0.01')
    if not value(lo) <= D(wires) <= value(hi):
        raise ValueError('profile root is outside the registered [0,0.01] bracket')
    for _ in range(280):
        mid = (lo + hi) / 2
        if value(mid) < D(wires): lo = mid
        else: hi = mid
    return lo
if __name__ == '__main__':
    profs = {
     'candidate (retired5)': {1:1606392, 2:427572, 3:189078, 4:85248, 5:25862, 8:5328, 32:1, 48:26558},
     'F double move': {1:1603728, 2:431568, 3:185082, 4:85248, 5:27194, 8:5328, 32:1, 48:26558},
    }
    out = {}
    for n, p in profs.items():
        mass = sum(r * c for r, c in p.items()); k = root(p); out[n] = k
        print(n, 'mass', mass, 'root', str(k)[:44])
    print('margin F - candidate', str(out['F double move'] - out['candidate (retired5)'])[:20])
    print('margin F - 0.001717256973467002', str(out['F double move'] - D('0.001717256973467002'))[:20])
