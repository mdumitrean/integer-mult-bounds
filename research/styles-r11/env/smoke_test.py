#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Smoke test for the r11 styles package: run from anywhere with `python3 -I research/styles-r11/env/smoke_test.py`.

Checks, in order: (1) every pinned word file has its recorded SHA-256 and Git blob id; (2) every in-tree dependency the plan
relies on exists; (3) every BORROW-WORD loads through #2745's `wordmodel.Word` (its constructor asserts that the recounted
paid profile equals `report.local_profile`); (4) every FULL-WORD loads through the #1186 toolkit's frame graph; (5) the
90-digit moment root of #2802's complete profile reproduces the certified endpoint; (6) the capped pool helper works.
Prints PASS_STYLES_R11_SMOKE on success. Needs only the standard library plus numpy for the toolkit graph (mpmath optional).
"""
import gzip, hashlib, json, os, subprocess, sys, time
from pathlib import Path
if not __debug__:
    raise SystemExit('run without -O: the loaders assert')
PKG = Path(__file__).resolve().parents[1]
ROOT = Path(os.environ.get('IMB_ROOT', PKG.parents[1]))
def require(ok, msg):
    if not ok:
        raise SystemExit('FAIL: ' + msg)
def blob(b): return hashlib.sha1(b'blob %d\0' % len(b) + b).hexdigest()
t0 = time.monotonic()

# 1. pins
pins = json.loads((PKG / 'data/words/PINS.json').read_text())['files']
for name, pin in pins.items():
    p = (PKG / 'data/words' / name) if '/' not in name else (ROOT / name)
    require(p.is_file(), 'missing word ' + name)
    b = p.read_bytes()
    require(hashlib.sha256(b).hexdigest() == pin['sha256'] and blob(b) == pin['git_blob'], 'pin mismatch ' + name)
print('pins OK', len(pins), 'word files', flush=True)

# 2. in-tree dependencies
R7 = 'research/t74-joint-twelve-retired7/'; R10 = 'research/t74-r10-hosting-leads/'
deps = [R7 + 'inputs/' + n for n in ('FILL.json.gz', 'FILL2751.json.gz', 'PLAN.json.gz', 'DISPATCH.json.gz', 'GLOBAL-TEMPLATE.json.gz',
        'PROVIDERS.json', 'PROVIDERS2751.json', 'ORDER.json', 'refit7c_43base.json', 'alias7_43base.json', 'hostmove2_43base.json')]
deps += [R7 + n for n in ('exact_moment.py', 'independent_owners.py', 'packing_cap.py', 'PROFILE.json', 'CLAIM.json', 'retired7_controls.py',
         'vendor/audit_local_pr2679.py', 'evidence/PR2751-CLAIM.json', 'evidence/PR2766-CLAIM.json', 'evidence/PR2745-CLAIM.json',
         'evidence/PR2733-CLAIM.json', 'evidence/PR2767-OUTER-CLAIM.json', 'evidence/retired7/CENSUS-AND-AUGMENTING-PATHS.json')]
deps += [R10 + 'J-dim1/code/' + n for n in ('wordmodel.py', 'bounds.py', 'word_patch.py', 'alias_build.py', 'refit.py', 'audit_local.py', 'borrow_price.py')]
deps += [R10 + n for n in ('deps/toolkit-rev3/frames.py', 'deps/toolkit-rev3/word.py', 'deps/toolkit-rev3/native.py', 'J-dim1/out/CENSUS-b.json',
         'J-dim1/out/eh', 'J-dim1/base-words', 'README.md')]
deps += ['research/community-frontier1094-audit/selected-replay.tar.gz']
for d in deps:
    require((ROOT / d).exists(), 'missing in-tree dependency ' + d)
print('in-tree dependencies OK', len(deps), flush=True)

# 3. BORROW-WORDs through wordmodel.Word (asserts paid profile == report.local_profile)
sys.path.insert(0, str(ROOT / R10 / 'J-dim1/code'))
from wordmodel import Word  # noqa: E402
nb = 0
for name, pin in pins.items():
    if pin['format'] != 'BORROW-WORD':
        continue
    p = (PKG / 'data/words' / name) if '/' not in name else (ROOT / name)
    Wd = Word(str(p))
    require(sum(r * c for r, c in Wd.paid.items()) == sum(int(r) * c for r, c in pin['local_profile'].items()), 'mass ' + name)
    nb += 1
print('BORROW-WORD loader OK', nb, 'words (paid profile == report.local_profile)', flush=True)

# 4. FULL-WORDs through the toolkit frame graph
os.environ.setdefault('IMB_ROOT', str(ROOT))
sys.path.insert(0, str(ROOT / R10 / 'deps/toolkit-rev3'))
import frames as F, word as Wmod  # noqa: E402
nf = 0
for name, pin in pins.items():
    if pin['format'] != 'FULL-WORD':
        continue
    w = F.load_word(str(PKG / 'data/words' / name))
    g = F.Graph(Wmod.inline(w, True), check_literal=True)
    require(len(g.chains) > 100, 'toolkit graph ' + name)
    nf += 1
print('FULL-WORD loader OK', nf, 'words (toolkit frame graph)', flush=True)

# 5. the moment root of #2802's complete profile
from decimal import Decimal as D, getcontext  # noqa: E402
getcontext().prec = 90
prof = {int(k): v for k, v in json.loads((ROOT / R7 / 'PROFILE.json').read_text())['profile'].items()} if 'profile' in json.loads((ROOT / R7 / 'PROFILE.json').read_text()) else None
if prof is None:
    prof = {int(k): v for k, v in json.loads((ROOT / R7 / 'CLAIM.json').read_text())['profile'].items()}
require(sum(r * c for r, c in prof.items()) == 4816512, 'rank mass')
def M(pr, k): return sum(D(c) * D(r) / D(73) * (k * (D(73) / D(r)).ln()).exp() for r, c in pr.items())
lo, hi = D(0), D('0.01')
for _ in range(280):
    mid = (lo + hi) / 2
    if M(prof, mid) < D(66304): lo = mid
    else: hi = mid
require(str(lo).startswith('0.001717794984118634663827'), 'root ' + str(lo)[:40])
print('moment root OK', str(lo)[:34], flush=True)

# 6. pool helper
r = subprocess.run([sys.executable, '-I', str(PKG / 'pipeline/pool.py')], capture_output=True, text=True)
require(r.returncode == 0 and "'TIMEOUT'" in r.stdout, 'pool helper: ' + r.stdout + r.stderr[-500:])
print('pool helper OK', r.stdout.strip(), flush=True)
print('PASS_STYLES_R11_SMOKE', round(time.monotonic() - t0, 1), 's')
