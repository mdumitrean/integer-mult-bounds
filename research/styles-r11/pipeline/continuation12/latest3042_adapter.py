"""Pinned PR3042 words and source-reported PR3054 comparison, parent loader.

No fetched program is imported or executed.  prepare() is called only after the
coordinator freezes the source and registration; baseline_task runs in pool.py.
Existing PR3015/2979 data are retained as credited fixtures, not current words.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time


PKG = Path(__file__).resolve().parents[2]
TRUSTED_ADAPTER = 'pipeline/continuation08/source3015.py'
TRUSTED_ADAPTER_SHA = 'bbc8c770d8540278988e32946069ee225be6ee1d39b13780ac392587e11261af'
ACQUISITION = 'data/continuation-11/latest-sources/ACQUISITION.json'
ACQUISITION_SHA = '08f77062e367fecde37005ebb199e4f555d15c8034524261d5b12ef963d0ad5c'
COMPARISON = 'data/continuation-11/latest-sources/WORD-COMPARISON.json'
COMPARISON_SHA = 'ca7d9138781b7f0ff64adc4c88029f9b2d55c62bb38d2868e94aaa947d1a18e9'
BINDINGS = 'data/continuation-12/allocation-source/BINDINGS.json'
BINDINGS_SHA = 'b9d7ce0eda0ccf2bfb3271a0e2f9db0c20d4207f553b3bb7aa08788663240ff1'
WORD_HEAD = '84cc406ad91ec53fff329a11a445d7effe564a77'
COMPARATOR_HEAD = '4773c3ea67b471415870e38411fae313ec44a675'
ENDPOINT = '864868975032139275621/500000000000000000000000'
PROFILE = {1: 2433, 2: 712, 3: 232, 4: 108, 5: 18, 8: 8}
INVENTORY = {4: 26, 5: 2, 6: 16, 7: 52, 8: 99, 9: 213}
WORD_SHA = {
    'base': '7e98f6f2a6c9ce9e7e04b515bd8ce4a4a533ff05f01ea265be2a1a994695260e',
    'extra': '1396410de482883416fc7f534062ab005b484056b035fdcfa3b5cc065536ba35',
}
_INNER = _SOURCE = _STATE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def semantic(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def checked(ref):
    path = (PKG / ref['path']).resolve()
    need(path.is_relative_to(PKG) and path.suffix != '.py', 'confined inert source input')
    raw = path.read_bytes()
    need(sha(raw) == ref['sha256'], 'exact inert source SHA: ' + ref['path'])
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'exact source byte count')
    if 'git_blob' in ref:
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == ref['git_blob'],
             'exact source Git blob')
    return raw


def _fixed_json(path, expected):
    return json.loads(checked(dict(path=path, sha256=expected)))


def prepare():
    global _INNER, _SOURCE, _STATE
    if _STATE is not None:
        return _STATE
    need(sys.flags.isolated and not sys.flags.optimize, 'Python -I with assertions enabled')
    path = PKG / TRUSTED_ADAPTER
    need(sha(path.read_bytes()) == TRUSTED_ADAPTER_SHA, 'trusted local fixture adapter source')
    spec = importlib.util.spec_from_file_location('styles12_trusted_source3015', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    old = module.prepare()
    _INNER, _SOURCE = module, module._SOURCE
    acq = _fixed_json(ACQUISITION, ACQUISITION_SHA)
    comparison = _fixed_json(COMPARISON, COMPARISON_SHA)
    bindings = _fixed_json(BINDINGS, BINDINGS_SHA)
    need(acq['source_reported_only'] and acq['scientific_replay'] is False and len(acq['files']) == 20,
         'complete compact inert acquisition scope')
    need(acq['sources']['3042']['head'] == WORD_HEAD and acq['sources']['3042']['author_login'] == 'dcharb78'
         and acq['sources']['3054']['head'] == COMPARATOR_HEAD, 'exact word and comparison release heads')
    files = {r['path']: r for r in acq['files']}
    need(len(files) == 20, 'no duplicate acquired source paths')
    payloads = {name: checked(ref) for name, ref in files.items()}
    need(sum(map(len, payloads.values())) == acq['payload_bytes'], 'all acquisition bytes accounted')
    prefix = 'data/continuation-11/latest-sources/'
    claim = json.loads(payloads[prefix + '3042/CLAIM.json'])
    manifest = json.loads(payloads[prefix + '3042/MANIFEST.json'])
    edit_pins = json.loads(payloads[prefix + '3042/EDIT-PINS.json'])
    native = json.loads(payloads[prefix + '3054/evidence/NATIVE-RECEIPT.json'])
    finite = json.loads(payloads[prefix + '3054/evidence/FINITE.json'])
    admission = json.loads(payloads[prefix + '3054/evidence/ADMISSION-RESULT.json'])
    outer = json.loads(payloads[prefix + '3054/evidence/OUTER-CLAIM.json'])
    need({int(k): v for k, v in claim['local_profile'].items()} == PROFILE and claim['helpers'] == 408
         and claim['independent_inputs'] == 632 and claim['physical_families'] == 66813
         and claim['replicas'] == 74, 'source word local and T74 physical declaration')
    need(finite['profile'] == admission['profile'] == bindings['source_reported_inventory']['profile']
         and Fraction(admission['complex_lower']) == Fraction(bindings['complex_lower']) == Fraction(ENDPOINT)
         and Fraction(outer['kappa_rational']) + Fraction(1, 10**46) + Fraction(1, 10**70) == Fraction(ENDPOINT),
         'exact source-reported comparator profile and endpoint bindings')
    need(finite['replicas'] == 740 and finite['live'] == 663040 and finite['physical'] == 663549
         and finite['calls'] == 6660 and finite['roles'] == 2717280 and finite['stock']['buffers'] == 91,
         'T740 comparison dimensions remain separate from T74 word declaration')
    records = {}
    for provider in ('base', 'extra'):
        logical = 'edits/FINAL-WORD-' + provider + '.json.gz'
        pin = deepcopy(files[prefix + '3042/' + logical])
        need(pin['sha256'] == WORD_SHA[provider] == edit_pins[logical] == manifest[logical]
             == native['providers'][provider]['word_sha256'], 'word identity across source, edit, manifest and native receipts')
        raw = json.loads(gzip.decompress(payloads[pin['path']]))
        before = old['records'][provider]
        comp = comparison['providers'][provider]
        need(comp['after']['sha256'] == pin['sha256'] and comp['before']['sha256'] == before['source_pin']['sha256'],
             'recorded before/after byte identity')
        changed = sorted(k for k in set(raw) | set(before['raw']) if raw.get(k) != before['raw'].get(k))
        need(changed == comp['changed_top_level_fields'] == ['cleanup', 'report', 'restore'],
             'source comparison changes only declared restore/report/cleanup fields')
        need(all(raw[k] == before['raw'][k] for k in ('A', 'B', 'warps'))
             and comp['A_identical'] and comp['B_identical'] and comp['warps_identical'],
             'unchanged A/B/warp source context')
        need({k: len(raw[k]) for k in ('A', 'B', 'restore', 'cleanup')} == comp['scalar_lengths_after'],
             'source scalar lengths exactly match existing comparison')
        pin.update(pr=3042, commit=WORD_HEAD, author='dcharb78', author_login='dcharb78',
                   format='BORROW-WORD', source='PR3042 six restore-carrier skips on credited PR3015/2979 lineage')
        records[provider] = dict(provider=provider, raw=raw, attribution=deepcopy(pin), source_pin=deepcopy(pin),
            expected_profile=dict(PROFILE), expected_inventory=dict(INVENTORY), expected_buffers=91,
            expected_physical_families=66813, expected_independent_inputs=632, expected_helpers=408,
            original_semantic_sha256=semantic(raw), source_status='UNCHANGED_PINNED_PR3042')
    inherited = deepcopy(old['provenance'])
    comparator_pin = deepcopy(files[prefix + '3054/evidence/OUTER-CLAIM.json'])
    comparator_pin.update(pr=3054, commit=COMPARATOR_HEAD, author='Nick Petalas (petalas)',
                          source='Source-reported T740 plus six-skip composition; no fresh admission in this adapter')
    credits = deepcopy(bindings['full_credit_references'])
    credit_contents = {r['path']: checked(r).decode() for r in credits}
    provenance = dict(source_attribution=inherited['source_attribution'] +
        [records[p]['attribution'] for p in ('base', 'extra')] + [comparator_pin],
        inherited_source_provenance=inherited,
        release_acquisition=dict(path=ACQUISITION, sha256=ACQUISITION_SHA),
        source_comparison=dict(path=COMPARISON, sha256=COMPARISON_SHA),
        latest_bindings=dict(path=BINDINGS, sha256=BINDINGS_SHA),
        release_claim=files[prefix + '3042/CLAIM.json'], release_manifest=files[prefix + '3042/MANIFEST.json'],
        source_credit_files=credits, source_credit_contents=credit_contents,
        comparison=dict(pr=3054, head=COMPARATOR_HEAD, author='Nick Petalas (petalas)', endpoint=ENDPOINT,
                        replicas=740, physical_families=663549, source_reported_only=True,
                        fresh_native_physical_outer=False),
        scope='Only exact data/receipt identity and registered finite local baseline checks. No new native, owner, physical, outer or kappa admission.')
    _STATE = dict(records=records, previous_records=old['records'], fixtures=old['fixtures'],
                  declaration=json.loads(payloads[prefix + '3042/edits/EDITS.json']), provenance=provenance,
                  source_claim=claim, endpoint=ENDPOINT, comparison_bindings=bindings)
    return _STATE


def baseline_task(spec):
    need(_STATE is not None, 'prepare once in parent')
    started = time.process_time()
    provider, seed = spec['provider'], int(spec['seed'])
    rec = _STATE['records'][provider]
    W, A = _SOURCE._modules()
    word = W.WordData(rec['raw'], rec['attribution'])
    need(word.paid == PROFILE and (word.v, word.h, word.R, len(word.live), len(word.helpers)) ==
         (112, 9, 480, 632, 408), 'canonical PR3042 profile and dimensions')
    widths = [len(word.end[h]) - len(word.start[h]) for h in word.helpers]
    need(dict(Counter(widths)) == INVENTORY, 'exact ordered-helper width inventory')
    audit = A.local_admission(rec['raw'], rec['attribution'])
    need(audit['status'] == 'PASS' and audit['paid_profile'] == PROFILE and audit['widths'] == widths,
         'independent finite ledger agrees with canonical baseline')
    finite = audit['audit']
    need(finite['checked_columns'] == finite['independent_inputs'] == 632 and
         finite['orientations'] == {'forward': 'PASS', 'dual': 'PASS'} and
         finite['restored_cold'] == finite['zero_buffers'] == 91,
         'all independent forward/dual columns and restored private buffers')
    need(semantic(rec['raw']) == rec['original_semantic_sha256'], 'source raw data not mutated')
    return dict(status='PASS', provider=provider, seed=seed, source_pin=rec['source_pin'],
                source_semantic_sha256=rec['original_semantic_sha256'], local_admission=audit,
                word_source_declared_physical_families=66813,
                comparison_source_declared_physical_families=663549, comparison_replicas=740,
                comparison_endpoint=ENDPOINT, fresh_native_physical_outer=False,
                cpu_seconds=time.process_time() - started)


def get_state():
    need(_STATE is not None, 'prepare once in parent')
    return _STATE


def provenance():
    need(_STATE is not None, 'prepare once in parent')
    return deepcopy(_STATE['provenance'])
