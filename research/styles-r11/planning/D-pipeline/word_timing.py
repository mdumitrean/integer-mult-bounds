"""Lane D grounding: cost of the BORROW-WORD event model (wordmodel.Word, bounds.Bounds from #2745's handoff code vendored in
J-dim1/code) on #2802's base word, the per-register climb strings it yields, and one 90-digit root solve.  Run with -I."""
import sys, time, json, gzip, collections
from decimal import Decimal as Dc, getcontext
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
CODE = str(_ROOT / "research/t74-r10-hosting-leads/J-dim1/code")
sys.path.insert(0, CODE)
W = str(_ROOT / "research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz")
t = time.time()
from wordmodel import Word
Wd = Word(W); t_word = time.time() - t
print(f"wordmodel.Word: {t_word:.2f}s | events {Wd.T_END} | live regs {len(Wd.live)} | helpers {len(Wd.helpers)} | paid {dict(sorted(Wd.paid.items()))}")
# climb strings: per register, the sequence of frame dimensions over time
climbs = Wd.climbs
lens = collections.Counter(len(v) for v in climbs.values())
print("climb-string lengths (jumps per register):", dict(sorted(lens.items())), "| registers with climbs", len(climbs))
jumps = collections.Counter(d for v in climbs.values() for (_, d, _, _) in v)
print("jump-rank histogram (== local profile minus centre descents):", dict(sorted(jumps.items())))
ex = sorted(climbs.items(), key=lambda kv: -len(kv[1]))[0]
print("longest climb string: register", ex[0], [(tm, d) for (tm, d, _, _) in ex[1]])
t = time.time()
from bounds import Bounds
b = Bounds(W); t_b = time.time() - t
print(f"bounds.Bounds (lo/hi lattice over all refits): {t_b:.2f}s | gates with lo<hi: {sum(1 for k in b.lo if len(b.lo[k]) < len(b.hi[k]))} of {len(b.lo)}")
# 90-digit root of the complete profile (r10/mine/root.py method)
getcontext().prec = 90
prof = {1: 1603728, 2: 431568, 3: 185082, 4: 85248, 5: 27194, 8: 5328, 32: 1, 48: 26558}
def Mm(p, k): return sum(Dc(c) * Dc(r) / Dc(73) * (k * (Dc(73) / Dc(r)).ln()).exp() for r, c in p.items())
t = time.time(); lo, hi = Dc(0), Dc("0.01")
for _ in range(280):
    mid = (lo + hi) / 2
    if Mm(prof, mid) < Dc(66304): lo = mid
    else: hi = mid
print(f"90-digit bisection root: {str(lo)[:30]}  ({time.time()-t:.2f}s; expected 0.0017177949841186346638272...)")
