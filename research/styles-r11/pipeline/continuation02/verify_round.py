"""Integrity-only audit of CONTINUATION-02; no scientific modules are imported.

Read stored JSON, bytes, Git tree metadata and exact rational bookkeeping only.
The coordinator runs this after all experiments and hand-back files are closed.
Use -I -B; --write creates the first immutable FINAL-AUDIT.json. Repeated runs
compare its stable payload without changing it. Original rounds are never edited.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction as Q
from itertools import product
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[1]
RESULTS = PKG / 'results'
ROUND = RESULTS / 'CONTINUATION-02'
DATA = PKG / 'data/continuation-02/checkpoint'
BASE = 'ee8ae6a23b761cfe8a9aa5c9723e54ff0e9b467c'
FAMILY = 'G2-ANCHORED-RANK7'
VALIDATION = 'V3-INVENTORY-CAP'
SEEDS = (12037, 31069)
PROVIDERS = ('extra', 'gauge44')
MODES = ('literal', 'downward_cap')
PREG_SHA = '678046f825d5943bc768afba378c3e59a37e7de1194e7b1f8c3b149a13a41526'
LIMIT = 200 * 1024 ** 2
REQUIRED = {'schema_version', 'experiment', 'milestone', 'seed', 'recorded_utc',
            'status', 'n_permutations', 'statistics', 'source_attribution',
            'word_blob_ids', 'script_sha256', 'script_manifest_sha256',
            'preregistration_sha256', 'wall_seconds', 'cpu_seconds',
            'peak_rss_bytes', 'null_summary', 'decision', 'confirmation_required'}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


def read(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def references(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def address(row):
    return (int(row['helper']), tuple(row['plane']), row['mode'], tuple(row['basis_indices']))


def address_data(key):
    return [key[0], list(key[1]), key[2], list(key[3])]


class Review:
    def __init__(self):
        self.errors, self.sections, self.files = [], {}, {}
        self.archives, self.receipts, self.attempts = {}, {}, {}
        self.v3_receipts = {}
        self.original_pins = read(PKG / 'data/words/PINS.json')['files']
        self.protocol = read(ROUND / 'G2/PREREGISTRATION.json')
        self.aliases = {}

    def section(self, name, method):
        try:
            self.sections[name] = method()
        except Exception as exc:
            self.errors.append(dict(section=name, type=type(exc).__name__, message=str(exc)))
            self.sections[name] = dict(status='ERROR')

    def file(self, path, expected=None, size=None, git_blob=None, decoded=None):
        path = Path(path).resolve()
        need(path.is_relative_to(ROOT), 'file outside repository: ' + str(path))
        raw = path.read_bytes()
        name = str(path.relative_to(ROOT))
        actual = dict(path=name, sha256=sha(raw), bytes=len(raw))
        if expected is not None:
            need(actual['sha256'] == expected, 'SHA256 mismatch: ' + name)
        if size is not None:
            need(len(raw) == size, 'size mismatch: ' + name)
        if git_blob is not None:
            need(blob(raw) == git_blob, 'Git blob mismatch: ' + name)
        if decoded is not None:
            payload = gzip.decompress(raw) if path.name.endswith('.gz') else raw
            need(sha(payload) == decoded, 'decoded SHA256 mismatch: ' + name)
        self.files[name] = actual
        return actual

    def resolve(self, ref):
        if ref.get('local_path'):
            return PKG / ref['local_path']
        path = ref['path']
        if (path, ref.get('sha256')) in self.aliases:
            return self.aliases[path, ref['sha256']]
        if path.startswith('research/'):
            return ROOT / path
        if path.startswith(('results/', 'data/', 'pipeline/')):
            return PKG / path
        if path in self.original_pins:
            return PKG / 'data/words' / path
        raise ValueError('unresolved local reference: ' + path)

    def reference(self, ref):
        return self.file(self.resolve(ref), ref['sha256'], ref.get('bytes'), ref.get('git_blob'),
                         ref.get('payload_sha256', ref.get('uncompressed_sha256')))

    def local_references(self, value):
        count = 0
        for ref in references(value):
            name = ref['path']
            if (ref.get('local_path') or name.startswith(('research/styles-r11/', 'results/', 'data/'))
                    or (name, ref['sha256']) in self.aliases or name in self.original_pins):
                self.reference(ref)
                count += 1
        return count

    def source_data(self):
        for name, pin in self.original_pins.items():
            path = ROOT / name if '/' in name else PKG / 'data/words' / name
            self.file(path, pin['sha256'], pin['bytes'], pin['git_blob'])
            self.aliases[name, pin['sha256']] = path
        manifest_path = PKG / 'data/continuation-01/pr2917/MANIFEST.json'
        self.file(manifest_path, self.protocol['baseline']['manifest_sha256'])
        manifest = read(manifest_path)
        need(manifest['commit'] == self.protocol['baseline']['commit'], 'PR2917 exact source head')
        for pin in manifest['files']:
            path = PKG / pin['local_path']
            self.file(path, pin['sha256'], pin.get('bytes'), pin.get('git_blob'))
            for key in ('path', 'relative_path', 'local_path'):
                if key in pin:
                    self.aliases[pin[key], pin['sha256']] = path
        receipt = read(DATA / 'RECEIPT.json')
        self.file(DATA / 'RECEIPT.json')
        need(receipt['canonical_main'] == '914cd73f563acaaa682d733a9fbfcc07272336a3'
             and receipt['priority_revision'] == 5, 'canonical guidance checkpoint')
        for name, pin in receipt['files'].items():
            self.file(DATA / name, pin['sha256'], pin['bytes'], decoded=pin.get('uncompressed_sha256'))
        for pin in receipt['guidance']:
            raw = gzip.decompress((DATA / pin['file']).read_bytes())
            need(blob(raw) == pin['git_blob'], 'canonical guidance Git blob')
        self.file(PKG / 'pipeline/continuation02/checkpoint_sources.py', receipt['script_sha256'])
        focus = read(DATA / 'FOCUS-RECEIPT.json')
        self.file(DATA / 'FOCUS-RECEIPT.json')
        self.file(ROOT / focus['path'], focus['sha256'], decoded=focus['uncompressed_sha256'])
        acquisition = read(DATA / 'pr2930/ACQUISITION.json')
        self.file(DATA / 'pr2930/ACQUISITION.json')
        need(acquisition['commit'] == self.protocol['target']['head'] and len(acquisition['files']) == 20,
             'exact twenty-file PR2930 acquisition')
        self.file(PKG / 'pipeline/continuation02/checkpoint_pr2930.py', acquisition['script_sha256'])
        for pin in acquisition['files']:
            path = PKG / pin['local_path']
            self.file(path, pin['sha256'], pin['bytes'], pin['git_blob'])
            self.aliases[pin['path'], pin['sha256']] = path
        target = self.protocol['target']
        self.file(PKG / target['path'], target['sha256'])
        need(read(PKG / target['path'])['complex_lower'] == target['complex_lower'], 'exact competitive endpoint')
        allocation = read(PKG / 'data/continuation-02/packing-source/ACQUISITION.json')
        self.file(PKG / 'data/continuation-02/packing-source/ACQUISITION.json')
        need(allocation['head'] == target['head'] and allocation['pr'] == 2930,
             'subsequent allocation acquisition uses the same frozen head')
        self.file(PKG / allocation['local_path'], allocation['sha256'], allocation['bytes'],
                  allocation['git_blob'], allocation['uncompressed_sha256'])
        claim = read(PKG / target['path'])
        allocation_pins = read(DATA / 'pr2930/ALLOCATION-PINS.json')
        package_manifest = read(DATA / 'pr2930/MANIFEST.json')
        need(allocation['sha256'] == claim['fill_sha256'] == allocation_pins['allocation/FILL.json.gz']
             == package_manifest['allocation/FILL.json.gz'], 'literal allocation has three frozen bindings')
        for pin in allocation['bindings'] + allocation['source_credit_files']:
            self.reference(pin)
            if 'copied_from' in pin:
                need((PKG / pin['path']).read_bytes() == (PKG / pin['copied_from']).read_bytes(),
                     'complete allocation source credit copied byte-for-byte')
        return dict(status='PASS', original_words=len(self.original_pins),
                    pr2917_files=len(manifest['files']), pr2930_files=20,
                    later_literal_allocation_files=1,
                    metadata_prs=receipt['distinct_prs'], metadata_coverage_limits=receipt['coverage_limits'],
                    fetched_code='Authenticated as inert bytes only; no imports or execution')

    def protocol_sources(self):
        self.file(ROUND / 'G2/PREREGISTRATION.json', PREG_SHA)
        need(self.protocol['state'] == 'FROZEN' and tuple(self.protocol['seeds']) == SEEDS,
             'frozen family and seed pair')
        for directory in ('C4', 'V2'):
            value = read(ROUND / directory / 'PREREGISTRATION.json')
            self.file(ROUND / directory / 'PREREGISTRATION.json')
            need(value['state'] == 'FROZEN', 'retired preregistration retained')
        self.validation_protocol = read(ROUND / 'V3/PREREGISTRATION.json')
        self.validation_preg_sha = sha((ROUND / 'V3/PREREGISTRATION.json').read_bytes())
        self.file(ROUND / 'V3/PREREGISTRATION.json')
        need(self.validation_protocol['state'] == 'FROZEN' and
             self.validation_protocol['experiment'] == VALIDATION and
             tuple(self.validation_protocol['seeds']) == SEEDS, 'frozen exact inventory-cap protocol')
        self.local_references(self.validation_protocol)
        for path in sorted((ROUND / 'SOURCES').glob('*.py.gz')):
            digest = path.name[:-6]
            need(len(digest) == 64 and sha(gzip.decompress(path.read_bytes())) == digest,
                 'source archive content/name binding: ' + path.name)
            self.file(path)
            self.archives[digest] = str(path.relative_to(PKG))
        need(self.archives, 'scientific source archive required')
        pin_files = list((ROUND / 'G2').glob('*PINS*.json')) + list((ROUND / 'V3').glob('*PINS*.json'))
        need(pin_files, 'frozen implementation pins required')
        self.implementation_pins = {sha(p.read_bytes()): read(p) for p in pin_files}
        for path in pin_files:
            self.file(path)
        for path in sorted((ROUND / 'G2').glob('*AMEND*.json')):
            self.file(path)
            self.local_references(read(path))
        return dict(status='PASS', preregistrations=4, source_archives=len(self.archives),
                    implementation_pin_records=len(pin_files))

    def final_checkpoint(self):
        directory = PKG / 'data/continuation-02/final-checkpoint'
        receipt = read(directory / 'RECEIPT.json')
        self.file(directory / 'RECEIPT.json')
        need(receipt['canonical_main'] == '95ff4e2dd396c505932a43ff7c1cdfdd94b8c867',
             'final read-only main checkpoint')
        for name, pin in receipt['files'].items():
            self.file(directory / name, pin['sha256'], pin['bytes'], decoded=pin['uncompressed_sha256'])
            source = pin['source']
            if 'git_blob' in source:
                need(blob(gzip.decompress((directory / name).read_bytes())) == source['git_blob'],
                     'final guidance exact Git blob')
        for item in receipt['guidance_comparison']:
            name = item['path'].replace('/', '__') + '.gz'
            need(item['changed_from_initial'] is False and
                 gzip.decompress((directory / name).read_bytes()) == gzip.decompress((DATA / name).read_bytes()),
                 'final priority/guidance/selected files unchanged')
        fetch = read(directory / 'GIT-FETCH.json')
        self.file(directory / 'GIT-FETCH.json')
        need(fetch['canonical_main'] == fetch['earlier_api_main'] == receipt['canonical_main'] and
             fetch['same_head'] is True and fetch['scientific_inputs_repinned'] is False and
             fetch['worktree_merged_or_rebased'] is False, 'final Git fetch preserves scientific source pins')
        for item in fetch['guidance_comparison']:
            payload = gzip.decompress((directory / (item['path'].replace('/', '__') + '.gz')).read_bytes())
            need(item['unchanged_from_final_api_checkpoint'] is True and sha(payload) == item['sha256'],
                 'final Git/API guidance byte agreement')
        recent = read(directory / 'recent-prs.json.gz')
        heads = {row['number']: row for row in recent}
        need(heads[2942]['head'] == 'a027b0f6fdb0ab2b42ba10fc31b53960166bf2bf' and
             heads[2943]['head'] == '289b98dd833ffdee69ae9f41d779fa9991990805', 'newer public source heads retained')
        return dict(status='PASS', canonical_main=receipt['canonical_main'],
                    started_utc=receipt['started_utc'], finished_utc=receipt['finished_utc'],
                    unchanged_guidance_files=len(receipt['guidance_comparison']),
                    stronger_reported_public_source=dict(pr=2942, head=heads[2942]['head'],
                        scope='Metadata claim only; not a new scientific input or locally replayed admission.'),
                    coverage='Thirty most recently updated PRs plus four exact relevant heads and Discussion2612; not another complete PR/discussion census.')

    def results(self):
        paths = sorted((ROUND / FAMILY).rglob('RESULT.json'))
        need(paths, 'executed G2 receipts required')
        historical_drift = []
        for path in paths:
            parts = path.relative_to(ROUND).parts
            need(len(parts) == 4 and parts[0] == FAMILY and parts[1].startswith('v')
                 and parts[2].startswith('seed-'), 'only registered G2 RESULT paths')
            attempt, seed = parts[1], int(parts[2][5:])
            value = read(path)
            self.file(path)
            need(REQUIRED <= set(value), 'required RESULT schema')
            need((value['schema_version'], value['experiment'], value['milestone'], value['seed']) ==
                 (1, FAMILY, 'CONTINUATION-02', seed) and seed in SEEDS, 'receipt identity')
            need(value['status'] in ('NULL', 'EXPLORATORY', 'ERROR', 'TIMEOUT') and
                 value['decision']['verdict'] == value['status'], 'scoped G2 verdict; no premature kappa PASS')
            need(value['n_permutations'] == 0 and value['confirmation_required'] is True, 'exact two-seed protocol')
            need(value['preregistration_sha256'] == PREG_SHA, 'receipt preregistration binding')
            need(value['decision']['pass_bar'] == self.protocol['pass_bar'] and
                 value['decision']['null_bar'] == self.protocol['null_bar'], 'unchanged decision bars')
            for key in ('cpu_seconds', 'wall_seconds'):
                need(isinstance(value[key], (int, float)) and math.isfinite(value[key]) and value[key] >= 0,
                     'finite recorded resource: ' + key)
            if value['peak_rss_bytes'] is not None:
                need(0 <= value['peak_rss_bytes'] <= 4 * 1024 ** 3, 'four GiB worker RSS')
            attrs = {p['path']: p for p in value['source_attribution']}
            need(len(attrs) == len(value['source_attribution']) == 23, 'all original and provider source credits')
            for name, pin in self.original_pins.items():
                need(name in attrs and all(attrs[name].get(k) == v for k, v in pin.items()),
                     'original attribution preserved: ' + name)
            need(value['word_blob_ids'] == {k: p['git_blob'] for k, p in attrs.items()}, 'word blob map')
            for pin in attrs.values():
                need(pin.get('author'), 'source author retained')
                self.reference(pin)
            sources = value['script_sha256']
            need(value['script_manifest_sha256'] == sha(canonical(sources)), 'source manifest digest')
            pin_digest = value['implementation_pins_sha256']
            need(pin_digest in self.implementation_pins, 'immutable implementation pin record')
            for source, digest in sources.items():
                need(digest in self.archives, 'exact archived source missing: ' + source)
                current = ROOT / source
                if not current.is_file() or sha(current.read_bytes()) != digest:
                    historical_drift.append(dict(attempt=attempt, source=source, sha256=digest,
                                                 archive=self.archives[digest]))
            self.receipts[attempt, seed] = value
            run = path.parent.parent
            self.attempts[attempt] = run
            implementation = run / 'IMPLEMENTATION.json'
            if implementation.exists():
                frozen = read(implementation)
                self.file(implementation)
                need(frozen['script_sha256'] == sources and frozen['preregistration_sha256'] == PREG_SHA
                     and frozen['implementation_pins_sha256'] == pin_digest, 'frozen run implementation binding')
            else:
                need(value['status'] in ('ERROR', 'TIMEOUT') and not sources,
                     'successful run must have frozen implementation')
            if value['status'] in ('NULL', 'EXPLORATORY'):
                need(value.get('launch_failure') is None and value['statistics']['complete'] is True
                     and not value.get('task_errors'), 'completed scientific record has no hidden errors')
            self.local_references(value)
        for attempt, run in self.attempts.items():
            need(all((attempt, seed) in self.receipts for seed in SEEDS), 'both seed receipts retained')
            summary = read(run / 'RUN.json')
            self.file(run / 'RUN.json')
            pair = [self.receipts[attempt, s] for s in SEEDS]
            need(pair[0]['status'] == pair[1]['status'] == summary['status'], 'run/seed status agreement')
            need(math.isclose(sum(v['cpu_seconds'] for v in pair), summary['total_cpu_seconds'],
                              rel_tol=0, abs_tol=1e-6), 'CPU assigned exactly once across seed receipts')
        return dict(status='PASS', receipt_count=len(self.receipts), attempts=sorted(self.attempts),
                    status_counts=dict(Counter(v['status'] for v in self.receipts.values())),
                    measured_experiment_cpu_seconds=sum(v['cpu_seconds'] for v in self.receipts.values()),
                    archived_source_drift=historical_drift)

    def task_records(self):
        out = {}
        for attempt, run in sorted(self.attempts.items()):
            complete = read(run / 'RUN.json')['status'] in ('NULL', 'EXPLORATORY')
            phases = {}
            for phase in ('controls', 'screen', 'cap', 'validation'):
                task_file = run / (phase.upper() + '-TASKS.json.gz')
                if not task_file.exists():
                    continue
                self.file(task_file)
                specs = read(task_file)
                saved = {}
                for path in sorted((run / phase).glob('task-*.json.gz')):
                    index = int(path.name[5:-8])
                    need(index not in saved and 0 <= index < len(specs), 'unique checkpoint task index')
                    self.file(path)
                    item = read(path)
                    saved[index] = dict(spec=specs[index], item=item)
                    self.local_references(item)
                if complete:
                    need(set(saved) == set(range(len(specs))), 'complete checkpoint inventory: ' + phase)
                    need(all(x['item']['status'] == 'OK' for x in saved.values()), 'successful pool tasks: ' + phase)
                phases[phase] = dict(specs=specs, saved=saved)
            self.attempts[attempt] = dict(path=run, complete=complete, phases=phases)
            out[attempt] = {phase: dict(tasks=len(v['specs']), checkpoints=len(v['saved'])) for phase, v in phases.items()}
        return dict(status='PASS', attempts=out)

    def controls_coverage(self):
        expected_planes = {tuple(sorted((a, b, a ^ b)))
                           for a in (7, 42, 45) for b in range(1, 512) if b != a}
        need(len(expected_planes) == 763, 'registered finite domain bookkeeping')
        out = {}
        for attempt, info in sorted(self.attempts.items()):
            if not info['complete']:
                out[attempt] = dict(status='INCOMPLETE_PRESERVED', scientific_null=False)
                continue
            controls = info['phases']['controls']['saved']
            expected_controls = {(kind, seed, pid) for kind in ('published_control',)
                                 for seed in SEEDS for pid in PROVIDERS}
            expected_controls |= {(kind, seed, None) for kind in ('rank7_control', 'cap_control') for seed in SEEDS}
            got_controls = set()
            for entry in controls.values():
                spec, value = entry['spec'], entry['item']['result']
                got_controls.add((spec['kind'], spec['seed'], spec.get('provider')))
                need(value['status'] == 'PASS', 'all enabled controls PASS')
                if spec['kind'] == 'published_control':
                    for field in ('baseline', 'positive_first_stage_audit'):
                        audit = value[field]['audit']
                        need(audit['checked_columns'] == 632 and audit['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
                             'all-column both-orientation positive control')
                    positive = value['positive_nine_stage']
                    need(positive['exact_final_payload_equality'] is True and len(positive['stages']) == 9,
                         'nine-stage exact reconstruction')
                    need(len(value['negative_controls']) == 4 and
                         all(x['status'] == 'PASS_REJECTED' for x in value['negative_controls']), 'semantic negative controls')
                elif spec['kind'] == 'rank7_control':
                    need(value['distinct_dual_planes'] == 763 and len(value['negative_controls']) == 6
                         and all(x['status'] == 'PASS_REJECTED' for x in value['negative_controls']), 'rank7 guard controls')
                else:
                    need(len(value['controls']) == 3 and all(x['rejected'] for x in value['controls'].values()),
                         'cap invoice/source controls')
            need(got_controls == expected_controls and len(controls) == len(expected_controls), 'exact eight control tasks')
            inventory = {seed: {pid: {} for pid in PROVIDERS} for seed in SEEDS}
            seen = defaultdict(list)
            coverage = {}
            for entry in info['phases']['screen']['saved'].values():
                spec, value = entry['spec'], entry['item']['result']
                need(value['provider'] == spec['provider'] and value['seed'] == spec['seed']
                     and value['group'] == spec['group'] and value['block'] == spec['block'], 'screen checkpoint identity')
                need(value['complete'] is True and value['status'] in ('NULL_BOUNDED_GRAMMAR', 'NOMINEES'), 'complete screen block')
                need(0 < len(value['planes']) <= 16 and value['pair_cap'] == 8 and value['pivot_cap'] == 16, 'registered block and choice caps')
                meta = value['spaces']
                need(meta['retained_basis_pairs'] == min(8, meta['nonzero_basis_pairs']) and
                     meta['truncated_basis_pairs'] == max(0, meta['nonzero_basis_pairs'] - 8), 'basis cap/truncation bookkeeping')
                need(len(value['retained_pivots']) == min(16, value['eligible_pivots']) and
                     value['truncated_pivots_per_pair'] == max(0, value['eligible_pivots'] - 16), 'pivot cap/truncation bookkeeping')
                expected = len(value['planes']) * meta['retained_basis_pairs'] * len(value['retained_pivots'])
                need(value['attempted_constructions'] == value['expected_constructions'] == expected and
                     value['unattempted_constructions'] == 0, 'all bounded candidates accounted')
                need(expected == len(value['witnesses']) + sum(value['rejections'].values()), 'candidate outcome partition')
                key = (spec['seed'], spec['provider'], value['mode'])
                seen[key].extend(tuple(p) for p in value['planes'])
                for candidate in value['witnesses']:
                    addr = address(candidate)
                    target = inventory[spec['seed']][spec['provider']]
                    need(addr not in target and tuple(candidate['plane']) in expected_planes,
                         'unique registered witness address')
                    need(candidate['helper'] != 408 and candidate['private_buffers'] == 83 and
                         candidate['declared_entrance_rank'] == 0 and candidate['declared_endpoint_rank'] == 9
                         and candidate['new_endpoint_rank'] == 7, 'rank7 witness scope')
                    target[addr] = candidate
            for seed in SEEDS:
                for pid in PROVIDERS:
                    for mode in MODES:
                        key = (seed, pid, mode)
                        need(len(seen[key]) == 763 and set(seen[key]) == expected_planes,
                             'all763 distinct registered planes exactly once: ' + str(key))
                        coverage['%s:%s:%s' % key] = dict(frames=763, unique_frames=763)
            for pid in PROVIDERS:
                need(inventory[SEEDS[0]][pid] == inventory[SEEDS[1]][pid], 'exact second-seed candidate inventory: ' + pid)
            stored = read(info['path'] / 'COVERAGE.json')
            self.file(info['path'] / 'COVERAGE.json')
            need(set(stored) == set(coverage), 'stored coverage key inventory')
            for key, value in stored.items():
                need(value['frames'] == value['unique_frames'] == 763, 'stored coverage frame counts')
            info['inventories'] = inventory
            out[attempt] = dict(status='PASS', controls=len(controls), coverage=coverage,
                                nominees_by_provider={pid: len(inventory[SEEDS[0]][pid]) for pid in PROVIDERS})
        return dict(status='PASS', attempts=out)

    def cap_validation(self):
        out = {}
        for attempt, info in sorted(self.attempts.items()):
            if not info['complete']:
                out[attempt] = dict(status='INCOMPLETE_PRESERVED')
                continue
            inv = info['inventories'][SEEDS[0]]
            common = set(inv['extra']) & set(inv['gauge44'])
            matched = read(info['path'] / 'MATCHED-LEDGERS.json.gz')
            self.file(info['path'] / 'MATCHED-LEDGERS.json.gz')
            counts, groups = matched['counts'], matched['ledger_groups']
            need(counts['matched_addresses'] == len(common) and
                 counts['nominees_by_provider'] == {pid: len(inv[pid]) for pid in PROVIDERS} and
                 counts['unmatched_by_provider'] == {pid: len(set(inv[pid]) - common) for pid in PROVIDERS},
                 'matched and unmatched provider counts')
            covered = []
            for lid, group in groups.items():
                need(sha(canonical(group['ledger'])) == lid, 'complete ledger cache key')
                keys = {address(x) for x in group['addresses'].values()}
                need(len(keys) == 1 and set(group['addresses']) == set(PROVIDERS), 'matched both-provider cache representative')
                for member in group['members']:
                    key = (member[0], tuple(member[1]), member[2], tuple(member[3]))
                    need(key in common, 'only common candidate retained in ledger cache')
                    expected = {pid: dict(helper=key[0], local_profile=inv[pid][key]['local_profile'],
                                width_inventory=inv[pid][key]['width_inventory'], private_buffers=inv[pid][key]['private_buffers'])
                                for pid in PROVIDERS}
                    need(expected == group['ledger'], 'complete profile/inventory/buffer ledger equality')
                    covered.append(key)
            need(len(covered) == len(common) and set(covered) == common, 'all matched addresses mapped exactly once')
            favorable, caps = [], {}
            phase = info['phases'].get('cap', {'saved': {}})
            for entry in phase['saved'].values():
                spec, value = entry['spec'], entry['item']['result']
                lid, seed = spec['ledger_id'], spec['seed']
                need(lid in groups and (lid, seed) not in caps, 'unique cap ledger/seed record')
                need(value['ledger_id'] == lid and value['identity'] == spec['identity'], 'cap task identity')
                need(value['physical_stock']['private_zero_buffers'] == 83 and
                     value['physical_stock']['total'] == 66805 and value['solver_calls'] == 0, 'cap stock and no solver')
                need([x['rank_cap'] for x in value['caps']] == [48, 51], 'primary and secondary caps')
                for report in value['caps']:
                    low, high = Q(report['target_moment_lower']), Q(report['target_moment_upper'])
                    need(low <= high, 'ordered exact saved moment interval')
                    expected = ('OPTIMISTIC_CAP_ABOVE_TARGET' if high < 1 else
                                'NO_CAP_HEADROOM_AT_TARGET' if low >= 1 else 'UNRESOLVED_INTERVAL')
                    need(report['classification'] == expected, 'saved cap decision arithmetic')
                caps[lid, seed] = value
            need(set(caps) == {(lid, seed) for lid in groups for seed in SEEDS}, 'every matched ledger screened twice')
            for lid, group in groups.items():
                one, two = (caps[lid, seed] for seed in SEEDS)
                need(one['caps'] == two['caps'] and one['status'] == two['status'], 'exact second-seed cap agreement')
                if one['status'] == 'PASS_OPTIMISTIC_LOCAL_COST_SCREEN':
                    for member in group['members']:
                        key = (member[0], tuple(member[1]), member[2], tuple(member[3]))
                        favorable.append((Q(one['caps'][0]['target_moment_upper']), key, lid))
                else:
                    need(one['status'] == 'NULL_OPTIMISTIC_CAP_NO_HEADROOM', 'complete cap decision classification')
            favorable.sort()
            retained = favorable[:16]
            validations = info['phases'].get('validation', {'saved': {}})['saved']
            need(len(validations) == 2 * len(retained), 'first16 favorable nominees validated twice')
            validated = {}
            for entry in validations.values():
                spec, value = entry['spec'], entry['item']['result']
                member = spec['identity']
                key = (member[0], tuple(member[1]), member[2], tuple(member[3]))
                need((key, spec['seed']) not in validated and key in {x[1] for x in retained}, 'retained validation address')
                need(value['status'] == 'PASS_LOCAL_RANK7_AND_OPTIMISTIC_CAP' and
                     value['complete_allocation'] == value['fresh_native_admission'] == value['full_physical_supplier_outer'] == 'UNRUN_REQUIRED',
                     'local success does not claim native or full admission')
                hashes = {}
                for pid in PROVIDERS:
                    saved = value['providers'][pid]
                    self.local_references(saved)
                    audit = saved['local_admission']['audit']
                    need(audit['checked_columns'] == 632 and audit['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
                         'fresh full-input candidate semantic audit')
                    raw = read(self.resolve(saved['word']))
                    semantic = sha(json.dumps(raw, sort_keys=True, separators=(',', ':')).encode())
                    need(semantic == info['inventories'][spec['seed']][pid][key]['semantic_sha256'], 'candidate artifact binds enumerated word')
                    hashes[pid] = saved['word']['sha256']
                validated[key, spec['seed']] = hashes
            for _, key, _ in retained:
                need(validated[key, SEEDS[0]] == validated[key, SEEDS[1]], 'byte-identical candidate words across seeds')
            for seed in SEEDS:
                result = self.receipts[attempt, seed]
                stat = result['statistics']
                need(stat['counts'] == counts and stat['matched_unique_cost_ledgers'] == len(groups)
                     and stat['favorable_addresses'] == len(favorable) and stat['retained_addresses'] == len(retained)
                     and stat['unretained_favorable'] == len(favorable)-len(retained), 'receipt candidate totals')
                need(result['status'] == ('EXPLORATORY' if favorable else 'NULL'), 'no false NULL with unresolved headroom')
            out[attempt] = dict(status='PASS', matched=len(common), cost_ledgers=len(groups), favorable=len(favorable),
                                retained=len(retained), unmatched=counts['unmatched_by_provider'])
        return dict(status='PASS', attempts=out)

    def inventory_cap_certificate(self, value):
        """Check saved rational linear certificates; never evaluate a power/root."""
        caps, widths, supplies = (8, 16, 32, 48), (4, 5, 7, 8, 9), (672, 448, 448, 448)
        patterns = []
        # Cartesian coverage is independent of the producer's recursive enumerator.
        for capacity in caps:
            for counts in product(*(range(capacity//w + 1) for w in widths)):
                used = sum(w*n for w, n in zip(widths, counts))
                if used <= capacity:
                    column = tuple(int(c == capacity) for c in caps) + counts
                    patterns.append((capacity, counts, capacity-used, column))
        need(len(patterns) == value['pattern_count'] == 1163 and
             sha(canonical(encode(patterns))) == value['pattern_census_sha256'], 'complete saved1163 pattern census hash')
        source_basis = read(DATA / 'pr2930/certificates/RELAX-CAP.json')['basis_patterns']
        columns, remainders = [], []
        for item in source_basis:
            count = Counter(item['widths'])
            columns.append([int(c == item['capacity']) for c in caps] + [count[w] for w in widths])
            remainders.append(item['capacity']-sum(item['widths']))
        matrix = [[Q(x) for x in row] for row in zip(*columns)]
        reported_matrix = [[Q(x) for x in row] for row in value['basis_matrix']]
        inverse = [[Q(x) for x in row] for row in value['basis_inverse']]
        need(matrix == reported_matrix and len(inverse) == 9 and all(len(row) == 9 for row in inverse), 'exact declared9-by9 basis')
        for left, right in ((matrix, inverse), (inverse, matrix)):
            need(all(sum((left[i][k]*right[k][j] for k in range(9)), Q(0)) == int(i == j)
                     for i in range(9) for j in range(9)), 'both rational inverse identities')
        old_inventory = {4: 26, 5: 2, 7: 62, 8: 96, 9: 222}
        new_inventory = {4: 26, 5: 2, 7: 63, 8: 96, 9: 221}
        need({int(k): v for k, v in value['old_inventory_per_call'].items()} == old_inventory and
             {int(k): v for k, v in value['new_inventory_per_call'].items()} == new_inventory, 'exact9-to7 width inventory')
        for inv, counts in ((old_inventory, value['controls']['source_primal_counts']),
                            (new_inventory, value['new_basis_counts_per_replica'])):
            vector = list(map(Q, counts))
            rhs = list(map(Q, supplies)) + [Q(9*inv[w]) for w in widths]
            need(len(vector) == 9 and all(x >= 0 for x in vector) and
                 [sum((a*b for a, b in zip(row, vector)), Q(0)) for row in matrix] == rhs,
                 'nonnegative primal solution meets all nine constraints')
        dual = []
        for i in range(9):
            poly = defaultdict(Q)
            for j, rank in enumerate(remainders):
                if rank:
                    poly[rank] += inverse[j][i]
            dual.append({r: q for r, q in poly.items() if q})
        need(encode(dual) == value['dual_coefficient_rows'], 'dual derived from exact inverse transpose')
        reduced = []
        for capacity, counts, remainder, column in patterns:
            poly = defaultdict(Q)
            if remainder:
                poly[remainder] = Q(1)
            for a, multiplier in zip(column, dual):
                for rank, coefficient in multiplier.items():
                    poly[rank] -= a*coefficient
            reduced.append({r: q for r, q in poly.items() if q})
        need(sha(canonical(encode(reduced))) == value['reduced_cost_coefficient_sha256'], 'all reduced-cost coefficient hash')
        zero = [i for i, poly in enumerate(reduced) if not poly]
        need(value['coefficient_zero_reduced_costs'] == len(zero), 'exact coefficientwise zero count')
        dual_rows_checked = 0

        def check_dual(report, expected_exponent):
            nonlocal dual_rows_checked
            need(Q(report['exponent']) == Q(expected_exponent) and report['patterns'] == 1163,
                 'dual report endpoint and coverage')
            intervals = {int(r): tuple(map(Q, bounds)) for r, bounds in report['child_cost_intervals'].items()}
            need(set(intervals) == {r for poly in reduced for r in poly} and
                 all(len(bounds) == 2 and 0 < bounds[0] <= bounds[1] < 1 for bounds in intervals.values()),
                 'saved directed child-cost interval coverage')
            minimum = None
            for index, poly in enumerate(reduced):
                if not poly:
                    continue
                lower = sum((q*intervals[r][0 if q >= 0 else 1] for r, q in poly.items()), Q(0))
                need(lower > 0, 'all saved nonzero reduced-cost rational lower bounds strictly positive')
                if minimum is None or lower < minimum[0]:
                    minimum = lower, index
            need(report['status'] == 'PASS' and report['exact_zero_polynomial_indices'] == zero and
                 report['exact_zero_count'] == len(zero) and report['strict_positive_count'] == 1163-len(zero)
                 and not report['negative_patterns'] and not report['unresolved_patterns'], 'complete exact dual classification')
            need(Q(report['minimum_strict_margin']) == minimum[0] and report['minimum_strict_pattern'] == minimum[1],
                 'minimum strict margin and pattern agree with all1163 rows')
            dual_rows_checked += 1163
            return intervals

        controls = value['controls']
        need(controls['status'] == 'PASS' and len(controls['negative_controls']) == 4 and
             all(row['rejected'] for row in controls['negative_controls'].values()), 'four exact inventory-cap rejection controls')
        old_low, old_high = map(Q, controls['source_root_bracket'])
        need(Q(controls['source_lower_moment'][1]) < 896 < Q(controls['source_upper_moment'][0]), 'source bracket positive control')
        check_dual(controls['source_dual'], old_high)
        target = Q(self.protocol['target']['complex_lower'])
        need(Q(value['target']) == target, 'V3 exact competitive endpoint')
        target_intervals = check_dual(value['target_dual'], target)
        idle = defaultdict(Q)
        for rank, count in zip(remainders, value['new_basis_counts_per_replica']):
            if rank:
                idle[rank] += Q(count)
        need(encode(dict(idle)) == value['new_idle_per_replica'], 'new fractional idle profile')
        profiles = {}
        caps_by_id = value['profile_caps']
        need(len(caps_by_id) == 6, 'all six distinct local profiles priced')
        below = []
        for cap in caps_by_id:
            local = {int(r): Q(n) for r, n in cap['local_per_call'].items()}
            need(all(n.denominator == 1 for n in local.values()) and
                 sum(r*n for r, n in local.items()) == sum(w*n for w, n in new_inventory.items())+1856,
                 'complete local profile/width mass equality')
            full = {r: 9*n for r, n in local.items()}
            for rank, count in idle.items():
                full[rank] = full.get(rank, Q(0))+count
            need(encode(full) == cap['complete_fractional_profile_per_replica'] and
                 sum(r*n for r, n in full.items()) == 65088, 'full fractional profile and exact coverage mass')
            calculated = tuple(sum((n*target_intervals[r][j] for r, n in full.items()), Q(0)) for j in (0, 1))
            need(calculated == (Q(cap['target_moment_lower']), Q(cap['target_moment_upper'])), 'target moment from saved child intervals')
            low, high = Q(cap['cap_lower']), Q(cap['cap_upper'])
            need(0 < high-low <= Q(1, 10**20) and Q(cap['grid']) == Q(1, 10**20), 'exact1e-20 root grid bracket')
            need(Q(cap['lower_endpoint_moment'][1]) < 896 < Q(cap['upper_endpoint_moment'][0]), 'saved complete-profile root separation')
            upper_intervals = check_dual(cap['dual_at_upper'], high)
            calculated_upper = tuple(sum((n*upper_intervals[r][j] for r, n in full.items()), Q(0)) for j in (0, 1))
            need(calculated_upper == tuple(map(Q, cap['upper_endpoint_moment'])), 'upper root moment from saved child intervals')
            need(Q(cap['gap_below_target']) == target-high and
                 list(map(Q, cap['admitted_target_fraction_of_cap_interval'])) == [target/high, target/low], 'exact target gaps and ratios')
            flag = high < target
            need(cap['strictly_below_target'] is flag and cap['target_bound_certified'] is True and
                 cap['target_root_rejected'] is (calculated[0] > 896) and cap['status'] == 'PASS_EXACT_FIXED_INVENTORY_CAP',
                 'certified inventory-cap classification')
            below.append(flag and calculated[0] > 896)
            profile_id = sha(canonical(encode({r: int(n) for r, n in local.items()})))
            need(profile_id == cap['profile_id'] and profile_id not in profiles, 'unique saved profile ID')
            profiles[profile_id] = {str(r): int(n) for r, n in local.items()}
        matched = read(ROUND / FAMILY / 'v1/MATCHED-LEDGERS.json.gz')['ledger_groups']
        mapping = value['ledger_mapping']
        need(len(mapping) == 16 and {x['ledger_id'] for x in mapping} == set(matched), 'all sixteen source ledger mappings')
        members = []
        for row in mapping:
            source = matched[row['ledger_id']]
            need(row['members'] == source['members'], 'all ledger member addresses retained')
            for provider in PROVIDERS:
                need(source['ledger'][provider]['local_profile'] == profiles[row['profile_id']], 'both provider ledger mapped to the correct exact local profile')
            members.extend(row['members'])
        need(len(members) == len({sha(canonical(m)) for m in members}) == 48, 'all48 distinct matched addresses covered')
        need(value['complete_coverage'] is True and value['all_six_profiles_certified_below_target'] is all(below)
             and value['status'] == ('NULL' if all(below) else 'EXPLORATORY'), 'registered V3 scoped decision')
        return dict(patterns=1163, profiles=6, ledgers=16, matched_addresses=48,
                    reconstructed_dual_inequalities=dual_rows_checked,
                    all_caps_below_target=all(below), controls=4,
                    analytic_scope='Saved child-cost enclosures are source-bound outputs of the pinned interval engine; this audit independently recombines rational bounds and checks all linear certificates, but does not rerun logarithms, powers or root searches.')

    def inventory_cap_results(self):
        path = ROUND / VALIDATION / 'v1'
        summary = read(path / 'RUN.json')
        self.file(path / 'RUN.json')
        implementation = read(path / 'IMPLEMENTATION.json')
        self.file(path / 'IMPLEMENTATION.json', summary['implementation_sha256'])
        details = {}
        for seed in SEEDS:
            result_path = path / ('seed-'+str(seed)) / 'RESULT.json'
            value = read(result_path)
            self.file(result_path)
            need(REQUIRED <= set(value) and (value['experiment'], value['milestone'], value['seed']) ==
                 (VALIDATION, 'CONTINUATION-02/V3', seed), 'V3 RESULT schema and identity')
            need(value['preregistration_sha256'] == self.validation_preg_sha and
                 value['implementation_pins_sha256'] in self.implementation_pins, 'V3 frozen protocol and implementation pins')
            need(value['script_manifest_sha256'] == sha(canonical(value['script_sha256'])) and
                 implementation['script_sha256'] == value['script_sha256'], 'V3 exact frozen source map')
            need(implementation['preregistration_sha256'] == self.validation_preg_sha and
                 implementation['implementation_pins_sha256'] == value['implementation_pins_sha256'], 'V3 frozen implementation header')
            for source, digest in value['script_sha256'].items():
                need(digest in self.archives, 'V3 exact historical source archive: ' + source)
            attrs = {p['path']: p for p in value['source_attribution']}
            need(len(attrs) == len(value['source_attribution']) == 23 and
                 value['word_blob_ids'] == {k: p['git_blob'] for k, p in attrs.items()}, 'V3 complete attribution and word blobs')
            for name, pin in self.original_pins.items():
                need(name in attrs and all(attrs[name].get(k) == v for k, v in pin.items()), 'V3 original source attribution')
            self.local_references(value)
            task = read(self.resolve(value['pool_receipt']))
            self.reference(value['pool_receipt'])
            need(task['status'] == 'OK' and task['result'] == value['statistics'], 'V3 saved pool/result equality')
            need(value['status'] == value['decision']['verdict'] == value['statistics']['status'] == summary['status'] and
                 value['status'] in ('NULL', 'EXPLORATORY') and value['launch_failure'] is None and
                 value['scientific_decision_agreement'] is True, 'V3 completed scoped verdict')
            need(value['decision']['null_bar'] == self.validation_protocol['null_bar'] and
                 value['decision']['headroom_bar'] == self.validation_protocol['headroom_bar'], 'unchanged V3 decision bars')
            need(value['no_actual_allocation_or_native_claim'] is True and value['confirmation_required'] is True and
                 value['n_permutations'] == 0, 'inventory cap is not a realized supplier')
            need(0 <= value['peak_rss_bytes'] <= 4*1024**3 and value['cpu_seconds'] >= 0 and value['wall_seconds'] >= 0,
                 'V3 finite resource metrics')
            details[str(seed)] = self.inventory_cap_certificate(value['statistics'])
            self.v3_receipts[seed] = value
        stable = lambda x: {k: v for k, v in x.items() if k not in ('seed', 'cpu_seconds')}
        need(stable(self.v3_receipts[SEEDS[0]]['statistics']) == stable(self.v3_receipts[SEEDS[1]]['statistics']),
             'complete V3 scientific payload agreement across seeds')
        need(math.isclose(sum(x['cpu_seconds'] for x in self.v3_receipts.values()), summary['total_cpu_seconds'],
                          rel_tol=0, abs_tol=1e-6), 'V3 CPU assigned exactly once')
        return dict(status='PASS', result_count=2, seed_arithmetic=details,
                    measured_experiment_cpu_seconds=summary['total_cpu_seconds'])

    def resources(self):
        projections = []
        for path in sorted(ROUND.rglob('*MEMORY-PROJECTION.json')):
            value = read(path)
            self.file(path)
            need(value['allocated_cores'] == 128 and value['reserved_cores'] == 8 and
                 value['workers'] == min(120, math.floor(value['ram_gib']/4)) == 61, 'registered61-worker allocation')
            need(value['worker_rss_cap_gib'] == 4 and value['projected_per_worker_gib'] < 4 and
                 value['projected_peak_gib'] < value['ram_gib'], 'safe pre-launch memory projection')
            projections.append(dict(path=str(path.relative_to(PKG)), **value))
        need(projections, 'at least one recorded pool projection')
        cpu = sum(v['cpu_seconds'] for v in self.receipts.values()) + sum(v['cpu_seconds'] for v in self.v3_receipts.values())
        need(cpu <= 14400, 'registered round CPU budget')
        return dict(status='PASS', projections=projections, measured_experiment_cpu_seconds=cpu,
                    registered_family_cpu_budget_seconds=14400,
                    scope='Recorded pool/receipt resource accounting only; no jobs relaunched. Parent overhead is assigned once, to the first seed.')

    def preservation(self):
        command = ['git', 'ls-tree', '-rz', '--full-tree', BASE, '--', 'research/styles-r11/']
        raw = subprocess.run(command, cwd=ROOT, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        count, size = 0, 0
        for record in raw.split(b'\0'):
            if not record:
                continue
            info, name = record.split(b'\t', 1)
            mode, kind, digest = info.decode().split()
            need(kind == 'blob' and mode in ('100644', '100755'), 'ordinary original file tree')
            path = ROOT / name.decode()
            payload = path.read_bytes()
            need(blob(payload) == digest, 'prior frozen file changed: ' + name.decode())
            count += 1
            size += len(payload)
        need(count > 0, 'baseline preservation tree nonempty')
        return dict(status='PASS', baseline_commit=BASE, preserved_files=count, preserved_bytes=size,
                    scope='Every tracked research/styles-r11 file at the prior-round final commit, including original audits/exports and CONTINUATION-01, remains byte-identical.')

    def registry_handback(self):
        registry = read(ROUND / 'EXPERIMENTS.json')
        self.file(ROUND / 'EXPERIMENTS.json')
        self.local_references(registry)
        need(registry['status'] == 'COMPLETE_SCOPED_NULL', 'closed round status')
        rows = {row['id']: row for row in registry['experiments']}
        need(set(rows) == {'C4-BATCHED-CROSS-CALL', 'V2-BATCH-ADMISSION', FAMILY, VALIDATION}, 'exact four family registry')
        for family in ('C4-BATCHED-CROSS-CALL', 'V2-BATCH-ADMISSION'):
            row = rows[family]
            need(row['status'] == 'EXPLORATORY' and row['execution'] == 'UNRUN' and
                 not row['confirmed'] and row['cpu_seconds'] == 0 and not row.get('result_files'), 'retired unrun family remains distinct from NULL')
            need(not (ROUND / family).exists(), 'no fabricated retired-family run')
        row = rows[FAMILY]
        latest = max(self.attempts, key=lambda x: int(x[1:]))
        pair = [self.receipts[latest, seed] for seed in SEEDS]
        need(row['status'] == pair[0]['status'] == pair[1]['status'], 'registry selects latest two-seed verdict')
        expected = {'results/CONTINUATION-02/'+FAMILY+'/'+latest+'/seed-'+str(seed)+'/RESULT.json' for seed in SEEDS}
        need(set(row['result_files']) == expected, 'registry latest receipt paths')
        confirmed = row['status'] == 'NULL'
        need(row['confirmed'] is confirmed and registry['no_active_experiments'] is True,
             'registry closed with exact scientific confirmation')
        validation = rows[VALIDATION]
        need(all(validation['status'] == x['status'] for x in self.v3_receipts.values()) and
             validation['confirmed'] is (validation['status'] == 'NULL') and
             set(validation['result_files']) == {'results/CONTINUATION-02/'+VALIDATION+'/v1/seed-'+str(s)+'/RESULT.json' for s in SEEDS},
             'V3 registry result selection and confirmation')
        need(registry['lane_status']['constructive-word']['consecutive_confirmed_nulls'] == (1 if validation['status'] == 'NULL' else 0),
             'no false lane null from errors, unrun families or exploratory nominees')
        retirement = read(ROUND / 'C4-RETIREMENT.json')
        self.file(ROUND / 'C4-RETIREMENT.json')
        need(retirement['execution'] == 'UNRUN' and retirement['scientific_trials'] == 0 and
             retirement['lane_null_streak_unchanged'] is True, 'pre-execution retirement remains explicit')
        for name in ('TASK.json', 'OVERLAP.md', 'README.md', 'RESULTS.md', 'HANDBACK.md',
                     'PREDICTIONS.json', 'ROUND-DECISION.json', 'FINAL-CHECKPOINT-DECISION.json'):
            self.file(ROUND / name)
            if name.endswith('.json'):
                self.local_references(read(ROUND / name))
        validation_review = read(ROUND / 'VALIDATION-CERTIFICATE.json')
        self.file(ROUND / 'VALIDATION-CERTIFICATE.json')
        need(validation_review['status'] == 'PASS' and validation_review['review_kind'] == 'INTEGRITY_ONLY' and
             not validation_review['errors'] and all(v['status'] == 'PASS' for v in validation_review['sections'].values()),
             'independent saved-evidence review passed')
        self.local_references(validation_review)
        if (ROUND / 'CLAIM.json').exists():
            self.file(ROUND / 'CLAIM.json')
            self.local_references(read(ROUND / 'CLAIM.json'))
        return dict(status='PASS', latest_attempt=latest, G2_verdict=row['status'], V3_verdict=validation['status'], retired_unrun_families=2,
                    earlier_attempts_preserved=sorted(set(self.attempts)-{latest}), no_active_experiments=True)

    def inventory(self):
        count = 0
        for root in (ROUND, PKG / 'data/continuation-02', HERE):
            for path in sorted(root.rglob('*')):
                if path.is_file() and path != ROUND / 'FINAL-AUDIT.json':
                    self.file(path)
                    count += 1
        expected_results = {ROUND / FAMILY / attempt / ('seed-'+str(seed)) / 'RESULT.json'
                            for attempt, seed in self.receipts}
        expected_results |= {ROUND / VALIDATION / 'v1' / ('seed-'+str(seed)) / 'RESULT.json' for seed in self.v3_receipts}
        need(set(ROUND.rglob('RESULT.json')) == expected_results, 'every current-round RESULT accounted')
        return dict(status='PASS', files=count, final_audit_excluded_for_idempotence=True)

    def run(self):
        for name, method in [('source_data', self.source_data), ('protocol_sources', self.protocol_sources),
                             ('final_checkpoint', self.final_checkpoint),
                             ('results', self.results), ('task_records', self.task_records),
                             ('controls_and_coverage', self.controls_coverage), ('cap_and_validation', self.cap_validation),
                             ('inventory_cap_results', self.inventory_cap_results),
                             ('resources', self.resources), ('prior_preservation', self.preservation),
                             ('registry_and_handback', self.registry_handback), ('complete_inventory', self.inventory)]:
            self.section(name, method)
        size = sum(p.stat().st_size for p in RESULTS.rglob('*') if p.is_file() and p != ROUND / 'FINAL-AUDIT.json')
        if size >= LIMIT:
            self.errors.append(dict(section='storage', message='total results exceed200MiB'))
        return dict(schema_version=1, round='CONTINUATION-02', status='PASS' if not self.errors else 'ERROR',
                    reviewed_utc=datetime.now(timezone.utc).isoformat(), errors=self.errors, sections=self.sections,
                    checker=dict(path=str(Path(__file__).relative_to(ROOT)), sha256=sha(Path(__file__).read_bytes())),
                    checked_file_count=len(self.files), checked_files=dict(sorted(self.files.items())),
                    results_bytes_excluding_this_audit=size, result_limit_bytes=LIMIT,
                    original_audits_overwritten=False,
                    source_attribution=[dict(path=k, **v) for k, v in self.original_pins.items()],
                    scope='Integrity, source preservation and exact saved-record bookkeeping only. No scientific function, candidate search, native chain, root evaluator, solver or fetched code was executed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='Write the first successful immutable audit; never overwrite an existing audit')
    args = parser.parse_args()
    output = ROUND / 'FINAL-AUDIT.json'
    source = Path(__file__).read_bytes()
    archive = ROUND / 'SOURCES' / (sha(source)+'.py.gz')
    if args.write and not archive.exists():
        with archive.open('xb') as handle:
            handle.write(gzip.compress(source, mtime=0))
    if output.exists():
        need(archive.is_file() and sha(gzip.decompress(archive.read_bytes())) == sha(source),
             'final checker has exact archived source bytes')
    result = Review().run()
    raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    total = result['results_bytes_excluding_this_audit'] + (output.stat().st_size if output.exists() else len(raw))
    if total >= LIMIT:
        result['status'] = 'ERROR'
        result['errors'].append(dict(section='storage', message='audit exceeds total200MiB bound'))
        raw = (json.dumps(result, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    matched = None
    if output.exists():
        stable = lambda x: {k: v for k, v in x.items() if k != 'reviewed_utc'}
        matched = stable(read(output)) == stable(result)
        if not matched:
            result['status'] = 'ERROR'
            result['errors'].append(dict(section='immutable_audit', message='Stable payload differs; existing audit bytes were not overwritten'))
    elif args.write and result['status'] == 'PASS':
        with output.open('xb') as handle:
            handle.write(raw)
    print(json.dumps(dict(status=result['status'], errors=result['errors'], checked_file_count=result['checked_file_count'],
                          results_bytes=total, existing_audit_stable_match=matched,
                          output=str(output.relative_to(PKG)) if output.exists() else None), sort_keys=True))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
