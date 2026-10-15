"""Per-rank moment weights c[r] (toolkit units, 2^-unit_bits) at b, for the packing economics."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'toolkit'))
import frames as F
b = sys.argv[1]; out = sys.argv[2]
C = F.Costs(b)
c = {r: C.c[r] for r in sorted(C.c) if r > 0}
res = dict(b=b, unit_bits=C.unit_bits, M_DIM=F.M_DIM if hasattr(F, 'M_DIM') else None, c=c,
           per_unit={r: c[r] / r for r in c}, marginal={r: c[r + 1] - c[r] for r in c if r + 1 in c})
json.dump(res, open(out, 'w'), indent=1)
for r in (1, 2, 3, 4, 5, 8, 9, 16, 32, 44, 47, 48): print(r, c[r], round(c[r] / r, 1), res['marginal'].get(r))
