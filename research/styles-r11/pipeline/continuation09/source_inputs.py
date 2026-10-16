"""Pinned PR3015 words with the separately attributed PR3028 comparator.

Fetched programs are authenticated inert data only. Scientific preparation is
called by the registered parent; baseline tasks run through the central pool.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

PKG = Path(__file__).resolve().parents[2]
ADAPTER_SHA = 'bbc8c770d8540278988e32946069ee225be6ee1d39b13780ac392587e11261af'
ACQUISITION_SHA = 'dd20434c5b53fa7927b0b4090d985dd27dada6d165ebeae3873d93e52c821284'
BINDINGS_SHA = 'bdaa7a5c5193875280cd0d3e20a735e8694480de093fa0f8759e2fc085b542a0'
COMPARATOR_HEAD = '9d10633660a3dff5469f4e7a0a009a6c9994c0d7'
ENDPOINT = '34583046742859167313/20000000000000000000000'
_INNER = _SOURCE = _STATE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def checked(ref):
    path = (PKG / ref['path']).resolve()
    need(path.is_relative_to(PKG) and path.suffix != '.py', 'confined inert source input')
    raw = path.read_bytes()
    need(sha(raw) == ref['sha256'], 'exact source input: ' + ref['path'])
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'exact source byte count')
    if 'git_blob' in ref:
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == ref['git_blob'],
             'exact source Git blob')
    return raw


def prepare():
    global _INNER, _SOURCE, _STATE
    if _STATE is not None:
        return _STATE
    need(sys.flags.isolated and not sys.flags.optimize, 'isolated Python with assertions')
    path = PKG / 'pipeline/continuation08/source3015.py'
    need(sha(path.read_bytes()) == ADAPTER_SHA, 'frozen trusted word adapter')
    spec = importlib.util.spec_from_file_location('styles09_pinned_source3015', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    _INNER = module
    state = module.prepare()
    _SOURCE = module._SOURCE
    directory = PKG / 'data/continuation-09/pr3028'
    acq_path, bind_path = directory / 'ACQUISITION.json', directory / 'SOURCE-BINDINGS.json'
    need(sha(acq_path.read_bytes()) == ACQUISITION_SHA and sha(bind_path.read_bytes()) == BINDINGS_SHA,
         'exact3028 compact acquisition and source bindings')
    acq, bindings = json.loads(acq_path.read_bytes()), json.loads(bind_path.read_bytes())
    need(acq['pr'] == bindings['pr'] == 3028 and acq['head'] == bindings['head'] == COMPARATOR_HEAD and
         acq['author_login'] == 'petalas' and not acq['errors'], 'exact comparator release identity')
    need(len(acq['files']) == 22 and len({r['path'] for r in acq['files']}) == 22, 'complete compact inventory')
    payloads = {row['path']: checked(row) for row in acq['files']}
    need(sum(map(len, payloads.values())) == acq['total_bytes'], 'all source bytes accounted')
    for ref in bindings['sources'].values():
        checked(ref)
    checked(bindings['original_pins'])
    for item in bindings['complete_inherited_credit_files']:
        existing = checked(item['existing_artifact'])
        need(sha(existing) == item['upstream_vendor_binding']['sha256'], 'inherited credit binding')
    claim = json.loads(checked(bindings['sources']['claim']))
    need(Fraction(claim['kappa_rational']) + Fraction(1,10**46) + Fraction(1,10**70) == Fraction(ENDPOINT)
         and bindings['complex_endpoint'] == ENDPOINT, 'exact reported comparison endpoint arithmetic')
    need(bindings['source_reported_only'] and bindings['helpers'] == 408 and
         bindings['independent_inputs'] == 632 and bindings['private_buffers'] == 91 and
         bindings['replicas'] == 148 and bindings['physical_families'] == 133117,
         'source-reported comparator scope and dimensions')
    for provider, record in state['records'].items():
        word = bindings['words'][provider]
        raw = checked(word['existing_artifact'])
        need(word['byte_identity_verified'] and sha(raw) == record['source_pin']['sha256'] ==
             word['native_receipt_word_sha256'], 'exact3015word reused in3028 source receipt')
        need({int(k): v for k,v in word['reported_local_profile'].items()} == record['expected_profile'],
             'unchanged local profile')
    provenance = deepcopy(state['provenance'])
    comparison_pin = deepcopy(next(row for row in acq['files'] if row['path'] == bindings['sources']['claim']['path']))
    comparison_pin.update(pr=3028, commit=COMPARATOR_HEAD, author='Nick Petalas (petalas)',
                          source='Source-reported T148 composition comparator; not independent admission here')
    provenance['source_attribution'].append(comparison_pin)
    provenance['comparison'] = dict(pr=3028, head=COMPARATOR_HEAD, author='Nick Petalas (petalas)',
        endpoint=ENDPOINT, replicas=148, physical_families=133117, source_reported_only=True,
        fresh_native_physical_outer=False,
        scope='The word-source metadata describes PR3015 atT74. The comparison release hasT148 and a separate allocation/physical ledger; no changed candidate is admitted by this reuse.')
    provenance['comparison_acquisition'] = dict(path=str(acq_path.relative_to(PKG)),sha256=ACQUISITION_SHA)
    provenance['comparison_bindings'] = dict(path=str(bind_path.relative_to(PKG)),sha256=BINDINGS_SHA)
    provenance['comparison_claim'] = comparison_pin
    _STATE = dict(state, provenance=provenance, endpoint=ENDPOINT, comparison_bindings=bindings)
    return _STATE


def baseline_task(spec):
    need(_STATE is not None, 'prepare once in parent')
    value = _INNER.baseline_task(spec)
    value['word_source_declared_physical_families'] = value.pop('declared_physical_families')
    value['comparison_source_declared_physical_families'] = 133117
    value['comparison_replicas'] = 148
    return value
