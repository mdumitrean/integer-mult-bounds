"""Shared context for the narrowed-inventory owner-map work (r6 C-hosting).
Builds PR1319's independent_core context (windows, families, charts) from the retained T74 replay inputs, and exposes
the current owner map, dispatch and provider widths/profiles of the 566+554 supplier (#1672 new/PLAN.json)."""
import collections, copy, gzip, hashlib, json, sys
from pathlib import Path
S = Path(__file__).resolve().parents[4]                      # scratchpad/
P1319 = S / 'wt-566/research/global-mixed-t74-exact-fill'
F = S / 'r2/full566b'                                        # retained fresh T74 replay work dir (#1625 rev2 run)
BASE8 = F / 'parent/layout/demotions1148-round43/baseline-replay/parent/t16/global8/base'
NATIVE = F / 'parent/layout/packing74-pivot566/native-extra/local'
PLAN72 = S / 'r3/vendor/pr1672/research/gmx-t74-k554-signed-001/new/PLAN.json'
sys.path.insert(0, str(P1319))
import independent_core as A                                  # PR1319's own checker (vendored, unchanged)
def rd(p):
    b = Path(p).read_bytes(); return json.loads(gzip.decompress(b) if str(p).endswith('.gz') else b)
def dump(p, x):
    b = json.dumps(x, sort_keys=True, separators=(',', ':')).encode()
    Path(p).write_bytes(gzip.compress(b, mtime=0) if str(p).endswith('.gz') else b)
def content_sha(x): return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def load():
    plan19 = rd(P1319 / 'PLAN.json'); plan72 = rd(PLAN72)
    roles = rd(P1319 / 'OWNERS.json.gz'); dispatch = {(s, r): p for s, r, p in rd(P1319 / 'DISPATCH.json')}
    parent = rd(BASE8 / 'split-centres/GLOBAL-TEMPLATE.json.gz'); phases = rd(BASE8 / 'work/complex-nine-native/DATA-PHASES.json')
    canonical = rd(BASE8 / 'split-centres/CANONICAL-WORD.json.gz')
    word, replay = rd(NATIVE / 'CANONICAL-WORD.json.gz'), rd(NATIVE / 'INDEPENDENT-LOCAL-REPLAY.json')
    widths = {p: plan72['provider_registry'][p]['widths'] for p in ('gauge44', 'extra')}
    paid = {p: collections.Counter({int(k): v for k, v in plan72['provider_registry'][p]['actual_paid_profile'].items()}) for p in widths}
    A.EXPECTED_WIDTHS = collections.Counter(widths['extra']); A.T = plan19['T']
    A.EXPECTED_IDLE = {48: 22748}
    ctx = A.make_context(parent, phases, canonical['ports'], word, replay, roles)
    ctx['max_local_prefix'] = max(x['prefix_bits_upper'] for x in replay['local'].values())
    return dict(A=A, ctx=ctx, roles=roles, dispatch=dispatch, widths=widths, paid=paid, plan19=plan19, plan72=plan72)
def set_inventory(L, dispatch, widths, paid, idle):
    """Point the checker context at a dispatch and per-provider widths/paid profiles (no local word needed)."""
    ctx = dict(L['ctx']); ctx['call_widths'] = {c: widths[p] for c, p in dispatch.items()}
    agg = collections.Counter()
    for p in dispatch.values(): agg.update(paid[p])
    ctx['aggregate_paid'] = agg; ctx['local_profiles'] = {p: dict(paid[p]) for p in paid}
    ctx['width_inventories'] = {p: dict(collections.Counter(w)) for p, w in widths.items()}
    L['A'].EXPECTED_IDLE = dict(idle); return ctx
