"""Certified complex lower endpoint of a global T74 profile with the retained moment engine (as r6 C-hosting endpoint.py).
usage: engine.py OUT.json NAME=PROFILE.json ...  (first NAME is the reference). Also enforces the checker's rank deficit
and halving reserve (M*M > 2*max(profile)**2)."""
import importlib.util, json, sys, time
from fractions import Fraction as Q
from decimal import Decimal, getcontext
from pathlib import Path
getcontext().prec = 60
S = Path(__file__).resolve().parents[4]
MC = S / 'wt-566/research/complex-k492-owner-repair/vendor/multicold/engines'
spec = importlib.util.spec_from_file_location('mc_moment', MC / 'moment.py'); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
m, live = 73, 896 * 74
out = {}
for arg in sys.argv[2:]:
    name, path = arg.split('=', 1); d = json.load(open(path)); H = {int(k): v for k, v in (d.get('profile', d)).items()}
    deficit_ok = m * live - sum(r * n for r, n in H.items()) == 320 * 74
    halving_ok = m * m > 2 * max(H) ** 2
    t = time.time(); b = Q(M.certify(H, m, live, False)['lower']); bc = Q(M.certify(H, m, live, True)['lower'])
    out[name] = dict(profile={str(k): v for k, v in sorted(H.items())}, deficit_ok=deficit_ok, halving_ok=halving_ok,
                     complex_lower=str(b), conservative_complex_lower=str(bc),
                     complex_lower_decimal=str(Decimal(b.numerator) / Decimal(b.denominator))[:40], seconds=round(time.time() - t, 1))
    print(name, out[name]['complex_lower_decimal'][:28], 'deficit_ok', deficit_ok, 'halving_ok', halving_ok, out[name]['seconds'], 's', flush=True)
names = list(out)
for n in names[1:]:
    d = Q(out[n]['complex_lower']) - Q(out[names[0]]['complex_lower']); dc = Q(out[n]['conservative_complex_lower']) - Q(out[names[0]]['conservative_complex_lower'])
    out[n]['gain'] = dict(native=float(d), conservative=float(dc)); print(n, 'gain', out[n]['gain'], flush=True)
json.dump(out, open(sys.argv[1], 'w'), indent=1)
