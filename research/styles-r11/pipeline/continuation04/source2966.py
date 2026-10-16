"""Pinned inert PR2966 words, complete credits and source receipts.

Source-only adapter until the coordinator freezes the experiment registration.
``prepare()`` loads two raw words once in the parent and returns records keyed
by ``base`` and ``extra``. Treat those raw dictionaries as immutable;
constructors must copy before editing. ``baseline_task({provider, seed})`` runs
only through the common pool after preparation and registration.

Only the existing hash-pinned r11 word loader/admission code and its pinned
PR2679 free-operator auditor are imported. Every PR2966 file, including producer
and reviewer text, remains inert. The baseline task proves finite local algebra
and frame accounting; native, physical, packing and outer admission are separate.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
PIPELINE = HERE.parent
RR = PIPELINE.parent
ROOT = RR.parents[1]
DIRECTORY = RR / 'data/continuation-04/pr2966'
HEAD = 'e62d3eb9005117d82a9babcfa937ecc53237c490'
ACQUISITION_SHA = 'd8bea290a72abc122f0103748f662afab84bea2d429096cd25224562fd38e5f1'
MANIFEST_SHA = '9e410c244efb370e20a5f9dc366550e11bcb14ebcecf8f2cb850512e82573914'
PINS_SHA = '4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65'
CLAIM_SHA = '4d4c4800bf3bcb36d09021313b2712aebd4aa0830c74dda30991daf6851c220a'
WORD_FILES = {'base':'rewrite/FINAL-WORD-base.json.gz',
              'extra':'rewrite/FINAL-WORD-extra.json.gz'}
WORD_SHA = {'base':'4e96cf33d2e0f85f6ff5ccc6165a6c8c0305ca0081ecaf40d72c5e1c4a13e9a5',
            'extra':'440398ee0d2bfd9448be77fa0652512cb79c6ecda9ae030afc79259056f5c6dc'}
PROFILE = {1:2430, 2:628, 3:282, 4:110, 5:26, 8:8}
INVENTORY = {4:26, 5:2, 7:62, 8:100, 9:218}
BUFFERS = 86
DECLARED_PHYSICAL_FAMILIES = 66808
TRUSTED = {
    'admission':('research/styles-r11/pipeline/continuation/admission.py',
                 '4feb94bb7b53d37a97233ef7a2556f9931d78f8ac6776f6d16fd458373002ec5'),
    'wordio':('research/styles-r11/pipeline/wordio.py',
              'a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4'),
    'auditor':('research/t74-joint-twelve-retired7/vendor/audit_local_pr2679.py',
               'a38940094f7d19cd6376aafdd4734fa68eabc9aff4c98c3c4a3e9540328b1c90'),
}
_META = None
_RECORDS = None
_MODULES = None


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def semantic_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          allow_nan=False).encode())


def _checked_bytes(path, expected, size=None, git_blob=None):
    path = Path(path).resolve()
    need(path.is_relative_to(ROOT), 'source path outside repository')
    raw = path.read_bytes()
    need(sha(raw) == expected, 'source SHA256 mismatch: ' + str(path.relative_to(ROOT)))
    if size is not None:
        need(len(raw) == size, 'source byte count mismatch')
    if git_blob is not None:
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == git_blob,
             'source Git blob mismatch')
    return raw


def _json(raw, compressed=False):
    return json.loads(gzip.decompress(raw) if compressed else raw)


def source_manifest():
    for relative, digest in TRUSTED.values():
        _checked_bytes(ROOT / relative, digest)
    return {relative:digest for relative, digest in TRUSTED.values()}


def _modules():
    global _MODULES
    need(not sys.flags.optimize, 'baseline admission requires enabled assertions')
    source_manifest()
    if _MODULES is None:
        sys.dont_write_bytecode = True
        path = ROOT / TRUSTED['admission'][0]
        spec = importlib.util.spec_from_file_location('styles_cont04_source2966_admission', path)
        admission = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = admission
        spec.loader.exec_module(admission)
        need(admission.TRUSTED['wordio'] == TRUSTED['wordio'] and
             admission.TRUSTED['auditor'] == TRUSTED['auditor'], 'transitive local-audit source pins')
        wordio = admission._module('wordio')
        # Load the trusted auditor once in the parent; no audit is run here.
        admission._module('auditor')
        _MODULES = (wordio, admission)
    return _MODULES


def _metadata():
    global _META
    if _META is not None:
        return _META
    acquisition = _json(_checked_bytes(DIRECTORY / 'ACQUISITION.json', ACQUISITION_SHA))
    need((acquisition['pr'], acquisition['head'], acquisition['author_login']) ==
         (2966, HEAD, 'jeremykothe2'), 'source head and author')
    files = {p['path']:deepcopy(p) for p in acquisition['files']}
    need(len(files) == len(acquisition['files']) == 110 and
         acquisition['manifest_entries_checked'] == 109, 'complete bounded package acquisition')
    pins = _json(_checked_bytes(RR / 'data/words/PINS.json', PINS_SHA))['files']
    need(len(pins) == 21, 'complete original attribution set')
    manifest = _json(_checked_bytes(DIRECTORY / 'package/MANIFEST.json', MANIFEST_SHA))
    claim = _json(_checked_bytes(DIRECTORY / 'package/CLAIM.json', CLAIM_SHA))
    need({int(k):v for k,v in claim['local_profile'].items()} == PROFILE and
         {int(k):v for k,v in claim['width_inventory'].items()} == INVENTORY and
         claim['zero_buffers'] == BUFFERS and claim['physical_families'] == DECLARED_PHYSICAL_FAMILIES,
         'declared source contract binding; not independent physical admission')
    credit_files, credit_text = [], {}
    for name in ('CREDITS.md', 'NOTICE', 'SOURCES.json'):
        pin = files[name]
        raw = _checked_bytes(RR / pin['local_path'], pin['sha256'], pin['bytes'], pin['git_blob'])
        credit_files.append(dict(path=pin['local_path'], sha256=pin['sha256'],
                                 git_blob=pin['git_blob'], bytes=pin['bytes'], source_path=pin['source_path']))
        credit_text[name] = raw.decode() if name != 'SOURCES.json' else _json(raw)
    word_pins = {}
    for provider, relative in WORD_FILES.items():
        pin = deepcopy(files[relative])
        need(pin['sha256'] == WORD_SHA[provider], 'registered provider byte pin')
        pin.update(path=pin['source_path'], relative_path=relative, pin_key=pin['source_path'],
                   pr=2966, commit=HEAD, author='Jeremy Kothe (jeremykothe2)',
                   author_login='jeremykothe2', format='BORROW-WORD',
                   lineage_attribution='Retain all original PINS and package CREDITS.md, NOTICE and SOURCES.json; PR2942/2930/2917/2908 and all retained predecessors remain credited.')
        word_pins[provider] = pin
    _META = dict(acquisition=acquisition, files=files, pins=pins, manifest=manifest,
                 word_pins=word_pins, credit_files=credit_files, credit_text=credit_text, claim=claim)
    return _META


def provenance():
    """All original attribution and complete PR2966 credit bindings; no audit."""
    m = _metadata()
    return dict(source_attribution=[dict(path=k, **deepcopy(v)) for k,v in m['pins'].items()] +
                    [deepcopy(m['word_pins'][p]) for p in ('base','extra')],
                source_credits=deepcopy(m['credit_files']), credit_contents=deepcopy(m['credit_text']),
                inherited_pins=dict(path='data/words/PINS.json', sha256=PINS_SHA),
                source_acquisition=dict(path=str((DIRECTORY/'ACQUISITION.json').relative_to(RR)),
                                        sha256=ACQUISITION_SHA, head=HEAD, pr=2966),
                package_manifest=dict(path=str((DIRECTORY/'package/MANIFEST.json').relative_to(RR)),
                                      sha256=MANIFEST_SHA),
                trusted_sources=source_manifest(),
                source_scope='Author-reported PR2966 is pinned inert input. Only the requested finite local tier is evaluated; inherited outer/native claims are not accepted by this adapter.')


def prepare():
    """Once-only parent loading; returns immutable-by-contract raw records."""
    global _RECORDS
    if _RECORDS is not None:
        return _RECORDS
    m = _metadata()
    _modules()
    # Authenticate every acquired byte while parsing only the two word objects.
    for relative, pin in m['files'].items():
        path = (RR / pin['local_path']).resolve()
        need(path.is_relative_to((DIRECTORY / 'package').resolve()), 'inert package confinement')
        raw = _checked_bytes(path, pin['sha256'], pin['bytes'], pin['git_blob'])
        if relative in m['manifest']:
            need(m['manifest'][relative] == pin['sha256'], 'package manifest binding: ' + relative)
    records = {}
    for provider in ('base','extra'):
        pin = m['word_pins'][provider]
        path = RR / pin['local_path']
        packed = _checked_bytes(path, pin['sha256'], pin['bytes'], pin['git_blob'])
        raw = _json(packed, compressed=True)
        expected_profile = dict(PROFILE)
        inventory = dict(INVENTORY)
        records[provider] = dict(provider=provider, raw=raw, attribution=deepcopy(pin),
            source_pin=deepcopy(pin), expected_profile=expected_profile, expected_inventory=inventory,
            expected_buffers=BUFFERS, expected_physical_families=DECLARED_PHYSICAL_FAMILIES,
            expected_independent_inputs=632, expected_helpers=408,
            original_semantic_sha256=semantic_sha(raw),
            source_status='UNCHANGED_PINNED_PR2966')
    _RECORDS = records
    return _RECORDS


def get_record(provider):
    need(_RECORDS is not None, 'call prepare() once in the parent before pool launch')
    need(provider in _RECORDS, 'unknown provider/control')
    return _RECORDS[provider]


def baseline_task(spec):
    """Registered finite baseline check; no source constructor or native claim."""
    started = time.process_time()
    provider, seed = spec['provider'], spec['seed']
    need(type(seed) is int, 'integer recorded seed required')
    record = get_record(provider)
    raw, attribution = record['raw'], record['attribution']
    need(semantic_sha(raw) == record['original_semantic_sha256'], 'prepared raw source was mutated')
    W, A = _modules()
    canonical = W.WordData(raw, attribution)
    need((canonical.v, canonical.h, canonical.R, len(canonical.live), len(canonical.helpers)) ==
         (112,9,480,632,408), 'baseline dimensions, input columns and helper census')
    need(canonical.family == 'BORROW-WORD' and canonical.paid == record['expected_profile'],
         'canonical source paid profile')
    widths = [len(canonical.end[h])-len(canonical.start[h]) for h in canonical.helpers]
    need(dict(Counter(widths)) == record['expected_inventory'], 'canonical source width inventory')
    cleanup = canonical.cleanup_check(scalar_replay=False)
    need(cleanup['status'] == 'PASS' and cleanup['literal_equality'] is True and cleanup['exact'] is True,
         'exact derived inverse-reverse cleanup')
    result = A.local_admission(raw, attribution)
    audit = result['audit']
    need(result['status'] == 'PASS' and audit['status'] == 'PASS_INDEPENDENT_EXACT_BORROWING_WORD',
         'independent free-operator audit')
    need(audit['checked_columns'] == audit['independent_inputs'] == record['expected_independent_inputs'] and
         audit['orientations'] == {'forward':'PASS','dual':'PASS'}, 'all632 inputs in both orientations')
    need(audit['restored_cold'] == audit['zero_buffers'] == len(raw['helper_final']) == record['expected_buffers'],
         'all restored endpoints and private zero buffers charged')
    need(result['paid_profile'] == canonical.paid and result['widths'] == widths and
         result['ordered_helpers'] == canonical.helpers, 'independent/canonical exact ledger parity')
    need(audit['local_mass'] == sum(k*v for k,v in canonical.paid.items()) == sum(widths)+1856,
         'exact local rank-mass identity')
    need(semantic_sha(raw) == record['original_semantic_sha256'], 'audit did not mutate pinned source')
    return dict(status='PASS', provider=provider, seed=seed, source_status=record['source_status'],
        source_pin=deepcopy(record['source_pin']), baseline_word_semantic_sha256=record['original_semantic_sha256'],
        canonical=dict(paid_profile=canonical.paid, width_inventory=dict(Counter(widths)),
                       ordered_helpers=canonical.helpers, widths=widths, cleanup=cleanup,
                       independent_inputs=len(canonical.live), zero_buffers=audit['zero_buffers'],
                        declared_physical_families=DECLARED_PHYSICAL_FAMILIES,
                        physical_families_independently_checked=False),
        local_admission=result,
        compensation=dict(gates=len(raw['compensation']), semantic_sha256=semantic_sha(raw['compensation']),
            exactness='Included literally with initial corrections in the independent632-column forward/dual audit; no separate compensation-minimality claim.'),
        n_permutations=0, cpu_seconds=time.process_time()-started,
        seed_use='Deterministic exact baseline check; second seed independently repeats the same frozen source obligations.',
        native_physical_owner_root_outer_checked=False,
        scope='Finite local algebra and exact frame/cleanup accounting only; no new bound or full theorem claim.',
        **provenance())
