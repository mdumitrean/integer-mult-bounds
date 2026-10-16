# Independent root of sum_r c_r (r/73) (73/r)^k = 66304 (decimal, 90 digits, bisection).
import json, sys
from decimal import Decimal as D, getcontext
getcontext().prec = 90
def M(prof, k):
    return sum(D(c) * D(r) / D(73) * (k * (D(73) / D(r)).ln()).exp() for r, c in prof.items())
def root(prof):
    lo, hi = D(0), D('0.01')
    for _ in range(280):
        mid = (lo + hi) / 2
        if M(prof, mid) < D(66304): lo = mid
        else: hi = mid
    return lo
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
