"""Authenticated PR3015 data and PR2979 positive fixture; registered parent only.

All acquired files are inert. Only existing hash-pinned local r11 tools are
imported. prepare() loads each word once; baseline_task runs in the central pool.
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
ROOT = PKG.parents[1]
DIRECTORY = PKG / 'data/continuation-07/holdout3015'
ACQUISITION_SHA = 'd0b48e18b559fc323cdd9e12a402d8f42b48ead8c8629f61e5d062f9adf1dde7'
HEAD = 'e244296debb45fe6f4da84d29e4d64fbab55fda0'
WORD_SHA = {'base': '77d9be7ac47347894e034d8b67bf07ff8a5e1c317923ed5dd9257c492187dcf5',
            'extra': '18d9c448ce892aa19f162e214760d0bd4ecb09f814b9b859dbf11f3ca637e9ea'}
SOURCE2979_SHA = 'fb8c5f84e076ebd0514800139b9310539ca56f4808dd92889744dee067e65bbd'
PROFILE = {1: 2443, 2: 707, 3: 232, 4: 108, 5: 18, 8: 8}
INVENTORY = {4: 26, 5: 2, 6: 16, 7: 52, 8: 99, 9: 213}
_STATE = None
_SOURCE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def semantic(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def read_json(raw, compressed=False):
    return json.loads(gzip.decompress(raw) if compressed else raw)


def checked(ref):
    path = (PKG / ref['path']).resolve()
    need(path.is_relative_to(PKG), 'inert source path confined to styles package')
    raw = path.read_bytes()
    need(sha(raw) == ref['sha256'], 'inert source SHA: ' + ref['path'])
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'inert source byte count')
    if 'git_blob' in ref:
        actual = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        need(actual == ref['git_blob'], 'inert source Git blob')
    need(path.suffix != '.py', 'acquired program must remain inert text')
    return raw


def prepare():
    global _STATE, _SOURCE
    if _STATE is not None:
        return _STATE
    need(sys.flags.isolated and not sys.flags.optimize, 'isolated Python and enabled assertions')
    path = PKG / 'pipeline/continuation05/source2979.py'
    need(sha(path.read_bytes()) == SOURCE2979_SHA, 'frozen fixture adapter')
    spec = importlib.util.spec_from_file_location('styles08_frozen_source2979', path)
    source = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = source
    spec.loader.exec_module(source)
    fixtures = source.prepare()
    _SOURCE = source
    acquisition_path = DIRECTORY / 'ACQUISITION.json'
    need(sha(acquisition_path.read_bytes()) == ACQUISITION_SHA, 'frozen 3015 acquisition')
    acquisition = read_json(acquisition_path.read_bytes())
    need(acquisition['pr'] == 3015 and acquisition['head'] == HEAD and
         acquisition['author'] == 'jeremykothe2', 'exact release identity and author')
    files = {f['path'].split('/package/', 1)[1]: f for f in acquisition['files']}
    need(len(files) == len(acquisition['files']) == 37, 'compact source inventory')
    payloads = {name: checked(ref) for name, ref in files.items()}
    manifest = read_json(payloads['MANIFEST.json'])
    count = 0
    for name, raw in payloads.items():
        if name in manifest:
            need(manifest[name] == sha(raw), 'exact upstream manifest membership')
            count += 1
    need(count == acquisition['manifest_entries_checked'] == 36, 'all compact manifest memberships')
    claim = read_json(payloads['CLAIM.json'])
    declaration = read_json(payloads['edits/EDITS.json'])
    need({int(k): v for k, v in claim['local_profile'].items()} == PROFILE and
         {int(k): v for k, v in claim['width_inventory'].items()} == INVENTORY and
         claim['zero_buffers'] == 91 and claim['physical_families'] == 66813,
         'source-declared local and physical contract')
    need(claim['release_receipt_sha256'] == files['evidence/RELEASE-RECEIPT.json']['sha256'],
         'exact complete source receipt binding, not independent admission')
    records = {}
    for provider in ('base', 'extra'):
        name = 'edits/FINAL-WORD-' + provider + '.json.gz'
        pin = deepcopy(files[name])
        need(pin['sha256'] == WORD_SHA[provider], 'current provider word byte pin')
        pin.update(pr=3015, commit=HEAD, author='Jeremy Kothe (jeremykothe2)',
                   author_login='jeremykothe2', format='BORROW-WORD',
                   source='PR3015 complete declared restore edit on PR2979; all inherited credits retained')
        raw = read_json(payloads[name], True)
        records[provider] = dict(provider=provider, raw=raw, attribution=deepcopy(pin),
            source_pin=deepcopy(pin), expected_profile=dict(PROFILE),
            expected_inventory=dict(INVENTORY), expected_buffers=91,
            expected_physical_families=66813, expected_independent_inputs=632,
            expected_helpers=408, original_semantic_sha256=semantic(raw),
            source_status='UNCHANGED_PINNED_PR3015')
        need(read_json(payloads['data/WORD-' + provider + '.json.gz'], True) == fixtures[provider]['raw'],
             'exact PR2979 positive-fixture parent')
    inherited = source.provenance()
    provenance = dict(
        source_attribution=inherited['source_attribution'] + [records[p]['attribution'] for p in ('base', 'extra')],
        inherited_source_provenance=inherited,
        release_acquisition=dict(path=str(acquisition_path.relative_to(PKG)), sha256=ACQUISITION_SHA),
        release_claim=files['CLAIM.json'], release_manifest=files['MANIFEST.json'],
        release_receipt=files['evidence/RELEASE-RECEIPT.json'],
        declared_positive_fixture=files['edits/EDITS.json'],
        source_credit_files=acquisition['source_credit_files'],
        source_credit_contents={name: read_json(payloads[name]) if name.endswith('.json') else payloads[name].decode()
                               for name in ('CREDITS.md', 'NOTICE', 'SOURCES.json')},
        scope='Compact inert producer evidence; this adapter does not establish fresh native, physical or outer admission.')
    _STATE = dict(records=records, fixtures=fixtures, declaration=declaration,
                  provenance=provenance, source_claim=claim,
                  endpoint=str(Fraction(claim['complex_lower'])))
    return _STATE


def baseline_task(spec):
    need(_STATE is not None, 'prepare once in the parent')
    begin = time.process_time()
    provider, seed = spec['provider'], int(spec['seed'])
    record = _STATE['records'][provider]
    W, A = _SOURCE._modules()
    raw, attribution = record['raw'], record['attribution']
    word = W.WordData(raw, attribution)
    need(word.paid == PROFILE and (word.v, word.h, word.R, len(word.live), len(word.helpers)) ==
         (112, 9, 480, 632, 408), 'canonical baseline profile and dimensions')
    widths = [len(word.end[h]) - len(word.start[h]) for h in word.helpers]
    need(dict(Counter(widths)) == INVENTORY, 'ordered-helper width inventory')
    audit = A.local_admission(raw, attribution)
    need(audit['status'] == 'PASS' and audit['paid_profile'] == PROFILE and audit['widths'] == widths,
         'canonical and independent ledgers agree')
    finite = audit['audit']
    need(finite['checked_columns'] == finite['independent_inputs'] == 632 and
         finite['orientations'] == {'forward': 'PASS', 'dual': 'PASS'} and
         finite['restored_cold'] == finite['zero_buffers'] == 91,
         'all forward/dual columns and restored buffers')
    need(semantic(raw) == record['original_semantic_sha256'], 'source not mutated')
    return dict(status='PASS', seed=seed, provider=provider,
        source_pin=record['source_pin'], source_semantic_sha256=semantic(raw),
        local_admission=audit, declared_physical_families=66813,
        fresh_native_physical_outer=False, cpu_seconds=time.process_time() - begin)
