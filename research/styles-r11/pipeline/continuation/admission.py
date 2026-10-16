"""Independent finite admission for continuation candidates.

The coordinator must preregister before calling any audit function, and must
launch workers through styles-r11/pipeline/pool.py.  This module has no pool,
solver, subprocess, automatic experiment, or fetched-code import.

``prepare(record, source_pin)`` accepts an already parent-loaded T74 record.
``audit_fill_candidate(spec)`` accepts a pinned inert FILL.json.gz artifact.
``local_admission(raw, attribution)`` is also available to word constructors.

Finite complex-root separation, native supplier admission, strict global
admission, outer arithmetic, and the inherited theorem are distinct tiers.
The first does not silently stand in for the latter four.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from decimal import Decimal, localcontext
from fractions import Fraction as Q
from functools import lru_cache
import contextlib
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import random
import sys
import time

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RR = PIPELINE.parent
ROOT = RR.parents[1]
HEAD = 'd01045dfb67428679618027dff552f1d032fa999'
DATA_MANIFEST_SHA = '9f515fdcead2753a0fdc176417e26468e6e77eb537fdcd20f53496e00a599567'
PINS_SHA = '4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65'
WORDS = {'gauge44': 'new/borrow/words/BORROW-WORD-43base.json.gz',
         'extra': 'new/borrow/words/BORROW-WORD-43extra.json.gz'}
TRUSTED = {
    'wordio': ('research/styles-r11/pipeline/wordio.py',
               'a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4'),
    'fill': ('research/styles-r11/pipeline/fill.py',
             '9ca05b47016ddbbb4a6713c981932d63a6eaecdd27f3604fcfb66877f239fc4a'),
    'growth': ('research/styles-r11/pipeline/growth.py',
               '4f29eba652ea1c7ca889f784c612a6ab11d8aefe96637d18bd32391532b8f167'),
    'auditor': ('research/t74-joint-twelve-retired7/vendor/audit_local_pr2679.py',
                'a38940094f7d19cd6376aafdd4734fa68eabc9aff4c98c3c4a3e9540328b1c90'),
    'owners': ('research/t74-joint-twelve-retired7/independent_owners.py',
               '219e16a7f35c5c9e9640760c28ad49a17b546c9f32bdf57dd76c30b5dd096aa6'),
    'moment': ('research/t74-joint-twelve-retired7/exact_moment.py',
               'f170292f7983773d4f142afdac4677c1615fb7b781dbabf395200aea886dcade'),
}
_MODULES = {}
_BASE = None
_SOURCE_PIN = None
_KEYS = None
_WORDS = None
_FILE_PINS = None
_PHASES = None
TRUSTED_PHASES = (
    'research/complex-mixed-coldkernel/vendor/pr558/vendor/pr552/complex-global/vendor531/inputs/data-base/work/complex-nine-native/DATA-PHASES.json',
    'c5916ff312678f12aba403847643fbbc29f643acec60bdf836fa56cd3e8251fa')
SOURCE_SPECIFICATIONS = [
    dict(pr=2853, commit=HEAD, path='research/gmx-t74-borrow43-handoff/code/invoice_allcold.py',
         sha256='bb213d0af12218ff7c9c572717e522d8bbeeb2856b87a253f4a7f44e0fd71f15',
         use='Read as inert data only: conservative primitive invoice and all nine exact finite supplier inequalities.'),
    dict(pr=2853, commit=HEAD, path='research/gmx-t74-borrow43-handoff/code/assemble.py',
         sha256='f25e1e870df5d5a16a1e367b3df8843cb01644ab4b75895d7939af81e4fcb833',
         use='Read as inert data only: independent finite invoice equations and supplier/outer boundary.'),
    dict(pr=2853, commit=HEAD, path='research/gmx-t74-borrow43-handoff/independent_core.py',
         sha256='02502a217fe8c9e10229075b50745518beac512c48db20e64c3e06514a4da5b5',
         use='Read as inert data only: exact bridge-event windows and orthogonal residual/spectator chart definition.'),
    dict(pr=2908, commit='51309592971e3b5be935599eed2a95404dc7781e',
         path='research/two-sided-helper-extraction/tools/channel_blocknorm.py',
         sha256='b53ebd53e3948f658c6da4f487a9ea10c9cb0a6acf2435750a32d6efeb9869c0',
         use='Read as inert data only: universal block-energy finite premises; source2917 binds the82-buffer adaptation.'),
    dict(pr=2917, commit='224bd5e56041c40078ff6b5fa7393733a215de5c',
         path='research/paired-helper-extension/evidence/ADAPTER-DERIVATION.json',
         sha256='2e8d4ba717294738780e179d4ffc734c64d6d05a4ad3c50f60b6c64c737a1d5d',
         use='Inert exact source adaptation evidence for unchanged82-buffer native and physical ABI.'),
]

LAYOUTS = {
    '2853': dict(fill='new/borrow-fill/FILL.json.gz', order='new/borrow-fill/ORDER.json',
                 dispatch='new/borrow-fill/DISPATCH.json', providers='new/BORROW-PROVIDERS.json',
                 plan='new/PLAN.json', template='GLOBAL-TEMPLATE.json.gz', profile='PROFILE.json'),
    '2917': dict(fill='allocation/FILL.json.gz', order='allocation/ORDER.json',
                 dispatch='allocation/DISPATCH.json', providers='allocation/PROVIDERS.json',
                 plan='allocation/vendor/PLAN.json.gz', template='allocation/vendor/TEMPLATE.json.gz',
                 profile='allocation/PROFILE.json'),
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def read_data(path):
    """Only inert JSON; this function never treats a path as an executable."""
    path = Path(path)
    need(path.name.endswith(('.json', '.json.gz')), 'only JSON/gzip JSON data accepted')
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.name.endswith('.gz') else raw)


def _module(name):
    relative, digest = TRUSTED[name]
    path = (ROOT / relative).resolve()
    need(sha(path) == digest, 'trusted source drift: ' + relative)
    if name not in _MODULES:
        need(not sys.flags.optimize, 'admission requires enabled assertions')
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location('styles_continuation_admission_' + name, path)
        module = importlib.util.module_from_spec(spec)
        # dataclasses resolves annotations through the defining module.
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _MODULES[name] = module
    return _MODULES[name]


def source_manifest():
    for relative, digest in TRUSTED.values():
        need(sha(ROOT / relative) == digest, 'trusted source drift: ' + relative)
    return {relative: digest for relative, digest in TRUSTED.values()}


def profile(value):
    need(isinstance(value, dict), 'profile object required')
    result = {}
    for rank, count in value.items():
        r = int(rank)
        need(str(r) == str(rank) and 0 < r < 73, 'canonical positive rank below dimension')
        need(type(count) is int and count >= 0, 'nonnegative integer multiplicity')
        if count:
            result[r] = count
    need(result, 'empty paid profile')
    return dict(sorted(result.items()))


def _mass(value):
    return sum(rank * count for rank, count in value.items())


def prepare(record, source_pin=None):
    """Bind an existing parent-loaded T74 record, without running an audit.

    The caller owns heldout_data.prepare and its memory accounting.  No large
    fill/template object is loaded again here.  Hash verification reads bytes,
    but does not create another parsed fill/template.

    A different baseline requires an explicit frozen ``source_pin`` containing
    ``pr``, ``commit`` and ``manifest_sha256``. Its record uses the same inert
    package/manifest contract. No live-head discovery occurs in this module.
    """
    global _BASE, _SOURCE_PIN, _KEYS, _WORDS, _FILE_PINS, _PHASES
    source_manifest()
    need(_BASE is None, 'parent preparation is once-only')
    source_pin = dict(source_pin or dict(pr=2853, commit=HEAD, manifest_sha256=DATA_MANIFEST_SHA))
    need(str(record.get('pr')) == str(source_pin['pr']) and record.get('prepare_error') is None,
         'prepared pinned baseline record required')
    directory = Path(record['directory']).resolve()
    need(directory.is_relative_to(RR.resolve()), 'baseline data directory confinement')
    manifest_path = Path(source_pin.get('manifest_path', directory / 'DATA-MANIFEST.json'))
    if not manifest_path.is_absolute():
        manifest_path = RR / manifest_path
    need(manifest_path.resolve().is_relative_to(directory), 'source manifest confinement')
    need(sha(manifest_path) == source_pin['manifest_sha256'], 'held source manifest pin')
    need(sha(RR / 'data/words/PINS.json') == PINS_SHA, 'inherited attribution pin')
    manifest = read_data(manifest_path)
    need(record['manifest'] == manifest and manifest['commit'] == source_pin['commit'], 'parent record manifest binding')
    file_pins = ({pin['relative_path']: pin for pin in manifest['files']}
                 if isinstance(manifest['files'], list) else manifest['files'])
    need(len(file_pins) == len(manifest['files']), 'unique manifest relative paths')
    for relative, pin in file_pins.items():
        path = ((RR / pin['local_path']) if 'local_path' in pin else
                (directory / 'package' / relative)).resolve()
        need(path.is_relative_to((directory / 'package').resolve()), 'inert source path confinement')
        need(sha(path) == pin['sha256'], 'source file digest: ' + relative)
    data, model = record['data'], record['model']
    keys = LAYOUTS[str(source_pin['pr'])]
    words = record.get('word_files', WORDS)
    need((record['dimension'], record['wires'], model.calls) == (73, 66304, 666), 'fixed T74 geometry')
    need([list(x) for x in model.rows] == data[keys['fill']]['rows'], 'model literal rows')
    need([list(x) for x in model.order] == data[keys['order']], 'model literal order')
    need(set(record['words']) == set(words) == {'gauge44', 'extra'}, 'both pinned providers required')
    for provider, relative in words.items():
        need(record['words'][provider].raw == data[relative], 'canonical word/payload equality')
    _BASE, _SOURCE_PIN, _KEYS, _WORDS, _FILE_PINS = record, source_pin, keys, words, file_pins
    need(sha(ROOT / TRUSTED_PHASES[0]) == TRUSTED_PHASES[1], 'trusted exact data-phase recipe pin')
    _PHASES = read_data(ROOT / TRUSTED_PHASES[0])
    # All imports below are source pinned, stdlib-only at import time.
    for name in TRUSTED:
        _module(name)
    return dict(pr=source_pin['pr'], commit=source_pin['commit'], parent_objects_loaded_once=True,
                source_manifest_sha256=source_pin['manifest_sha256'], trusted_sources=source_manifest(),
                calls=model.calls, roles=len(model.rows),
                word_pins={pid: deepcopy(file_pins[rel]) for pid, rel in words.items()})


def _base():
    need(_BASE is not None, 'prepare(record) must run once in the parent before pool launch')
    return _BASE


def _data(key):
    return _base()['data'][_KEYS.get(key, key)]


def provenance():
    b = _base()
    pins = read_data(RR / 'data/words/PINS.json')['files']
    return dict(source_attribution=[dict(path=key, **value) for key, value in pins.items()] +
                [deepcopy(_FILE_PINS[rel]) for rel in _WORDS.values()],
                inherited_pins_sha256=PINS_SHA, held_manifest_sha256=_SOURCE_PIN['manifest_sha256'],
                baseline_pr=_SOURCE_PIN['pr'], baseline_commit=_SOURCE_PIN['commit'],
                trusted_sources=source_manifest(),
                trusted_data={TRUSTED_PHASES[0]: TRUSTED_PHASES[1]},
                inert_source_specifications=deepcopy(SOURCE_SPECIFICATIONS))


class _MemoryPath:
    def __init__(self, name, payload=b''):
        self.name, self.payload = name, payload

    def read_bytes(self):
        return self.payload

    def write_text(self, text):
        self.payload = text.encode()


def local_admission(raw, attribution):
    """Exact frame/paid bill and free-operator map; no native phase claim."""
    started = time.process_time()
    W, A = _module('wordio'), _module('auditor')
    need(raw.get('kind') == 'BORROW-WORD', 'BORROW-WORD candidate required')
    canonical = W.WordData(raw, attribution)
    payload = json.dumps(raw, separators=(',', ':')).encode()
    inp = _MemoryPath('candidate.json.gz', gzip.compress(payload, mtime=0))
    out, log = _MemoryPath('audit.json'), io.StringIO()
    with contextlib.redirect_stdout(log):
        report = A.run_borrow(inp, out, None, None, raw, payload, time.monotonic())
    need(report['status'] == 'PASS_INDEPENDENT_EXACT_BORROWING_WORD', 'free-algebra audit status')
    need(report['orientations'] == {'forward': 'PASS', 'dual': 'PASS'}, 'both orientations')
    need(report['checked_columns'] == len(canonical.live), 'all independent live columns')
    need(profile(report['local_profile']) == canonical.paid, 'independent local profile parity')
    widths = [len(canonical.end[r]) - len(canonical.start[r]) for r in canonical.helpers]
    need(all(type(w) is int and w > 0 for w in widths), 'positive physical helper widths')
    return dict(status='PASS', tier='finite_local_free_operator_algebra', audit=report,
                paid_profile=canonical.paid, ordered_helpers=canonical.helpers, widths=widths,
                word_semantic_sha256=semantic_sha(raw), source_attribution=deepcopy(attribution),
                cpu_seconds=time.process_time() - started,
                native_clifford_phase_and_gaussian_checked=False,
                parent_global_supplier_and_outer_checked=False)


def _normalized_owner_plan():
    """Exact adapter between two stored deficit conventions; no geometry change."""
    b = _base()
    original = _data('plan')
    M, W, deficit = (original[key] for key in ('M', 'live', 'deficit'))
    if (M, W, deficit) == (73, 33152, 11840):
        need(2 * (M * W - deficit) == 4816512, 'literal T37 doubled coverage')
        return original, dict(original_live=W, original_deficit=deficit,
             independent_checker_live=W, independent_checker_deficit=deficit,
             formula='2*(73*33152-11840)=4816512; all74 replicas checked independently',
             exact_rank_mass=4816512, changed_input_field_only=None)
    need((M, W) == (73, 66304) and type(deficit) is int, 'literal plan geometry')
    total = M * W + deficit
    need(total % 2 == 0, 'integer two-sided deficit')
    adapted = dict(original, deficit=total // 2)
    mass = M * W - deficit
    need(mass == 2 * (M * W - adapted['deficit']) == 4816512,
         'single- and two-sided coverage identities')
    return adapted, dict(original_deficit=deficit, independent_checker_deficit=adapted['deficit'],
                         formula='D_two_sided=(73*W+D_single_sided)/2', exact_rank_mass=mass,
                         changed_input_field_only='internal deficit convention; not a candidate edit')


def _provider_binding():
    b, W = _base(), _module('wordio')
    providers = {}
    word_hashes = {}
    for pid, relative in _WORDS.items():
        raw = b['data'][relative]
        canonical = W.WordData(raw, _FILE_PINS[relative])
        widths = [len(canonical.end[h]) - len(canonical.start[h]) for h in canonical.helpers]
        declared = _data('providers')[pid]
        need(widths == declared['widths'] and canonical.paid == profile(declared['actual_paid_profile']),
             'canonical pinned provider inventory and profile')
        providers[pid] = dict(widths=widths, actual_paid_profile=canonical.paid)
        word_hashes[pid] = dict(compressed_sha256=_FILE_PINS[relative]['sha256'],
                                semantic_sha256=semantic_sha(raw))
    for t, call in enumerate(b['model'].order):
        provider = providers[b['dispatch'][call]]
        need(tuple(provider['widths']) == tuple(b['model'].widths[t]), 'actual dispatched widths')
        need(provider['actual_paid_profile'] == profile(b['model'].local_profiles[t]), 'actual dispatched local bill')
    return providers, word_hashes


def literal_admission(candidate_fill):
    """Two independent literal owner checks on a fixed-word/order/template fill."""
    b, F, I = _base(), _module('fill'), _module('owners')
    original = _data('fill')
    need(candidate_fill['columns'] == original['columns'] == F.COLUMNS, 'literal fill columns')
    need(candidate_fill['dispatch_overrides'] == original['dispatch_overrides'], 'fixed dispatch overrides')
    providers, word_hashes = _provider_binding()
    # require_profile=False derives the candidate's complete profile instead of
    # comparing against the original expected profile. All actual rules remain.
    literal = F.audit(b['model'], rows=candidate_fill['rows'], require_profile=False)
    paid = profile(literal['profile'])
    plan, convention = _normalized_owner_plan()
    initial = {(s, r): pid for s, r, pid in _data('dispatch')}
    independent = I.check(plan, _data('template'), b['model'].order,
                          candidate_fill, providers, initial, paid)
    need(independent['profile'] == paid and independent['idle'] == literal['idle'], 'independent profile/idle parity')
    need(independent['window_sha256'] == literal['window_sha256'], 'independent chronology parity')
    need(_mass(paid) == literal['rank_mass'] == 4816512, 'exact unchanged coverage mass')
    aggregate = Counter()
    for call in b['model'].order:
        aggregate.update(providers[b['dispatch'][call]]['actual_paid_profile'])
    need(Counter(paid) == aggregate + Counter(literal['idle']), 'complete local plus idle identity')
    return dict(status='PASS', profile=paid, idle=literal['idle'], aggregate_local_profile=dict(aggregate),
                rank_mass=4816512, independent_owner_audit=independent,
                literal_fill_audit=literal, deficit_convention=convention,
                fixed_local_words=word_hashes,
                frozen_inputs=dict(order=semantic_sha(b['model'].order),
                    dispatch=semantic_sha(sorted((s, r, pid) for (s, r), pid in b['dispatch'].items())),
                    template=_FILE_PINS[_KEYS['template']]['sha256'],
                    provider_inventory=semantic_sha(_data('providers'))))


def _prior_release_binding():
    """Authenticate stored prior evidence; deliberately not a fresh native run."""
    b = _base()
    need(str(_SOURCE_PIN['pr']) == '2917', 'complete stored-release transfer is scoped to PR2917')
    data = b['data']
    claim, admission = data['CLAIM.json'], data['evidence/ADMISSION-RESULT.json']
    native, native_result = data['evidence/FULL-NATIVE-RECEIPT.json'], data['evidence/FULL-NATIVE-RESULT.json']
    release, invoice = data['evidence/RELEASE-RECEIPT.json'], data['evidence/PHYSICAL-INVOICE.json']
    for field, relative in [('native_receipt_sha256', 'evidence/FULL-NATIVE-RECEIPT.json'),
                            ('release_receipt_sha256', 'evidence/RELEASE-RECEIPT.json')]:
        need(claim[field] == admission[field] == _FILE_PINS[relative]['sha256'], 'prior receipt linkage: ' + field)
    need(native_result['native_receipt_sha256'] == claim['native_receipt_sha256'], 'native result linkage')
    need(claim['source_manifest_sha256'] == native['manifest_sha256'] ==
         native_result['source_manifest_sha256'] == admission['source_manifest_sha256'], 'source manifest linkage')
    need(claim['complete_package_manifest_sha256'] == admission['package_manifest_sha256'] ==
         release['manifest_sha256'], 'integrated prior release manifest linkage')
    need(claim['status'] == 'CONDITIONAL_CANDIDATE_COMPLETE_FINITE_RELEASE' and
         admission['status'] == 'PASS_REPLICA_ORDER_FILL_DERIVATIVE_COMPLETE_RELEASE' and
         release['status'] == 'PASS_RELEASE', 'stored complete release statuses')
    need(native['status'] == 'PASS_COMPOSED_FRESH_NATIVE_PROVIDERS_AND_AUTHENTICATED_CACHE' and
         native_result['status'] == 'PASS_TWO_FRESH_SHARED_KERNEL_NATIVE_CHAINS_AUTHENTICATED_PARENT_REUSE',
         'stored native statuses')
    need(Q(claim['kappa']) == Q(admission['kappa']) == Q(release['kappa_decimal']), 'stored released exponent')
    need(profile(claim['profile']) == profile(admission['profile']) == profile(_data('profile')),
         'stored released complete profile')
    need({s['name'] for s in admission['stages']} ==
         {'owners', 'parent-lift', 'rebind', 'discovery', 'outer-check_ledger.py', 'outer-independent_check.py', 'release'}
         and all(s['exit_code'] == 0 for s in admission['stages']), 'complete prior admission stages')
    need({s['name'] for s in native_result['stages']} == {'fresh-current-base', 'fresh-current-extra'} and
         all(s['exit_code'] == 0 for s in native_result['stages']), 'both prior native provider chains')
    for field, key in [('fill_sha256', 'fill'), ('order_sha256', 'order'), ('dispatch_sha256', 'dispatch')]:
        need(admission[field] == _FILE_PINS[_KEYS[key]]['sha256'], 'prior allocation source binding: ' + field)
    records = {}
    for pid, relative in _WORDS.items():
        tag = 'base' if pid == 'gauge44' else pid
        saved = native['providers'][tag]
        word_sha = _FILE_PINS[relative]['sha256']
        need(saved['word_sha256'] == saved['complete_native_files']['local/FULL-WORD.json.gz'] == word_sha,
             'native proof binds literal unchanged word: ' + pid)
        required = {'STEPS.json', 'local/CANONICAL-WORD.json.gz', 'local/CLIFFORD-RECIPES.json',
                    'local/CLIFFORD-REVIEW.json', 'local/FULL-WORD.json.gz',
                    'local/INDEPENDENT-LOCAL-REPLAY.json', 'local/LOCAL-CHECKS.json',
                    'local/LOCAL-PROGRAMS.json.gz', 'local/RESIDUAL-ADAPTERS.json',
                    'local/SCALAR-FRAME-AUDIT.json', 'local/WARP-RECIPE-CHECKS.json',
                    'local/WRAPPER-CHECKS.json'}
        need(set(saved['complete_native_files']) == required, 'complete listed native artifact coverage')
        for name, digest in saved['complete_native_files'].items():
            need(native['cache_files'][word_sha + '/' + name] == digest, 'native tree receipt parity')
        records[pid] = dict(word_sha256=word_sha, complete_native_files=deepcopy(saved['complete_native_files']),
                            actual_cache_bytes_replayed_here=False)
    owner = data['evidence/EXACT-OWNER-MOMENT.json']
    for relative in (_KEYS[k] for k in ('fill', 'order', 'dispatch', 'providers', 'profile', 'plan', 'template')):
        need(owner['allocation_sha256'][relative] == _FILE_PINS[relative]['sha256'], 'prior owner evidence allocation pin')
    need(invoice['status'] == 'PASS_INDEPENDENT_MIXED_ASYNC_SCALAR_PREFIX_AND_FINITE_INVOICE',
         'stored physical invoice status')
    return dict(status='PASS_SOURCE_BOUND_PRIOR_RELEASE_BINDING', baseline_pr=2917,
                baseline_commit=_SOURCE_PIN['commit'], native_receipt_sha256=claim['native_receipt_sha256'],
                release_receipt_sha256=claim['release_receipt_sha256'],
                physical_invoice_sha256=_FILE_PINS['evidence/PHYSICAL-INVOICE.json']['sha256'],
                integrated_source_manifest_sha256=claim['source_manifest_sha256'],
                integrated_package_manifest_sha256=claim['complete_package_manifest_sha256'],
                unchanged_native_providers=records, inherited_scope=claim['scope'],
                scope='Fresh hash/link checks of previously published evidence; no native cache or prior executable is replayed here.')


def _family_assignment(rows):
    """Check the physical family sets and active-data exclusion independently."""
    b, model = _base(), _base()['model']
    pairs = {event['stage']: event['pair'] for event in _data('template')['recipe'] if event['kind'] == 'local'}
    by_call = [set() for _ in model.order]
    roles = {}
    foreign = 0
    for row in rows:
        t, h, owner, child, port, offset = row
        need((t, h) not in roles, 'one row per call/helper for physical transfer')
        roles[t, h] = tuple(row)
        family = owner * 896 + model.family[child] * 112 + port
        stage, replica = model.order[t]
        active_first = replica * 896 + 2 * pairs[stage] * 112
        need(not active_first <= family < active_first + 224, 'helper family outside the active data pair')
        need(family not in by_call[t], 'same-call physical family injectivity')
        by_call[t].add(family)
        foreign += owner != replica
    need(all(len(x) == 408 for x in by_call), 'every call has408 distinct helper families')
    return roles, by_call, foreign


def _chart_audit(rows):
    """Fresh finite charts, pending-axis disjointness and event-time windows.

    The exact phases are already present in the trusted checkout and hash
    identically to the pinned PR2917 template. No fetched code is executed.
    """
    b, model, template = _base(), _base()['model'], _data('template')
    need(template['exact_data_phase_recipe_sha256'] == TRUSTED_PHASES[1], 'literal source phase binding')
    ports = b['data'][_WORDS['gauge44']]['ports']
    need(ports == b['data'][_WORDS['extra']]['ports'] == _PHASES['ports'], 'unchanged ordered physical ports')
    need(_PHASES['m'] == 73 and len(ports) == len(_PHASES['recipes']) == 112, 'data-phase geometry')
    ranks = {child['child']: child['rank'] for child in template['idle_children']}
    for child in template['idle_children']:
        need(ranks[child['child']] == child['rank'], 'consistent idle rank across physical ports')
    pairs = {e['stage']: e['pair'] for e in template['recipe'] if e['kind'] == 'local'}
    blocks, stage = {}, None
    for index, event in enumerate(template['execution_schedule']):
        if event['kind'] in ('bank_padding_cover_sweep', 'translate_every_live_family'):
            continue
        if event['kind'] == 'local_cover_sweep':
            stage = event['stage']
            blocks[stage] = []
        need(stage is not None, 'source event must follow first local call')
        blocks[stage].append((index, event))
    need(set(blocks) == set(range(9)), 'exact source stage coverage')
    events = [(index, event, replica, t) for t, (stage, replica) in enumerate(model.order)
              for index, event in blocks[stage]]
    projections = defaultdict(list)
    last, windows, call_positions, child_family = {}, {}, {}, {}
    for position, (index, event, replica, t) in enumerate(events):
        projections[replica].append(index)
        kind = event['kind']
        if kind == 'local_cover_sweep':
            call_positions[t] = position
            last[replica, pairs[event['stage']]] = position
        elif kind == 'bridge':
            need(0 <= event['src'] < 4 and 0 <= event['dst'] < 4 and event['src'] != event['dst'] and
                 event['coefficient'] in (-1, 1), 'within-replica unit shear bridge')
            last[replica, event['src']] = last[replica, event['dst']] = position
        elif kind == 'idle_cover_sweep':
            for side, child in enumerate(event['child_indices']):
                if child in ranks:
                    windows[replica, child] = (last.get((replica, event['pair']), -1), position)
                    child_family[child] = (event['pair'], side)
    need(set(projections) == set(range(74)) and all(p == list(range(30)) for p in projections.values()),
         'literal per-replica30-event projection')
    need(len(windows) == 74 * len(ranks) and len(call_positions) == 666, 'complete event-time windows')
    bases, pending_indices = {}, {}
    for port, q in enumerate(ports):
        need(type(q) is int and 0 <= q < 512, 'literal9-bit port')
        zero = next(i for i in range(9) if not (q >> i & 1))
        correction = q ^ (1 << zero)
        axes = list(range(9))
        axes[0], axes[zero] = axes[zero], axes[0]
        basis = [(1 << i) ^ (correction if correction >> i & 1 else 0) for i in axes]
        basis += [1 << i for i in range(9, 73)]
        need(all((x & y).bit_count() % 2 == int(i == j) for i, x in enumerate(basis)
                 for j, y in enumerate(basis)), 'exact orthonormal73-axis port basis')
        recipe = _PHASES['recipes'][port]
        need((recipe['port'], recipe['q']) == (port, q), 'literal phase recipe port order')
        used = defaultdict(set)
        for child, rank in ranks.items():
            pending = recipe['idle_children'][child]['orthogonal_axes']
            need(recipe['idle_children'][child]['rank'] == rank and len(pending) == rank and
                 len(set(pending)) == rank and set(pending) <= set(basis), 'literal pending orthogonal axes')
            family = child_family[child]
            need(not used[family] & set(pending), 'disjoint pending children of each physical family')
            used[family].update(pending)
            pending_indices[port, child] = tuple(basis.index(axis) for axis in pending)
        bases[port] = basis
    chart_keys, digest = set(), hashlib.sha256()
    for t, h, owner, child, port, offset in rows:
        lo, hi = windows[owner, child]
        need(lo < call_positions[t] < hi, 'strict bridge-aware event-time idle interval')
        width = model.widths[t][h]
        key = port, child, offset, width
        if key in chart_keys:
            continue
        chart_keys.add(key)
        pending = pending_indices[port, child]
        occupied = list(pending[offset:offset + width])
        spectators = [i for i in range(73) if i not in occupied][:9 - width]
        permutation = occupied + spectators + [i for i in range(73) if i not in occupied and i not in spectators]
        need(0 < width <= 9 and offset >= 0 and offset + width <= ranks[child], 'literal chart slice bounds')
        need(len(occupied) == width and len(spectators) == 9 - width and
             len(set(occupied + spectators)) == 9 and sorted(permutation) == list(range(73)),
             'exact residual/spectator permutation')
        pending_vectors = _PHASES['recipes'][port]['idle_children'][child]['orthogonal_axes']
        need([bases[port][i] for i in permutation[:width]] == pending_vectors[offset:offset + width],
             'chart binds actual pending-axis slice')
        digest.update(json.dumps([list(key), permutation], separators=(',', ':')).encode() + b'\n')
    return dict(status='PASS_EXACT_EVENT_WINDOWS_AND_RESIDUAL_SPECTATOR_CHARTS',
                checked_roles=len(rows), literal_event_windows=len(windows), source_events_per_replica=30,
                expanded_events=len(events), orthogonal_port_bases=len(bases), unique_charts=len(chart_keys),
                chart_sha256=digest.hexdigest(), pending_child_disjointness_checks=112 * len(ranks),
                exact_phase_source=dict(path=TRUSTED_PHASES[0], sha256=TRUSTED_PHASES[1]),
                construction='Occupied actual pending axes; first9−width unused orthogonal basis axes as spectators; complete to73-axis permutation.',
                scope='Fresh concrete literal windows and family-local isometric charts; native phase recipes remain explicitly reused unchanged.')


def _strict_finite_invoice(candidate_audit, group_order, stock_bits):
    """Independent integer evaluation of all nine finite supplier gates.

    The conservative dedicated-bank envelope depends on the unchanged native
    programs, dispatch and parent stock, not on the helper assignment. The
    candidate's actual residual count is bounded separately before this call.
    """
    invoice, template = _base()['data']['evidence/PHYSICAL-INVOICE.json'], _data('template')
    compiler = 64 * 74 ** 3
    need(invoice['compiler'] == compiler, 'exact compiler allowance')
    for pid, p in invoice['providers'].items():
        adapters = 16 * (max(z['macros'] for z in p['local'].values()) +
                        max(z['warp_events'] for z in p['local'].values()) +
                        sum(profile(p['paid_profile']).values()) + 632 + 8 + 82 + 2) + 64 * 73
        primitive_bound = max(z['real_component_primitives'] for z in p['local'].values()) + adapters * compiler
        need(p['compiler'] == compiler and p['local_adapters'] == adapters and
             p['local_primitive_bound'] == primitive_bound, 'independent native adapter/primitive reserve')
    adapters = max(p['local_adapters'] for p in invoice['providers'].values())
    primitive_bound = max(p['local_primitive_bound'] for p in invoice['providers'].values())
    need(invoice['local_adapters'] == adapters and invoice['local_primitive_bound'] == primitive_bound,
         'complete local reserve maximum')
    wrappers = sum(c['pre_wrappers'] + c['post_wrappers'] for c in invoice['selected_calls']) * 144
    need(invoice['factors_per_wrapper'] == 144 and invoice['wrapper_elementary_factors_charged'] == wrappers,
         'all actual primitive wrapper charges')
    parent_live = 2 * template['live']
    parent_helpers = template['physical'] - template['live'] - 8 - 2
    parent_physical = parent_live + parent_helpers + 8 + 2
    parent_idle = 2 * sum(c['replicas'] for c in template['idle_children'])
    need((parent_live, parent_helpers, parent_physical, parent_idle) == (111664, 504, 112178, 149184),
         'source two-copy dedicated-bank envelope')
    parent_banks, rem = divmod(parent_live - 66304, 9)
    need(rem == 0 and parent_banks > 0, 'dedicated-bank geometry')
    bridge_additions, shifts = 224 * 666, 4 * 112 * 74
    moves = 2 * shifts
    nonlocal_items = (4 * 112 * 74 * 9 + 2 * 112 * 74 * 9 + 2 * 666 * 408 + parent_idle +
                     9 * parent_banks + bridge_additions + shifts + moves + parent_live + parent_physical + wrappers)
    outside = 8 * nonlocal_items + 64 * 73
    pervertex = (invoice['selected_real_component_primitives'] + bridge_additions + shifts + moves + parent_live +
                 (666 * adapters + outside) * compiler + 64 * parent_physical)
    rebased = pervertex + 65 * (66804 - parent_physical) + (66304 - parent_live)
    prior = invoice['retained_prior_overcharge']
    need(prior['policy'] == 'Retain old allowance and add entire fresh mixed recount.' and
         type(prior['previous_pervertex_allowance']) is int and prior['previous_pervertex_allowance'] > 0 and
         prior['added_complete_new_pervertex'] == pervertex, 'retained overcharge binding')
    used = max(pervertex, rebased, prior['previous_pervertex_allowance'] + pervertex)
    need((pervertex, rebased, used) == (invoice['unhosted_pervertex'], invoice['hosted_rebased_pervertex'],
                                      invoice['conservative_pervertex_used']), 'independent full finite invoice')
    need(sum(candidate_audit['idle'].values()) <= parent_idle, 'actual idle children within source reserve')
    stock, streamed_mass = group_order * 66804, group_order * candidate_audit['rank_mass']
    logical = group_order * used + 64
    router = compiler * (logical + 1) * (stock + 1) ** 2
    literal = 2 * 2 ** 30000 * stock ** 2 + 8 * streamed_mass + 4 * stock + 4 + 32 * 73
    total_mass = streamed_mass + 2 ** 100000
    powers = {
        'local_primitive_bound': (primitive_bound, 48),
        'logical': (logical, 6050), 'router': (router, 30000), 'literal': (literal, 100000),
        'mass': (total_mass, 100001), 'precision': (32 * 73 * total_mass ** 2, 210000),
        'tape': (2 * total_mass + 18, 210000),
    }
    certificates = {name: dict(lhs_bit_length=value.bit_length(), rhs_power_of_two=exponent,
                              strictly_less=value < 2 ** exponent,
                              lhs_hex_sha256=hashlib.sha256(format(value, 'x').encode()).hexdigest())
                    for name, (value, exponent) in powers.items()}
    row = 2 * stock_bits + 9909 + 252 + 2 * 2048
    max_rank = max(candidate_audit['profile'])
    certificates['row'] = dict(lhs=row, rhs=20161, gap=20161-row, strictly_less=row < 20161)
    certificates['halving'] = dict(lhs=2*max_rank**2, rhs=73**2, gap=73**2-2*max_rank**2,
                                   strictly_less=2*max_rank**2 < 73**2)
    need(all(c['strictly_less'] for c in certificates.values()), 'all nine strict finite supplier gates')
    need(set(certificates) == set(invoice['strict_checks']) and all(invoice['strict_checks'].values()),
         'same complete finite gate inventory')
    finite = invoice['finite']
    need((router.bit_length(), literal.bit_length(), powers['precision'][0].bit_length(), row) ==
         (finite['router_bits'], finite['literal_bits'], finite['required_C0_bits'], finite['physical_row_coefficient']),
         'fresh exact finite values bind stored invariant bounds')
    return dict(status='PASS_NINE_EXACT_FINITE_SUPPLIER_INEQUALITIES', checks=certificates,
                compiler=compiler, local_adapters=adapters, local_primitive_bound=primitive_bound,
                dedicated_bank_envelope=dict(parent_live=parent_live, parent_physical=parent_physical,
                    parent_helpers=parent_helpers, parent_idle_reserve=parent_idle, banks=parent_banks),
                full_pervertex=pervertex, hosted_rebased_pervertex=rebased, conservative_pervertex=used,
                rank_mass=candidate_audit['rank_mass'], max_child_rank=max_rank,
                formula_scope='Integer finite supplier gates: local primitive, logical, router, literal, mass, precision, tape, row and halving. Endpoint moment and outer arithmetic remain separate.',
                invoice_transfer='Local programs, dispatch, parent envelope and physical stock are fixed; actual residual child count stays within the same charged reserve.')


def fill_transfer(candidate_fill, baseline_audit, candidate_audit, local_audits):
    """Check the exact invalidation boundary for a fixed-word allocation edit.

    Native programs and endpoint proofs are reused by their exact source pins.
    Literal owners are checked afresh. A new global/outer release still must
    independently check its endpoint-dependent strict arithmetic.
    """
    b, model = _base(), _base()['model']
    evidence = _prior_release_binding()
    invoice = b['data']['evidence/PHYSICAL-INVOICE.json']
    claim = b['data']['CLAIM.json']
    providers, word_hashes = _provider_binding()
    old_roles, old_families, old_foreign = _family_assignment(_data('fill')['rows'])
    new_roles, new_families, new_foreign = _family_assignment(candidate_fill['rows'])
    need(old_roles.keys() == new_roles.keys(), 'same complete physical role domain')
    need(old_foreign == invoice['blocknorm']['foreign_helper_roles_checked'], 'baseline foreign-helper role count')
    charts = _chart_audit(candidate_fill['rows'])
    changed_assignments, shifted_offsets = [], []
    for key in sorted(old_roles):
        before, after = old_roles[key], new_roles[key]
        if before[2:5] != after[2:5]:
            changed_assignments.append(dict(call=key[0], helper_index=key[1], before=list(before), after=list(after)))
        elif before[5] != after[5]:
            shifted_offsets.append(dict(call=key[0], helper_index=key[1], before=before[5], after=after[5]))
    need(baseline_audit['rank_mass'] == candidate_audit['rank_mass'] == 4816512,
         'unchanged full streamed rank mass')
    need(baseline_audit['aggregate_local_profile'] == candidate_audit['aggregate_local_profile'],
         'unchanged complete local invoice')
    need(sum(candidate_audit['idle'].values()) <= sum(baseline_audit['idle'].values()),
         'no increase in number of residual idle children for conservative invoice transfer')
    need(max(candidate_audit['idle']) <= 48, 'retained maximum idle child rank')
    expected_stock = dict(data_and_owner_families=66304, local_helpers=408,
                          private_centres=8, private_zero_buffers=82, coefficient_work=2)
    need(invoice['physical_stock_identity'] == expected_stock and sum(expected_stock.values()) == 66804,
         'complete physical stock including all82 private buffers')
    need((claim['zero_buffers'], claim['physical_families'], claim['independent_inputs']) == (82, 66804, 632),
         'source physical claim binding')
    need(len(invoice['selected_calls']) == model.calls == 666, 'source complete selected-call invoice')
    orientations = {event['stage']: ('backward' if event['reverse'] else 'forward')
                    for event in _data('template')['recipe'] if event['kind'] == 'local'}
    real_primitives = coefficient_work = scalar_macros = 0
    for t, (stage, replica) in enumerate(model.order):
        entry = invoice['selected_calls'][t]
        pid, orientation = b['dispatch'][stage, replica], orientations[stage]
        local = invoice['providers'][pid]
        need((entry['stage'], entry['replica'], entry['provider_id'], entry['orientation']) ==
             (stage, replica, pid, orientation), 'unchanged literal call/dispatch/orientation invoice')
        need(entry['program_sha256'] == local['program_hashes'][orientation], 'selected native program hash')
        for field in ('events', 'macros', 'real_component_primitives', 'coefficient_work_primitive_count'):
            need(entry[field] == local['local'][orientation][field], 'selected local primitive invoice')
        real_primitives += entry['real_component_primitives']
        coefficient_work += entry['coefficient_work_primitive_count']
        scalar_macros += entry['macros']
    need((real_primitives, coefficient_work, scalar_macros) ==
         (invoice['selected_real_component_primitives'], invoice['selected_coefficient_work_primitive_count'],
          invoice['selected_scalar_macros']), 'unchanged aggregate primitive and coefficient work counts')
    max_prefix = 0
    for pid, provider in providers.items():
        local = invoice['providers'][pid]
        need((local['helpers'], local['centres'], local['zero_buffers'], local['n']) == (408, 8, 82, 632),
             'actual local native ABI including work stock')
        need(local['widths'] == provider['widths'] and profile(local['paid_profile']) == provider['actual_paid_profile'],
             'native invoice binds actual ordered helper inventory and paid bill')
        need(local_audits[pid]['status'] == 'PASS' and local_audits[pid]['ordered_helpers'] == b['words'][pid].helpers,
             'fresh all-column finite algebra check')
        need(len(b['data'][_WORDS[pid]]['helper_final']) == 82, 'literal82-buffer cleanup namespace')
        for orientation in ('forward', 'backward'):
            receipt = local['local'][orientation]
            need(receipt['all_exact_columns'] == 632 and receipt['dirty_helper_columns'] == 408 and
                 receipt['all_dirty_helper_columns_restored'] and receipt['private_centres_and_coefficient_work_cleared'],
                 'unchanged universal endpoint contracts')
            need((receipt['private_zero_buffer_peak'], receipt['private_zero_buffer_clears']) == (82, 164),
                 'unchanged private buffer peak and two clears')
            prefix = Q(receipt['prefix_l1'])
            need(0 < prefix <= 2 ** receipt['prefix_bits'], 'native scalar prefix numerical enclosure')
            max_prefix = max(max_prefix, receipt['prefix_bits'])
    # Exact group order |Sp(2n,2)| = 2^(n^2) product_{j=1}^n (2^(2j)-1).
    group_order = 2 ** (36 * 36)
    for j in range(1, 37):
        group_order *= 2 ** (2 * j) - 1
    stock_bits = (group_order * 66804).bit_length()
    stock_l2_bits = (stock_bits + 1) // 2
    active_calls = sum(e['kind'] == 'local' for e in _data('template')['recipe'])
    bridges = sum(e['kind'] == 'bridge' for e in _data('template')['recipe'])
    need((active_calls, bridges) == (9, 9), 'unchanged per-replica active depth')
    actual_prefix = max_prefix + 37 + active_calls + bridges + stock_l2_bits + 1 + 4
    reserve_prefix = 128 + 37 + active_calls + bridges + stock_l2_bits + 1 + 4
    bn = invoice['blocknorm']
    need((stock_bits, stock_l2_bits, max_prefix, actual_prefix, reserve_prefix) == (2644, 1322, 74, 1456, 1510),
         'independent full physical-stock and prefix recomputation')
    need(bn['physical_stock_bits'] == stock_bits and bn['stock_l2_bits'] == stock_l2_bits and
         bn['actual_prefix_bits'] == invoice['global_prefix_bits'] == actual_prefix and
         bn['required_reserve_bits'] == reserve_prefix and reserve_prefix < invoice['charged_prefix_bits'] == 2048,
         'retained prefix reserve remains sufficient')
    need(max_prefix <=128 and invoice['row_prefix_extra'] == 2 * invoice['charged_prefix_bits'],
         'unchanged local reserve and charged row prefix')
    finite = _strict_finite_invoice(candidate_audit, group_order, stock_bits)
    return dict(status='PASS_SOURCE_BOUND_FILL_TRANSFER', prior_evidence=evidence,
                changed_role_assignments=changed_assignments, compacted_other_role_offsets=shifted_offsets,
                same_call_physical_family_sets=(old_families == new_families),
                family_sets_changed_at_calls=[i for i in range(model.calls) if old_families[i] != new_families[i]],
                family_set_sha256=semantic_sha([sorted(x) for x in new_families]),
                roles=len(new_roles), calls=model.calls, foreign_helper_roles=new_foreign,
                baseline_foreign_helper_roles=old_foreign, residual_charts=charts,
                active_data_families_excluded=True, all_role_intervals_and_offsets_checked_fresh=True,
                unchanged_native_words=word_hashes, physical_stock=expected_stock,
                unchanged_primitive_invoice=dict(real_components=real_primitives, coefficient_work=coefficient_work,
                    scalar_macros=scalar_macros, compiler=invoice['compiler'], local_adapters=invoice['local_adapters'],
                    local_primitive_bound=invoice['local_primitive_bound']),
                prefix_bound=dict(group_order=str(group_order), physical_stock_bits=stock_bits,
                    stock_l2_bits=stock_l2_bits, local_actual_bits=max_prefix, active_depth=active_calls+bridges,
                    partial_cover_bits=1, actual_prefix_bits=actual_prefix, reserve_bits=reserve_prefix,
                    charged_prefix_bits=2048),
                strict_finite_supplier=finite,
                residual_children=dict(before=sum(baseline_audit['idle'].values()), after=sum(candidate_audit['idle'].values()),
                    maximum_rank=max(candidate_audit['idle']), complete_rank_mass=4816512),
                blocknorm_argument=[
                    'For each invocation the helper-to-physical-family map remains injective and excludes the active data pair; freshly checked literal windows make every role legal.',
                    'Every fresh helper-to-family embedding and residual/spectator chart is isometric and the native word is unchanged. Equality to the previous family set is not required by the inherited block-energy lemma.',
                    'The unchanged all-column native contract has zero helper-to-data response and identity formal helper rows. Together with its audited frame/phase transports, each completed foreign helper channel is a within-family unitary. Thus foreign owner-block energy is preserved; only the active owner block receives the source-proved data shear.',
                    'The unchanged controller gives nine active invocations and nine bridges per block. Width and offset changes are tensor-coordinate embeddings and do not change the whole-family unitary operator-norm bound.',
                    'At an internal invocation prefix, use the unchanged maximum local prefix for arbitrary input columns, the full physical-stock sup-to-l2 factor, and the retained one-bit partial-cover margin.'],
                fresh_native_replay=False,
                pending=['fresh exact endpoint moment bound', 'fresh modern outer arithmetic',
                         'new immutable candidate/source/release receipt binding'],
                scope='Conditional transfer from the explicitly pinned complete PR2917 native and physical admission. Changed owner geometry and invariant prefix arithmetic are checked here; no fresh prior native replay is claimed.')


@lru_cache(maxsize=8192)
def _cost(rank, endpoint):
    """Outward round exact retained atanh/Taylor bounds to a 10^-40 grid."""
    lower, upper = _module('moment').moment_bounds({rank: 1}, Q(endpoint))
    grid = 10 ** 40
    low = Q((lower.numerator * grid) // lower.denominator, grid)
    high = Q(-((-upper.numerator * grid) // upper.denominator), grid)
    need(low <= lower <= upper <= high, 'outward rational coefficient enclosure')
    return low, high


def moment_bounds(value, endpoint):
    value = profile(value)
    k = Q(endpoint)
    need(0 <= k < Q(1, 500), 'registered small positive exponent range')
    lower = sum(count * _cost(rank, str(k))[0] for rank, count in value.items())
    upper = sum(count * _cost(rank, str(k))[1] for rank, count in value.items())
    return lower, upper


def root_separation(candidate_profile, baseline_profile, separator=None):
    """Prove old root < q < new root with a common exact rational q.

    One fixed midpoint proposal is used when q is omitted. Decimal roots are
    proposals only; the final decision uses outward rational moments exclusively.
    """
    candidate_profile, baseline_profile = profile(candidate_profile), profile(baseline_profile)
    need(_mass(candidate_profile) == _mass(baseline_profile) == 4816512, 'same complete coverage mass')
    numerical = None
    if separator is None:
        G = _module('growth')
        G._root_cached.cache_clear()
        old, new = G.root(baseline_profile), G.root(candidate_profile)
        with localcontext() as context:
            context.prec = 90
            separator = str((old + new) / 2)
        numerical = dict(baseline=str(old), candidate=str(new), protocol='90 digits, 280 bisections; proposal only')
    q = Q(separator)
    old_lower, old_upper = moment_bounds(baseline_profile, q)
    new_lower, new_upper = moment_bounds(candidate_profile, q)
    passed = old_lower > 66304 > new_upper
    return dict(status='PASS' if passed else 'NOT_CERTIFIED', separator=str(q),
                baseline_moment_lower=str(old_lower), baseline_moment_upper=str(old_upper),
                candidate_moment_lower=str(new_lower), candidate_moment_upper=str(new_upper),
                baseline_rejection_margin=str(old_lower - 66304),
                candidate_acceptance_margin=str(66304 - new_upper), numerical_proposals=numerical,
                proof='For positive ranks below73, M(k)=sum c_r*(r/73)^(1-k) strictly increases. Baseline lower moment>66304>candidate upper moment implies old root<q<new root.',
                scope='Complete-profile complex recurrence root; supplier/native/outer admission is separate.')


def endpoint_admission(value):
    """Fixed24-place grid bracket; Decimal proposes and rationals decide."""
    value = profile(value)
    estimate = _module('growth').root(value)
    scale = 10 ** 24
    proposed = Q(str(estimate))
    C = Q((proposed * scale).__floor__(), scale)
    lo, hi = moment_bounds(value, C)
    upper_lo, upper_hi = moment_bounds(value, C + Q(1, scale))
    need(hi < 66304 < upper_lo, 'exact24-place candidate root bracket')
    return dict(status='PASS_EXACT_RATIONAL_ROOT_BRACKET', complex_lower=str(C),
                complex_upper=str(C + Q(1, scale)), numerical_proposal=str(estimate),
                lower_endpoint_moment=[str(lo), str(hi)], upper_endpoint_moment=[str(upper_lo), str(upper_hi)],
                acceptance_margin=str(66304-hi), rejection_margin=str(upper_lo-66304),
                overstated_endpoint_control_rejected=True,
                method='Pinned positive-tail atanh/Taylor enclosures; coefficients outward rounded to10^-40. Decimal90-digit root is proposal only.',
                scope='Complete-profile complex moment and fixed24-place grid only; source-bound supplier/outer checks are separate.')


def native_and_outer_obligations(local_words_unchanged=True, separator=None):
    b = _base()
    if str(_SOURCE_PIN['pr']) == '2917':
        reuse = {pid: dict(word_sha256=_FILE_PINS[relative]['sha256']) for pid, relative in _WORDS.items()}
    else:
        declared = b['data']['new/SPEC.json']['providers']
        reuse = {pid: dict(word_sha256=_FILE_PINS[relative]['sha256'],
                orientation_program_sha256=deepcopy(declared[pid]['program_hashes']),
                semantic_artifact_sha256=deepcopy(declared[pid]['artifact_semantic_sha256']),
                complete_contract_sha256=semantic_sha(declared[pid]['complete_contract']))
             for pid, relative in _WORDS.items()}
    buffer_peak = max(len(b['data'][relative].get('helper_final', {})) for relative in _WORDS.values())
    proposal = None
    if separator is not None:
        # This equality is an arithmetic proposal from the held #2802 precision24
        # workflow. Passing it is deliberately not called outer verification.
        q = Q(separator)
        k = q - Q(1, 10 ** 70) - Q(1, 10 ** 46)
        old = Q(b['data']['CLAIM.json' if str(_SOURCE_PIN['pr']) == '2917' else 'outer/OUTER-CLAIM.json']['kappa'])
        proposal = dict(complex_lower_proposal=str(q), outer_kappa_proposal=str(k),
                        exceeds_pinned_outer_headline=k > old,
                        formula='C-10^-70-10^-46 (held precision24 workflow)',
                        arithmetic_only=True, full_outer_verification=False)
    return dict(native_supplier=dict(status='UNRUN', unchanged_words=local_words_unchanged,
                    source_bound_reuse_possible=local_words_unchanged,
                    declarations_only=reuse,
                    required=['complete native artifact tree bound to these exact word bytes',
                              'native, ledgers, local-replay, wrappers, phases all pass',
                              'actual paid profiles and ordered widths in both orientations',
                              'independent all-column replay, warp recipes, Clifford phases, residual adapters',
                              'retained-parent receipt with source/claim/native pins']),
                strict_global_supplier=dict(status='UNRUN', required=[
                    'reconstruct changed owners and parent lift',
                    f'rebind source/target interfaces, native invoices and physical stock including {buffer_peak} private buffers',
                    'full strict supplier/precision/endpoint discovery with current fill/profile',
                    'new candidate manifest and source-bound release receipt']),
                outer=dict(status='UNRUN', proposal=proposal, required=[
                    'independently evaluate modern fine-prime-padding ledger at new admitted complex endpoint',
                    'all strict gaps, bit-supplier constraints, layout and precision guards',
                    f'headline rational kappa exceeds pinned #{_SOURCE_PIN["pr"]} outer claim',
                    'two independent arithmetic checkers and full release binding']),
                inherited_theorem=dict(status='CONDITIONAL_INHERITED', obligations=[
                    'all-size compiler and machine realization', 'common labels and mutable-source access',
                    'physical hosting and routing', 'precision and fixed-tape contracts',
                    'exact recovery and analytic transfer', 'PR559 recurrence correction',
                    'PR589 bit H1-H5 and cited fine-prime/gauge-free theorems']))


def audit_fill_candidate(spec):
    """Pool worker entry: exact two-seed confirmation of a concrete fill artifact.

    spec = {seed, candidate_path, candidate_sha256, separator?}. The file may
    contain only a changed literal fill; no generated module is imported.
    """
    started = time.process_time()
    b = _base()
    path = Path(spec['candidate_path'])
    if not path.is_absolute():
        path = RR / path
    path = path.resolve()
    need(path.is_relative_to(RR.resolve()), 'candidate artifact must stay inside styles-r11')
    need(sha(path) == spec['candidate_sha256'], 'candidate artifact digest')
    candidate = read_data(path)
    baseline = _data('fill')
    baseline_check = literal_admission(baseline)
    complete = _data('profile')
    extra_complete = b['data']['CLAIM.json']['profile'] if str(_SOURCE_PIN['pr']) == '2917' else b['data']['new/PROFILE.json']
    idle = b['data']['evidence/EXACT-OWNER-MOMENT.json']['idle'] if str(_SOURCE_PIN['pr']) == '2917' else b['data']['CONSTRUCTION.json']['idle']
    need(baseline_check['profile'] == profile(complete) == profile(extra_complete),
         'reconstructed baseline and both pinned complete profiles')
    need(baseline_check['idle'] == profile(idle),
         'reconstructed baseline and pinned idle profile')
    candidate_check = literal_admission(candidate)
    order = list(_WORDS)
    random.Random(int(spec['seed'])).shuffle(order)
    local = {pid: local_admission(b['data'][_WORDS[pid]], _FILE_PINS[_WORDS[pid]]) for pid in order}
    separation = root_separation(candidate_check['profile'], baseline_check['profile'], spec.get('separator'))
    endpoint = endpoint_admission(candidate_check['profile'])
    transfer = (fill_transfer(candidate, baseline_check, candidate_check, local)
                if str(_SOURCE_PIN['pr']) == '2917' else None)
    obligations = native_and_outer_obligations(True, endpoint['complex_lower'])
    if transfer is not None:
        obligations['native_supplier'] = dict(status='REUSED_SOURCE_BOUND_PRIOR_NATIVE_ADMISSION',
            fresh_native_replay=False, source_evidence=transfer['prior_evidence'], unchanged_words=True)
        obligations['strict_global_supplier'] = dict(status='PASS_CHANGED_FILL_FINITE_TRANSFER',
            source_bound_transfer=transfer['status'], residual_charts=transfer['residual_charts']['status'],
            strict_finite=transfer['strict_finite_supplier']['status'], exact_endpoint=endpoint['status'],
            scope='Fresh affected finite checks plus explicitly reused unchanged predecessor native/controller evidence.')
    delta = {rank: candidate_check['profile'].get(rank, 0) - baseline_check['profile'].get(rank, 0)
             for rank in sorted(set(candidate_check['profile']) | set(baseline_check['profile']))
             if candidate_check['profile'].get(rank, 0) != baseline_check['profile'].get(rank, 0)}
    need(_mass(delta) == 0, 'exact complete-profile delta is mass-neutral')
    return dict(status='PASS' if separation['status'] == 'PASS' else 'EXPLORATORY', seed=int(spec['seed']),
                admission_level='FINITE_COMPLEX_ROOT_IMPROVEMENT' if separation['status'] == 'PASS' else 'NO_CERTIFIED_IMPROVEMENT',
                candidate_artifact=dict(path=str(path.relative_to(RR)), sha256=sha(path)),
                baseline_profile=baseline_check['profile'], candidate_profile=candidate_check['profile'],
                complete_profile_delta=delta, local_audits=local, literal_admission=candidate_check,
                root_separation=separation, endpoint_admission=endpoint, source_bound_transfer=transfer,
                obligations=obligations,
                solver_calls=0, n_permutations=0, cpu_seconds=time.process_time()-started,
                scope='Independent finite local algebra, literal hosting, exact complex root separation and registered unchanged-source transfer where available. A complete released headline additionally needs the independent outer checks and new release binding. No unexecuted native replay is promoted to fresh PASS.',
                **provenance())


def admission_controls(seed):
    """Preregistered exact controls; coordinator alone decides when to run."""
    b = _base()
    original = _data('fill')
    positive = literal_admission(original)
    labels = ['duplicate_helper', 'out_of_capacity', 'out_of_call_range']
    random.Random(seed).shuffle(labels)
    results = []
    for label in labels:
        rows = list(original['rows'])
        if label == 'duplicate_helper':
            rows[1] = list(rows[0])
        else:
            rows[0] = list(rows[0])
            if label == 'out_of_capacity':
                rows[0][5] = b['model'].win[rows[0][2], rows[0][3]][0]
            else:
                rows[0][0] = b['model'].calls
        bad = dict(original, rows=rows)
        try:
            literal_admission(bad)
        except (ValueError, RuntimeError, AssertionError, KeyError, IndexError) as exc:
            results.append(dict(control=label, rejected=True, reason=str(exc)[:300]))
        else:
            results.append(dict(control=label, rejected=False))
    same = root_separation(positive['profile'], positive['profile'])
    good = all(x['rejected'] for x in results) and same['status'] == 'NOT_CERTIFIED'
    return dict(status='PASS' if good else 'ERROR', seed=seed, baseline=positive,
                negative_controls=results, equal_profile_not_improved=same,
                n_permutations=0, scope='Exact admission controls, not an inferential test family.', **provenance())
