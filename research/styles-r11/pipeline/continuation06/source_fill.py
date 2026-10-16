"""Pinned PR2979 T74 fill and its literal five-copy T370 interleaving.

Only trusted, hash-pinned local r11 implementations are imported.  The complete
PR2979 acquisition, including every fetched Python file, is inert input.  Call
``prepare()`` once in the parent after registration, then inherit the state in
the common fork pool.  No constructor, checker or search runs at import time.

The existing independent owner checker is fixed to T74.  It checks the source
directly; the lifted baseline has a separately checked exact five-copy
bijection.  The trusted fill audit checks every lifted role.  Its only adapted
binding is its diagnostic floating root, whose historical 66304 denominator is
inapplicable at T370: that non-decision output is explicitly disabled.  All
owner, window, mask, family, profile and mass checks use its unchanged code.

Credit the PR2979 construction and complete retained CREDITS/NOTICE/SOURCES,
Tekalign's independent owner checker, and the source authors retained by fill.py.
This module makes no native, physical implementation, outer or theorem claim.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from dataclasses import replace
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import time
import types


HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RR = PIPELINE.parent
ROOT = RR.parents[1]
TRUSTED = {
    'source': ('research/styles-r11/pipeline/continuation05/source2979.py',
               'fb8c5f84e076ebd0514800139b9310539ca56f4808dd92889744dee067e65bbd'),
    'fill': ('research/styles-r11/pipeline/fill.py',
             '9ca05b47016ddbbb4a6713c981932d63a6eaecdd27f3604fcfb66877f239fc4a'),
    'wordio': ('research/styles-r11/pipeline/wordio.py',
               'a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4'),
    'owners': ('research/t74-joint-twelve-retired7/independent_owners.py',
               '219e16a7f35c5c9e9640760c28ad49a17b546c9f32bdf57dd76c30b5dd096aa6'),
}
FILES = {
    'fill': 'allocation/FILL.json.gz',
    'order': 'allocation/ORDER.json',
    'dispatch': 'allocation/DISPATCH.json',
    'providers': 'allocation/PROVIDERS.json',
    'profile': 'allocation/PROFILE.json',
    'plan': 'allocation/vendor/PLAN.json.gz',
    'template': 'allocation/vendor/TEMPLATE.json.gz',
    'allocation_pins': 'ALLOCATION-PINS.json',
}
EXPECTED_ALLOCATION_PINS_SHA = 'd0a4e7fb9f629534e7e258a5bfd9e5f9e47564277f677a54ca77d5148ffaabf9'
PROVIDER_ALIASES = {'gauge44': 'base', 'extra': 'extra'}
FACTOR = 5
BASE_REPLICAS = 74
REPLICAS = 370
BASE_LIVE = 66304
LIVE = 331520
PHYSICAL_NAMESPACE = 332029
HELPERS = 408
BUFFERS = 91
BASE_MASS = 4816512
MASS = 24082560
_MODULES = None
_STATE = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def semantic_sha(value):
    raw = json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(raw).hexdigest()


def _rows_sha(rows):
    """Order-sensitive fixed-width binary digest, avoiding a second JSON copy."""
    h = hashlib.sha256(b'CONT06-ROWS-i64be-v1\0')
    for row in rows:
        need(len(row) == 6 and all(type(v) is int for v in row), 'six integer role coordinates')
        h.update(struct.pack('>6q', *row))
    return h.hexdigest()


def source_manifest():
    pins = {}
    for relative, expected in TRUSTED.values():
        raw = (ROOT / relative).read_bytes()
        need(hashlib.sha256(raw).hexdigest() == expected, 'trusted source drift: ' + relative)
        pins[relative] = expected
    return pins


def _load_trusted(key):
    relative, expected = TRUSTED[key]
    path = ROOT / relative
    need(hashlib.sha256(path.read_bytes()).hexdigest() == expected, 'trusted import hash: ' + key)
    name = 'styles_cont06_source_fill_' + key
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _modules():
    global _MODULES
    need(not sys.flags.optimize, 'enabled assertions required')
    source_manifest()
    if _MODULES is None:
        sys.dont_write_bytecode = True
        source = _load_trusted('source')
        fill = _load_trusted('fill')
        owners = _load_trusted('owners')
        wordio, admission = source._modules()
        need(source.TRUSTED['wordio'] == TRUSTED['wordio'], 'transitive canonical-word pin')
        # Isolated globals: do not modify the frozen fill module or audit code.
        namespace = dict(fill.audit.__globals__)
        namespace['kappa_float'] = lambda profile: None
        audit_lift = types.FunctionType(fill.audit.__code__, namespace,
            name='audit_with_disabled_historical_stock_diagnostic',
            argdefs=fill.audit.__defaults__, closure=fill.audit.__closure__)
        _MODULES = dict(source=source, fill=fill, owners=owners, wordio=wordio,
                        local_admission=admission, audit_lift=audit_lift)
    return _MODULES


def _profile(value):
    out = {}
    for rank, count in value.items():
        r = int(rank)
        need(str(r) == str(rank) and 0 < r < 73, 'canonical positive recursive rank')
        need(type(count) is int and count >= 0, 'nonnegative integer profile count')
        if count:
            out[r] = count
    return dict(sorted(out.items()))


def _read_checked(source, pin):
    raw = source._checked_bytes(RR / pin['local_path'], pin['sha256'], pin['bytes'], pin['git_blob'])
    return json.loads(gzip.decompress(raw) if pin['local_path'].endswith('.gz') else raw)


def provenance():
    """Complete original credits and immutable allocation bindings; no audit."""
    modules = _modules()
    source = modules['source']
    result = source.provenance()
    meta = source._metadata()
    result['fill_source_files'] = [deepcopy(meta['files'][name]) for name in FILES.values()]
    result['trusted_sources'] = dict(result['trusted_sources'], **source_manifest())
    result['adapter_scope'] = ('Exact finite owner lift and unchanged source-word local algebra; '
        'native/physical/precision/outer implementation transfer is a separate obligation.')
    return result


def prepare():
    """Load words, FILL, plan and template once; return a small JSON summary."""
    global _STATE
    if _STATE is not None:
        return deepcopy(_STATE['summary'])
    modules = _modules()
    S, F, W = (modules[k] for k in ('source', 'fill', 'wordio'))
    records = S.prepare()  # Includes all112 bytes /111 manifest entry checks.
    meta = S._metadata()
    data = {name: _read_checked(S, meta['files'][name]) for name in FILES.values()}
    data['CLAIM.json'] = meta['claim']
    data['data/WORD-base.json.gz'] = records['base']['raw']
    data['data/WORD-extra.json.gz'] = records['extra']['raw']
    allocation_pins = data[FILES['allocation_pins']]
    need(meta['files'][FILES['allocation_pins']]['sha256'] == EXPECTED_ALLOCATION_PINS_SHA,
         'allocation manifest digest')
    need(all(name in meta['files'] and meta['files'][name]['sha256'] == digest
             for name, digest in allocation_pins.items()), 'complete allocation source binding')
    claim, plan, template = (data[k] for k in ('CLAIM.json', FILES['plan'], FILES['template']))
    literal, providers = data[FILES['fill']], data[FILES['providers']]
    need(claim['fill_sha256'] == meta['files'][FILES['fill']]['sha256'], 'claim literal fill binding')
    need((plan['M'], plan['K'], plan['L'], plan['T'], plan['live'], plan['deficit']) ==
         (73, 4, 9, 37, 33152, 11840), 'inherited T37 plan geometry')
    need((claim['replicas'], claim['calls'], claim['live_families'], claim['helpers'],
          claim['zero_buffers'], claim['physical_families']) == (74, 666, 66304, 408, 91, 66813),
         'literal source geometry and declared namespace')
    need(template['m'] == 73 and template['replica_lift']['replicas'] == 37 and
         template['replica_lift']['data_stock'] == 33152, 'inherited template data stock')
    # Old template bank stock/native namespace is never used as a new denominator.
    need(len(template['idle_children']) == 18 * 112 and
         {(x['child'], x['port']) for x in template['idle_children']} ==
         {(c, p) for c in range(18) for p in range(112)}, 'all template child/port bins')
    need(literal['columns'] == F.COLUMNS and literal['dispatch_overrides'] == [],
         'registered source columns and empty override list')
    base_order = [tuple(call) for call in data[FILES['order']]]
    need(base_order == [(s, r + 37*k) for s, r in plan['order'] for k in range(2)],
         'literal T74 order is the pinned two-copy T37 interleaving')
    need(len(base_order) == len(set(base_order)) == 666 and
         set(base_order) == {(s, r) for s in range(9) for r in range(BASE_REPLICAS)},
         'complete unique T74 call coverage')
    dispatch_rows = data[FILES['dispatch']]
    base_dispatch = {(s, r): pid for s, r, pid in dispatch_rows}
    need(len(dispatch_rows) == len(base_dispatch) == 666 and set(base_dispatch) == set(base_order),
         'complete unique source dispatch')
    need(set(providers) == set(base_dispatch.values()) == set(PROVIDER_ALIASES),
         'exact gauge44/base and extra provider aliases')
    words, canonical_widths, canonical_profiles = {}, {}, {}
    for pid, record_name in PROVIDER_ALIASES.items():
        rec = records[record_name]
        need(S.semantic_sha(rec['raw']) == rec['original_semantic_sha256'], 'unchanged source word')
        word = W.WordData(rec['raw'], rec['attribution'])
        widths = tuple(len(word.end[h]) - len(word.start[h]) for h in word.helpers)
        need(len(widths) == HELPERS and widths == tuple(providers[pid]['widths']),
             'ordered canonical helper/provider width equality')
        need(dict(Counter(widths)) == rec['expected_inventory'] and
             word.paid == _profile(providers[pid]['actual_paid_profile']) == rec['expected_profile'],
             'canonical local profile and width inventory')
        need(sum(r*n for r, n in word.paid.items()) == sum(widths) + 1856,
             'complete local rank-mass identity')
        words[pid] = word
        canonical_widths[pid], canonical_profiles[pid] = widths, dict(word.paid)
    base_rows = [tuple(row) for row in literal['rows']]
    literal['rows'] = base_rows  # Retain one parsed source row collection.
    need(len(base_rows) == 666 * HELPERS == 271728, 'source role count')
    order = [(s, r + BASE_REPLICAS*k) for s, r in base_order for k in range(FACTOR)]
    dispatch = {(s, r + BASE_REPLICAS*k): pid
                for (s, r), pid in base_dispatch.items() for k in range(FACTOR)}
    rows = [(FACTOR*t+k, h, o+BASE_REPLICAS*k, c, p, off)
            for t, h, o, c, p, off in base_rows for k in range(FACTOR)]
    need(len(order) == len(set(order)) == len(dispatch) == 3330 and
         set(order) == {(s, r) for s in range(9) for r in range(REPLICAS)},
         'complete unique T370 call and dispatch coverage')
    need(len(rows) == 1358640, 'five-copy role count')
    base_profile = _profile(data[FILES['profile']])
    need(base_profile == _profile(claim['profile']), 'claim/allocation complete profile binding')
    profile = {r: FACTOR*n for r, n in base_profile.items()}
    need(sum(r*n for r, n in base_profile.items()) == BASE_MASS ==
         2*(73*plan['live']-plan['deficit']) == 72*BASE_LIVE+64*666,
         'T37 to T74 and actual coverage rank-mass identities')
    need(MASS == FACTOR*BASE_MASS == 72*LIVE+64*len(order) ==
         10*(73*plan['live']-plan['deficit']) == sum(r*n for r, n in profile.items()),
         'ten T37 copies / five T74 copies / actual T370 rank-mass identity')
    need(LIVE == FACTOR*BASE_LIVE == 2*4*112*REPLICAS and
         PHYSICAL_NAMESPACE == LIVE+HELPERS+8+BUFFERS+2,
         'live-family scaling and explicit namespace ledger')
    source = provenance()
    source_files = deepcopy(source['fill_source_files'])
    family = {int(c): 2*p + plan['sides'][c] for c, p in plan['pairs'].items()}
    notes = dict(source_pr=2979, source_head=S.HEAD, base_replicas=BASE_REPLICAS,
        actual_replicas=REPLICAS, lift_factor=FACTOR, inherited_template_replicas=37,
        inherited_template_data_stock=33152, live_families=LIVE,
        physical_namespace=PHYSICAL_NAMESPACE, native_physical_admission=False,
        order_rule='(s,r) -> [(s,r+74*k) for k=0..4], in that order',
        row_rule='(t,h,o,c,p,offset) -> (5*t+k,h,o+74*k,c,p,offset)',
        window_rule='Reconstruct from the actual order and unchanged source events; start<t<=stop.',
        inherited_template_bank_stock_excluded=True,
        mass_formula='10*(73*33152-11840)=5*4816512=72*331520+64*3330=24082560')
    base_model = F.FillModel(name='continuation06-pr2979-T74', rows=base_rows,
        order=base_order, widths=[canonical_widths[base_dispatch[c]] for c in base_order],
        local_profiles=[canonical_profiles[base_dispatch[c]] for c in base_order],
        win=F.windows(template, base_order), family=family, expected_profile=base_profile,
        expected_mass=BASE_MASS, sources=source_files, attributions=source['source_attribution'],
        source_notes=dict(notes, actual_replicas=74, lift_factor=1, live_families=BASE_LIVE,
            physical_namespace=66813,
            order_rule='Pinned literal T74 order: each T37(s,r) becomes (s,r),(s,r+37).',
            row_rule='Pinned literal T74 roles; no role-coordinate transformation.',
            mass_formula='2*(73*33152-11840)=72*66304+64*666=4816512'), ports=112)
    model = F.FillModel(name='continuation06-pr2979-T370-five-copy', rows=rows,
        order=order, widths=[canonical_widths[dispatch[c]] for c in order],
        local_profiles=[canonical_profiles[dispatch[c]] for c in order],
        win=F.windows(template, order), family=family, expected_profile=profile,
        expected_mass=MASS, sources=source_files, attributions=source['source_attribution'],
        source_notes=notes, ports=112)
    effective_plan = dict(M=73, K=4, L=9, T=REPLICAS, live=LIVE,
        deficit=10*plan['deficit'], order=order, pairs=plan['pairs'], sides=plan['sides'])
    summary = dict(status='PREPARED', source_pr=2979, source_head=S.HEAD,
        base_replicas=BASE_REPLICAS, replicas=REPLICAS, lift_factor=FACTOR,
        base_calls=666, calls=3330, base_roles=len(base_rows), roles=len(rows),
        helpers_per_call=HELPERS, private_zero_buffers=BUFFERS,
        live_families=LIVE, declared_physical_namespace=PHYSICAL_NAMESPACE,
        physical_implementation_admitted=False, base_profile=base_profile, profile=profile,
        base_rank_mass=BASE_MASS, rank_mass=MASS,
        base_rows_sha256=_rows_sha(base_rows), rows_sha256=_rows_sha(rows),
        row_digest_encoding='SHA256(header CONT06-ROWS-i64be-v1\\0; six signed int64 big-endian coordinates per role)',
        base_order_sha256=semantic_sha(base_order), order_sha256=semantic_sha(order),
        dispatch_sha256=semantic_sha(sorted((s, r, pid) for (s, r), pid in dispatch.items())),
        parsed_large_objects_once=True, complete_acquisition_files=112, manifest_entries=111,
        diagnostic_root_policy='T370 historical hardcoded-stock floating diagnostic disabled; all exact fill-audit code retained.',
        source_attribution=deepcopy(source['source_attribution']), adapter_derivation=deepcopy(notes))
    _STATE = dict(base_model=base_model, model=model, lift_model=model, base_rows=base_rows,
        rows=rows, base_order=base_order, order=order, base_dispatch=base_dispatch,
        dispatch=dispatch, providers=providers, plan=plan, template=template,
        effective_plan=effective_plan, records=records, words=words, data=data,
        file_pins=meta['files'], source=source, summary=summary,
        literal=literal, lifted_fill=dict(columns=F.COLUMNS, dispatch_overrides=[], rows=rows,
            method='Literal five-copy T74 interleaving; no allocation change.'),
        base_initial_dispatch=base_dispatch, dimension=73, wires=LIVE, live=LIVE,
        physical_families=PHYSICAL_NAMESPACE, word_files=dict(S.WORD_FILES))
    _STATE['audit_rows'] = audit_rows
    _STATE['fill_module'] = F
    return deepcopy(summary)


def get_state():
    need(_STATE is not None, 'call prepare() once in parent before pool launch')
    return _STATE


def family_id(owner, child, port, lift=True):
    state = get_state()
    return state['model' if lift else 'base_model'].family_id(owner, child, port)


def audit_rows(rows=None, expected_profile=None, require_profile=True, lift=True):
    """Complete trusted owner audit; only the T370 float diagnostic is disabled."""
    state, modules = get_state(), _modules()
    model = state['model' if lift else 'base_model']
    if expected_profile is not None:
        need(require_profile, 'an explicit expected profile requires profile equality')
        model = replace(model, expected_profile=_profile(expected_profile))
    audit = modules['audit_lift'] if lift else modules['fill'].audit
    result = audit(model, rows=rows, require_profile=require_profile)
    if lift:
        need(result['kappa_diagnostic'] is None, 'historical-stock diagnostic disabled')
        result['diagnostic_root_policy'] = 'Unavailable here: exact pricing uses a separate registered live331520 verifier.'
        result['live_families'] = LIVE
        result['exact_audit_code_unchanged'] = True
        result['only_rebound_global'] = 'kappa_float (diagnostic output only)'
    return result


def _five_copy_bijection():
    state = get_state()
    base, lift = state['base_model'], state['model']
    need(len(lift.rows) == FACTOR*len(base.rows), 'exact role expansion cardinality')
    counts = [0]*FACTOR
    for i, (t, h, owner, child, port, offset) in enumerate(base.rows):
        for k in range(FACTOR):
            expected = (FACTOR*t+k, h, owner+BASE_REPLICAS*k, child, port, offset)
            need(lift.rows[FACTOR*i+k] == expected, 'literal row lift/preimage')
            counts[k] += 1
    for t, (stage, replica) in enumerate(base.order):
        for k in range(FACTOR):
            call = (stage, replica+BASE_REPLICAS*k)
            need(lift.order[FACTOR*t+k] == call and
                 state['dispatch'][call] == state['base_dispatch'][stage, replica],
                 'literal call/dispatch lift/preimage')
            need(lift.widths[FACTOR*t+k] == base.widths[t] and
                 lift.local_profiles[FACTOR*t+k] == base.local_profiles[t],
                 'source-local widths and paid profiles unchanged')
    need(len(lift.win) == FACTOR*len(base.win), 'complete window-copy count')
    for (owner, child), (cap, start, stop) in base.win.items():
        for k in range(FACTOR):
            expected = (cap, -1 if start == -1 else FACTOR*start+k, FACTOR*stop+k)
            need(lift.win[owner+BASE_REPLICAS*k, child] == expected,
                 'actual chronological window equals exact copied event window')
    need(counts == [271728]*FACTOR, 'all five complete source projections')
    return dict(status='PASS_EXACT_FIVE_COPY_BIJECTION', copies=FACTOR,
        projected_role_counts=counts, original_calls=666, lifted_calls=3330,
        original_roles=271728, lifted_roles=1358640,
        disjoint_owner_replica_ranges=[[74*k, 74*(k+1)-1] for k in range(FACTOR)],
        time_projection='t_new=5*t_old+k; the call and owner belong to the same copy k',
        physical_family_projection='(o,c,p)->(o+74*k,c,p), with disjoint owner ranges',
        offsets_and_widths_preserved=True, actual_window_endpoints_checked=True,
        scope='Transfer of the independently audited literal baseline only; not an independent arbitrary-candidate T370 checker.')


def baseline_task(spec):
    """Registered pool task: local words, both complete fills and exact lift."""
    started = time.process_time()
    seed = spec['seed'] if isinstance(spec, dict) else spec
    need(type(seed) is int, 'integer recorded seed')
    state, modules = get_state(), _modules()
    S, I = modules['source'], modules['owners']
    local = {name: S.baseline_task(dict(provider=name, seed=seed))
             for name in ('base', 'extra')}
    base_audit = audit_rows(lift=False)
    independent = I.check(state['plan'], state['template'], state['base_order'],
        state['literal'], state['providers'], state['base_initial_dispatch'],
        state['base_model'].expected_profile)
    need(independent['profile'] == base_audit['profile'] and
         independent['idle'] == base_audit['idle'] and
         independent['window_sha256'] == base_audit['window_sha256'],
         'two independent complete source-owner audits agree')
    bijection = _five_copy_bijection()
    lift_audit = audit_rows(lift=True)
    need(lift_audit['profile'] == {r: FACTOR*n for r, n in base_audit['profile'].items()} and
         lift_audit['idle'] == {r: FACTOR*n for r, n in base_audit['idle'].items()},
         'exact fivefold complete local-plus-idle profile')
    need(lift_audit['rank_mass'] == MASS and lift_audit['roles'] == 1358640 and
         lift_audit['calls'] == 3330, 'entire T370 witness checked')
    return dict(status='PASS', seed=seed, n_permutations=0,
        word_baselines=local, base_audit=base_audit, independent_base_owner_audit=independent,
        five_copy_bijection=bijection, lift_audit=lift_audit,
        preparation=deepcopy(state['summary']), cpu_seconds=time.process_time()-started,
        seed_use='Exact deterministic obligations independently repeated under two recorded seeds.',
        native_physical_outer_admission=False,
        scope='Finite unchanged-word algebra, actual owner chronology and exact replicated invoice only.',
        **provenance())
