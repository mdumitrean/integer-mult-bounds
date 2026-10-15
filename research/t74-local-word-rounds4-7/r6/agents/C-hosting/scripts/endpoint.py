"""Certified complex lower endpoint (and PR1319-style outer kappa) of a global T74 profile, with the retained engines
(research/complex-k492-owner-repair/vendor/multicold/engines, as used by the #1625 verifier).
usage: endpoint.py OUT.json NAME=PROFILE_JSON_OR_CHECK.json ..."""
import importlib.util, json, sys, time
from fractions import Fraction as Q
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec = 60
S = Path(__file__).resolve().parents[4]; ROOT = S / 'wt-566'
MC = ROOT / 'research/complex-k492-owner-repair/vendor/multicold/engines'
def load(n, p): s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
M = load('mc_moment', MC / 'moment.py')
m, live = 73, 896 * 74
out = {}
for arg in sys.argv[2:]:
    name, path = arg.split('=', 1); d = json.load(open(path)); H = {int(k): v for k, v in (d['profile'] if 'profile' in d else d).items()}
    assert m * live - sum(r * n for r, n in H.items()) == 320 * 74, 'rank deficit'
    t = time.time(); b = Q(M.certify(H, m, live, False)['lower']); bc = Q(M.certify(H, m, live, True)['lower'])
    out[name] = dict(profile={str(k): v for k, v in sorted(H.items())}, complex_lower=str(b), conservative_complex_lower=str(bc),
                     complex_lower_decimal=str(Decimal(b.numerator) / Decimal(b.denominator)), seconds=round(time.time() - t, 1))
    print(name, out[name]['complex_lower_decimal'][:30], out[name]['seconds'], flush=True)
names = list(out)
for n in names[1:]:
    d = Q(out[n]['complex_lower']) - Q(out[names[0]]['complex_lower']); dc = Q(out[n]['conservative_complex_lower']) - Q(out[names[0]]['conservative_complex_lower'])
    out[n]['gain_over_' + names[0]] = dict(complex_lower=str(Decimal(d.numerator) / Decimal(d.denominator)), conservative=str(Decimal(dc.numerator) / Decimal(dc.denominator)))
    print(n, 'gain over', names[0], out[n]['gain_over_' + names[0]], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
