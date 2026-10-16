#!/usr/bin/env python3
"""Lane C grounding, part 4: the coalescence ceiling of mapping 2 (frame climbs as heights).

A paid child of rank r is a monotone frame-dimension jump of size r on one register chain (paid_profile).
For one register with total climb W split into jumps r_1..r_k, concavity ((a+b)^p <= a^p + b^p, 0<p<1)
makes the moment contribution smallest when k = 1.  So the profile in which every register climbs in ONE
jump (rank = its width) is a valid ceiling for every frame-only or gate-order-only edit at fixed register
widths and fixed owner fill.  Exact per-register climbs of the #2802 base word: 408 helpers (widths
{4:26,5:2,7:62,8:78,9:240}), 112 ports (dim 1 -> perp(port) dim 8: climb 7), 112 target rows (0 -> 9),
plus the 8 rank-8 private cut copies (not climbs; kept as they are).  Mass check: 5188 per call.
usage: ground_ceiling.py INPUT_DIR
"""
import gzip, json, sys
from pathlib import Path
from mpmath import mp, mpf
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ground_fill import kappa_root, MASS, CALLS
mp.dps = 40
IN = Path(sys.argv[1])
with gzip.open(IN / 'WORD-base.json.gz', 'rt') as fh: w = json.load(fh)
def dim(F):
    rows = []
    for x in F or []:
        for r in rows: x = min(x, x ^ r)
        if x: rows.append(x)
    return len(rows)
removed = set(w['removed']); se = {int(k): dim(v) for k, v in w['start_extra'].items()}; hf = {int(k): dim(v) for k, v in w['helper_final'].items()}
coal = {}
def add(r, n=1): coal[r] = coal.get(r, 0) + n
for reg in range(224, 704):
    if reg in removed: continue
    add(hf.get(reg, 9) - se.get(reg, 0))
for port in w['ports']:                       # ports climb from [port] (dim 1) to perp(port) (dim 8)
    add(8 - 1)
for t in range(112):                          # target rows climb from the empty frame to full
    add(9)
add(8, 8)                                      # the eight rank-8 private cut copies (unchanged)
local = {int(r): n for r, n in w['report']['local_profile'].items()}
assert sum(r * n for r, n in coal.items()) == sum(r * n for r, n in local.items()) == 5188, (coal, local)
idle = {1: 17316, 3: 6594, 5: 9878, 32: 1, 48: 26558}
def glob(loc):
    p = {r: CALLS * n for r, n in loc.items()}
    for r, n in idle.items(): p[r] = p.get(r, 0) + n
    assert sum(r * n for r, n in p.items()) == MASS
    return p
k_real = kappa_root(glob(local)); k_coal = kappa_root(glob(coal))
print('local profile      ', dict(sorted(local.items())), 'children', sum(local.values()))
print('coalesced profile  ', dict(sorted(coal.items())), 'children', sum(coal.values()))
print('kappa_real         ', mp.nstr(k_real, 22))
print('kappa_coalesced    ', mp.nstr(k_coal, 22), ' (ceiling for frame/order edits at fixed widths and fill)')
print('gap                ', mp.nstr(k_coal - k_real, 8))
# what one fully merged register is worth: e.g. a width-9 helper climbing (1,1,2,5) -> (9)
for part in ([1, 1, 2, 5], [1, 3, 5], [4, 5], [1, 8], [1, 1], [2, 2], [4, 4]):
    loc = dict(local)
    for r in part: loc[r] -= 1
    loc[sum(part)] = loc.get(sum(part), 0) + 1
    print('merge', part, '->', sum(part), 'per call on both words: dkappa', mp.nstr(kappa_root(glob(loc)) - k_real, 6))
json.dump(dict(local=local, coalesced=coal, kappa_real=mp.nstr(k_real, 25), kappa_coalesced=mp.nstr(k_coal, 25)),
          open(Path(__file__).resolve().parent / 'ground_ceiling.out.json', 'w'), indent=1)
