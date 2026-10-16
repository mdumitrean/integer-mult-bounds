"""Integrity-only hand-back audit of CONTINUATION-01.

This reader imports no experiment, solver, mathematical validator or fetched
code. It checks stored schemas, byte hashes, exact bookkeeping and agreement.
The coordinator runs it after CLAIM, reports and registry completion. Its only
optional write is a new continuation audit file; the original r11 audit is
never replaced. Run with Python -I -B. No experimental result is recomputed.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
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
PKG = HERE.parent.parent
ROOT = PKG.parents[1]
RESULTS = PKG / 'results'
ROUND = RESULTS / 'CONTINUATION-01'
SEEDS = (11031, 29063)
ORIGINAL_COMMIT = '0358ac61e'
LIMIT_BYTES = 200 * 1024 ** 2
EXPECTED = {
    'C1-SAME-CALL-EXCHANGE/v1/seed-11031/RESULT.json': ('PASS', '79d5110669c1a094c9d5b9449fef0968be3daa223bbf8abf6d6a0b9dc932c30e'),
    'C1-SAME-CALL-EXCHANGE/v1/seed-29063/RESULT.json': ('PASS', 'e48622ee15d7021ce4580ac9acd9339ff8c69d1297af2dfda7b2618a000669e3'),
    'C2-LATEST-SAME-CALL/v1/seed-11031/RESULT.json': ('NULL', '3a6c3ecd01e87793917a69471d7cca3abcf8d7c529a0f9ec38fbc5c82541f0e5'),
    'C2-LATEST-SAME-CALL/v1/seed-29063/RESULT.json': ('NULL', '5a9d0f419151123400075cbed55b8bd4fe462e1942be6cfe57b643bc8da1e09d'),
    'C3-CROSS-CALL-EXCHANGE/v1/seed-11031/RESULT.json': ('PASS', '8a6a15c33854f0dfa123eef66cc12c14c32422784f4bb9f4c7cab52477f11612'),
    'C3-CROSS-CALL-EXCHANGE/v1/seed-29063/RESULT.json': ('PASS', 'f2d8aa5af97c5f8f3cf54d4a387291f62eb46e99f0362ed7c5b8447cd4ab4546'),
    'V1-FILL-ADMISSION/v1/seed-11031/RESULT.json': ('ERROR', '85349456c4c428f0bb885f9c3ff773b7805df680478bdd26914da4ad3df546b8'),
    'V1-FILL-ADMISSION/v1/seed-29063/RESULT.json': ('ERROR', 'aafe24eff7a8572983a7ab0967f6fcc0cb1ef7dc17e2ddef0930cb60322c9d40'),
    'V1-FILL-ADMISSION/v2/seed-11031/RESULT.json': ('PASS', 'aa37d0f8f1b55af7ed805363f94e22496b49e10cf21ffcf683308416fd3fc380'),
    'V1-FILL-ADMISSION/v2/seed-29063/RESULT.json': ('PASS', '5a58ebba440cce95272d4d4f27b18f5c63c3ce88f7c6c5c7799c546f6cf80ba2'),
}
PREREGS = {
    'C1-SAME-CALL-EXCHANGE': 'PREREGISTRATION.json',
    'C2-LATEST-SAME-CALL': 'C2/PREREGISTRATION.json',
    'C3-CROSS-CALL-EXCHANGE': 'C3/PREREGISTRATION.json',
    'V1-FILL-ADMISSION': 'V1/PREREGISTRATION.json',
    'G1-PAIRED-GRAMMAR': 'G1/PREREGISTRATION.json',
}
REQUIRED = {
    'schema_version', 'experiment', 'milestone', 'seed', 'recorded_utc', 'status',
    'n_permutations', 'statistics', 'source_attribution', 'word_blob_ids',
    'script_sha256', 'script_manifest_sha256', 'preregistration_sha256',
    'wall_seconds', 'cpu_seconds', 'peak_rss_bytes', 'null_summary', 'decision',
    'confirmation_required', 'scope',
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def json_data(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def refs(value):
    """Yield actual file-reference objects, never bare native-cache hash maps."""
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            yield value
        for child in value.values():
            yield from refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs(child)


class Review:
    def __init__(self):
        self.errors, self.sections, self.files, self.aliases = [], {}, {}, {}
        self.receipts, self.protocols, self.archives = {}, {}, {}
        self.original_pins = json_data(PKG / 'data/words/PINS.json')['files']

    def section(self, name, function):
        try:
            self.sections[name] = function()
        except Exception as exc:
            self.errors.append(dict(section=name, type=type(exc).__name__, message=str(exc)))
            self.sections[name] = dict(status='ERROR')

    def file(self, path, digest=None, size=None, blob=None, decoded=None):
        path = Path(path).resolve()
        need(path.is_relative_to(ROOT), 'reference outside repository: ' + str(path))
        raw = path.read_bytes()
        value = dict(path=str(path.relative_to(ROOT)), sha256=sha(raw), bytes=len(raw))
        if digest is not None:
            need(value['sha256'] == digest, 'SHA256 mismatch: ' + value['path'])
        if size is not None:
            need(len(raw) == size, 'byte length mismatch: ' + value['path'])
        if blob is not None:
            need(git_blob(raw) == blob, 'Git blob mismatch: ' + value['path'])
        if decoded is not None:
            payload = gzip.decompress(raw) if path.name.endswith('.gz') else raw
            need(sha(payload) == decoded, 'decoded SHA256 mismatch: ' + value['path'])
        self.files[value['path']] = value
        return value

    def resolve(self, ref):
        if ref.get('local_path'):
            return PKG / ref['local_path']
        path = ref['path']
        alias = self.aliases.get((path, ref.get('sha256')))
        if alias is not None:
            return alias
        if path.startswith('research/'):
            return ROOT / path
        if path.startswith(('results/', 'data/', 'pipeline/')) or path == 'EXPERIMENTS.json':
            return PKG / path
        if path in self.original_pins:
            return ROOT / path if '/' in path else PKG / 'data/words' / path
        raise ValueError('unresolved local artifact reference: ' + path)

    def reference(self, ref):
        return self.file(self.resolve(ref), ref.get('sha256'), ref.get('bytes'),
                         ref.get('git_blob'), ref.get('uncompressed_sha256', ref.get('decoded_sha256')))

    def local_references(self, value):
        count = 0
        for ref in refs(value):
            path = ref['path']
            # A cited historical executable specification or unavailable native
            # cache is attribution, not an acquired artifact. Acquired source
            # records have local_path or a manifest alias and are checked.
            if (ref.get('local_path') or path.startswith(('results/', 'research/styles-r11/'))
                    or (path, ref['sha256']) in self.aliases):
                self.reference(ref)
                count += 1
        return count

    def data_pins(self):
        for key, pin in self.original_pins.items():
            path = ROOT / key if '/' in key else PKG / 'data/words' / key
            self.file(path, pin['sha256'], pin['bytes'], pin['git_blob'])
            self.aliases[key, pin['sha256']] = path
        manifests = sorted((PKG / 'data/heldout').glob('*/DATA-MANIFEST.json'))
        manifests += [PKG / 'data/continuation-01/pr2917/MANIFEST.json',
                      PKG / 'data/continuation-01/references/MANIFEST.json']
        count = 0
        for path in manifests:
            self.file(path)
            value = json_data(path)
            entries = value if isinstance(value, list) else value['files']
            if isinstance(entries, dict):
                entries = list(entries.values())
            for pin in entries:
                local = PKG / pin['local_path']
                self.file(local, pin['sha256'], pin.get('bytes'), pin.get('git_blob'))
                for name in ('path', 'repository_path', 'local_path'):
                    if name in pin:
                        self.aliases[pin[name], pin['sha256']] = local
                count += 1
        return dict(status='PASS', original_words=len(self.original_pins), acquired_source_files=count,
                    manifests=[str(p.relative_to(PKG)) for p in manifests],
                    fetched_executable_text='Hashed as inert bytes only; never imported or executed')

    def protocol_records(self):
        for experiment, relative in PREREGS.items():
            path = ROUND / relative
            self.file(path)
            value = json_data(path)
            need(value['state'] == 'FROZEN' and tuple(value['seeds']) == SEEDS, 'frozen protocol/seeds: ' + experiment)
            need(experiment in value['experiments'], 'registered family: ' + experiment)
            self.protocols[experiment] = value
            if 'source_manifest_sha256' in value:
                self.file(PKG / 'data/continuation-01/pr2917/MANIFEST.json', value['source_manifest_sha256'])
            self.local_references(value)
        amendment = json_data(ROUND / 'V1/AMENDMENT-v2.json')
        self.file(ROUND / 'V1/AMENDMENT-v2.json')
        need(amendment['state'] == 'FROZEN', 'frozen V1 repair')
        need(amendment['preregistration_sha256'] == sha((ROUND / PREREGS['V1-FILL-ADMISSION']).read_bytes()), 'amendment binds V1 protocol')
        self.local_references(amendment)
        for relative, digest in amendment['implementation_sha256'].items():
            self.file(ROOT / relative, digest)
        clarification = json_data(ROUND / 'G1/IMPLEMENTATION-CLARIFICATION.json')
        self.file(ROUND / 'G1/IMPLEMENTATION-CLARIFICATION.json')
        need(clarification['state'] == 'FROZEN' and clarification['admission_retention_cap'] == 16, 'frozen G1 clarification')
        need(clarification['preregistration_sha256'] == sha((ROUND / PREREGS['G1-PAIRED-GRAMMAR']).read_bytes()), 'G1 clarification binding')
        for relative, digest in clarification['implementation_sha256'].items():
            self.file(ROOT / relative, digest)
        return dict(status='PASS', preregistrations=len(self.protocols), amendment='V1/AMENDMENT-v2.json',
                    unrun_implementation_clarification='G1/IMPLEMENTATION-CLARIFICATION.json')

    def source_archives(self):
        for path in sorted((ROUND / 'SOURCES').glob('*.py.gz')):
            digest = path.name[:-6]
            need(len(digest) == 64 and sha(gzip.decompress(path.read_bytes())) == digest, 'source archive content: ' + path.name)
            self.file(path)
            self.archives[digest] = str(path.relative_to(PKG))
        need(self.archives, 'continuation source archives missing')
        return dict(status='PASS', unique_archives=len(self.archives),
                    scope='All continuation archive bytes; original r11 historical missing archives remain in the unchanged original audit')

    def results(self):
        actual = {str(p.relative_to(ROUND)) for p in ROUND.rglob('RESULT.json')}
        need(actual == set(EXPECTED), 'exact ten immutable RESULT inventory')
        drift, required_sources = [], set()
        for relative, (status, digest) in EXPECTED.items():
            path = ROUND / relative
            self.file(path, digest)
            value = json_data(path)
            need(REQUIRED <= set(value), 'RESULT required schema: ' + relative)
            experiment, attempt, seedpart, _ = relative.split('/')
            seed = int(seedpart[5:])
            need((value['schema_version'], value['experiment'], value['milestone'], value['seed']) ==
                 (1, experiment, 'CONTINUATION-01', seed), 'RESULT identity: ' + relative)
            need(value['status'] == value['decision']['verdict'] == status, 'RESULT verdict: ' + relative)
            need(value['confirmation_required'] is True and value['n_permutations'] == 0, 'RESULT finite/confirmation schema')
            need(all(isinstance(value[k], (float, int)) and math.isfinite(value[k]) and value[k] >= 0
                     for k in ('cpu_seconds', 'wall_seconds', 'peak_rss_bytes')), 'finite resource metrics')
            need(value['peak_rss_bytes'] <= 6 * 1024 ** 3, 'recorded per-worker RSS cap')
            preg = ROUND / PREREGS[experiment]
            need(value['preregistration_sha256'] == sha(preg.read_bytes()), 'RESULT preregistration hash')
            need(value['decision']['pass_bar'] == self.protocols[experiment]['experiments'][experiment]['pass_bar'], 'unchanged pass bar')
            sources = value['script_sha256']
            need(sources and value['script_manifest_sha256'] == sha(json.dumps(sources, sort_keys=True).encode()), 'source manifest digest')
            implementation = path.parent.parent / 'IMPLEMENTATION.json'
            frozen = json_data(implementation)
            self.file(implementation)
            need(frozen['script_sha256'] == sources and frozen['preregistration_sha256'] == value['preregistration_sha256'], 'RESULT frozen implementation binding')
            for source, source_digest in sources.items():
                need(source_digest in self.archives, 'missing continuation source bytes: ' + source_digest)
                required_sources.add(source_digest)
                current = ROOT / source
                if not current.is_file() or sha(current.read_bytes()) != source_digest:
                    drift.append(dict(receipt=relative, source=source, frozen_sha256=source_digest,
                                      archive=self.archives[source_digest]))
            attrs = {p['path']: p for p in value['source_attribution']}
            need(len(attrs) == len(value['source_attribution']) == 23, 'complete original plus baseline attribution')
            for key, pin in self.original_pins.items():
                need(key in attrs and all(attrs[key].get(k) == v for k, v in pin.items()), 'original source credit retained: ' + key)
            need(value['word_blob_ids'] == {k: p['git_blob'] for k, p in attrs.items()}, 'complete word blob mapping')
            for pin in attrs.values():
                need(pin.get('author'), 'nonempty word author')
                self.reference(pin)
            self.local_references(value)
            if attempt == 'v2':
                need(value['amendment_sha256'] == frozen['amendment_sha256'] == sha((ROUND / 'V1/AMENDMENT-v2.json').read_bytes()), 'v2 amendment chain')
            if status == 'ERROR':
                need(experiment == 'V1-FILL-ADMISSION' and attempt == 'v1' and value['statistics'] == {}
                     and 'unchanged ordered physical ports' in value['task_error'], 'original schema-error receipt preserved')
            else:
                need(value.get('launch_failure') is None and not value.get('task_error') and not value.get('task_errors'), 'successful receipt has no error')
            self.receipts[experiment, attempt, seed] = value
        return dict(status='PASS', results=len(self.receipts), status_counts=dict(Counter(v['status'] for v in self.receipts.values())),
                    required_source_digests=len(required_sources), archived_historical_source_changes=drift,
                    recorded_cpu_seconds=sum(v['cpu_seconds'] for v in self.receipts.values()),
                    compute_scope='Sum of all ten preserved measured receipts, including failed V1 v1; no scientific functions rerun')

    def get(self, family, attempt, seed):
        return self.receipts[family, attempt, seed]['statistics']

    def same_call(self):
        out = {}
        for family in ('C1-SAME-CALL-EXCHANGE', 'C2-LATEST-SAME-CALL'):
            rows = [self.get(family, 'v1', seed) for seed in SEEDS]
            for value in rows:
                c = value['counts']
                need(value['complete'] and value['completed_calls'] == list(range(666)), 'all same-call source calls')
                need(c['all_pairs'] == value['expected_pairs'] == 666 * 408 * 407 // 2, 'same-call total pairs')
                need(c['equal_width_pairs'] + c['unequal_width_pairs'] == c['all_pairs'], 'width category accounting')
                need(c['infeasible_capacity_pairs'] + c['feasible_unequal_pairs'] == c['unequal_width_pairs'], 'capacity category accounting')
                need(c['nonimproving_feasible_pairs'] + c.get('strictly_improving_pairs', 0) == c['feasible_unequal_pairs'], 'feasible category accounting')
                need(value['controls']['status'] == 'PASS' and value['solver_calls'] == 0, 'same-call controls and solver count')
            need(rows[0]['counts'] == rows[1]['counts'], 'same-call seed counts agree')
            if family.startswith('C1'):
                need(rows[0]['candidate']['pair'] == rows[1]['candidate']['pair'], 'C1 selected pair agreement')
                for name in ('fill_artifact', 'profile_artifact'):
                    need(rows[0]['candidate'][name]['sha256'] == rows[1]['candidate'][name]['sha256'], 'C1 candidate bytes agree')
            else:
                need(all(v['candidate'] is None and v['counts'].get('strictly_improving_pairs', 0) == 0 for v in rows), 'C2 scoped NULL no witness')
            out[family] = dict(complete_calls=666, pairs_per_seed=rows[0]['expected_pairs'], counts_agree=True)
        return dict(status='PASS', families=out)

    def cross_call(self):
        family = 'C3-CROSS-CALL-EXCHANGE'
        totals, winners, per_seed = [], [], {}
        for seed in SEEDS:
            directory = ROUND / family / 'v1' / ('seed-' + str(seed))
            paths = sorted((directory / 'blocks').glob('block-*.json.gz'))
            need([p.name for p in paths] == ['block-%03d.json.gz' % i for i in range(84)], 'exact 84 C3 shards')
            counts, calls, roles, bests = Counter(), [], 0, []
            for index, path in enumerate(paths):
                self.file(path)
                item = json_data(path)
                value = item['result']
                need(item['status'] == 'OK' and value['status'] == 'COMPLETE' and value['complete'] is True, 'completed C3 shard')
                need(value['block'] == index and value['seed'] == seed and value['solver_calls'] == 0, 'C3 shard identity')
                expected_calls = list(range(index * 8, min(index * 8 + 8, 666)))
                need(sorted(value['source_calls']) == expected_calls, 'C3 shard exact source call interval')
                need(value['source_roles_expected'] == value['source_roles_processed'] == 408 * len(expected_calls), 'C3 source role count')
                need(item['peak_rss_bytes'] <= 6 * 1024 ** 3 and item['seconds'] <= 300, 'C3 shard resource bounds')
                need(all(type(n) is int and n >= 0 for n in value['counts'].values()), 'C3 integer category counts')
                counts.update(value['counts']); calls.extend(value['source_calls']); roles += value['source_roles_processed']
                if value['best'] is not None:
                    bests.append(value['best'])
            need(sorted(calls) == list(range(666)) and roles == 271728, 'C3 source coverage once')
            value = self.get(family, 'v1', seed)
            need(value['shards'] == 84 and value['source_calls'] == 666 and value['source_roles'] == roles, 'C3 receipt coverage')
            need(dict(counts) == value['counts'] and sum(counts.values()) == value['conceptual_pairs'] == 36862620480, 'C3 exact shard reduction')
            need(value['excluded_same_call_pairs'] == 55296648 and value['complete'], 'C3 excluded scope/complete')
            need(value['controls']['status'] == 'PASS', 'C3 registered controls')
            winner = min(bests, key=lambda b: (-b['square_gain'], b['canonical_pair']))
            candidate = value['candidate']
            need(winner['canonical_pair'] == candidate['pair'] and winner['square_gain'] == candidate['square_gain'], 'C3 canonical winner reduction')
            for ref in (candidate['fill_artifact'], candidate['profile_artifact']):
                self.reference(ref)
            need(json_data(self.resolve(candidate['profile_artifact'])) == candidate['complete_profile'], 'C3 emitted complete profile equality')
            totals.append(dict(counts)); winners.append({k:candidate[k] for k in ('pair','square_gain','complete_profile','complete_profile_delta')})
            per_seed[str(seed)] = dict(shards=84, calls=666, roles=roles, conceptual_pairs=sum(counts.values()), counts=dict(counts))
        need(totals[0] == totals[1] and winners[0] == winners[1], 'C3 second seed counts/winner agreement')
        candidates = [self.get(family, 'v1', s)['candidate'] for s in SEEDS]
        need(all(candidates[0][k]['sha256'] == candidates[1][k]['sha256'] for k in ('fill_artifact','profile_artifact')), 'C3 both candidate artifacts agree')
        run = json_data(ROUND / family / 'v1/RUN.json')
        need(run['completed_by_phase'] == {'blocks':168,'controls':2,'finish':2} and run['confirmed'] is True, 'C3 whole-run phase accounting')
        return dict(status='PASS', shards=168, by_seed=per_seed, canonical_winner=winners[0])

    def validation(self):
        family = 'V1-FILL-ADMISSION'
        old = [self.receipts[family, 'v1', s] for s in SEEDS]
        new = [self.get(family, 'v2', s) for s in SEEDS]
        need(all(v['status'] == 'ERROR' for v in old), 'failed V1 attempt retained')
        selected = self.get('C3-CROSS-CALL-EXCHANGE', 'v1', SEEDS[0])['candidate']
        for value in new:
            need(value['status'] == value['controls']['status'] == 'PASS', 'V1 current validation and controls')
            need(value['candidate']['sha256'] == selected['fill_artifact']['sha256'], 'V1 validates selected C3 bytes')
            admission = value['admission']
            need(admission['candidate_profile'] == selected['complete_profile'], 'V1 complete profile binds C3')
            need(admission['root_separation']['status'] == 'PASS' and
                 admission['endpoint_admission']['status'] == 'PASS_EXACT_RATIONAL_ROOT_BRACKET', 'stored exact root decisions')
            need(value['outer']['status'] == 'PASS_CONDITIONAL_OUTER_ARITHMETIC', 'stored conditional outer decision')
            need(value['headline']['conditional'] is True and value['fresh_native_replay'] is False, 'conditional scope and prior-native reuse retained')
            need(Fraction(value['headline']['kappa']) - Fraction(value['outer']['predecessor_kappa']) ==
                 Fraction(value['headline']['improvement']) > 0, 'exact stored headline difference')
            need(Fraction(value['headline']['kappa_decimal']) == Fraction(value['headline']['kappa']), 'decimal/rational headline agreement')
            need(value['inherited_obligations']['status'] == 'CONDITIONAL_INHERITED' and value['inherited_obligations']['obligations'], 'inherited obligations explicit')
            need(value['solver_calls'] == 0 and value['n_permutations'] == 0, 'finite validation protocol')
        for key in ('headline','candidate','inherited_obligations'):
            need(new[0][key] == new[1][key], 'V1 second-seed agreement: ' + key)
        for key in ('candidate_profile','complete_profile_delta','endpoint_admission','root_separation'):
            need(new[0]['admission'][key] == new[1]['admission'][key], 'V1 exact certificates agree: ' + key)
        releases = []
        for attempt, status in [('v1','ERROR'),('v2','PASS')]:
            path = ROUND / family / attempt / 'RELEASE-RECEIPT.json'
            self.file(path); release = json_data(path)
            need(release['status'] == status, 'release attempt status')
            self.local_references(release)
            self.file(path.parent/'IMPLEMENTATION.json', release['source_implementation_sha256'])
            need({ref['path'] for ref in release['result_files']} ==
                 {'results/CONTINUATION-01/'+family+'/'+attempt+'/seed-'+str(s)+'/RESULT.json' for s in SEEDS}, 'release exact two seed receipts')
            releases.append(release)
        need(releases[1]['fresh_native_replay'] is False, 'release does not claim fresh native replay')
        return dict(status='PASS', prior_attempt='v1 ERROR preserved', current_attempt='v2 PASS both seeds',
                    headline=new[0]['headline'], fresh_native_replay=False,
                    inherited_obligations=new[0]['inherited_obligations'],
                    scope='Stored certificate and arithmetic consistency only; no scientific computation rerun')

    def resource_records(self):
        paths = sorted(ROUND.rglob('*MEMORY-PROJECTION*.json'))
        need(len(paths) == 7, 'seven executed-phase memory projections')
        records = []
        for path in paths:
            self.file(path); value = json_data(path)
            need(value['workers'] == 61 == min(120, int(value['ram_gib']//4)), 'registered worker formula')
            need(value['allocated_cores'] == 128 and value['reserved_cores'] == 8 and value['workers'] <= 120, 'eight cores free')
            need(value['worker_rss_cap_gib'] == 6 and value['projected_per_worker_gib'] <= 6, 'fill worker memory projection')
            need(value['projected_peak_gib'] <= value['ram_gib'], 'projected peak fits RAM')
            records.append(dict(path=str(path.relative_to(PKG)), **value))
        cpu_by_family = Counter()
        for (family, _, _), value in self.receipts.items():
            cpu_by_family[family] += value['cpu_seconds']
        for family, seconds in cpu_by_family.items():
            need(seconds <= self.protocols[family]['resources']['cpu_budget_seconds_family'], 'family CPU cap includes all attempts')
        return dict(status='PASS', memory_projections=records, cpu_seconds_by_family=dict(cpu_by_family),
                    recorded_cpu_seconds=sum(cpu_by_family.values()),
                    scope='Checks saved projections and measured receipt RSS/CPU; cannot retrospectively measure unrecorded processes or concurrency')

    def original_preservation(self):
        commit = subprocess.check_output(['git','rev-parse',ORIGINAL_COMMIT+'^{commit}'], cwd=ROOT, text=True).strip()
        raw = subprocess.check_output(['git','ls-tree','-rz',commit,'--','research/styles-r11'], cwd=ROOT)
        matched, category = [], Counter()
        for entry in raw.split(b'\0'):
            if not entry:
                continue
            header, name = entry.split(b'\t', 1)
            mode, kind, blob = header.decode().split()
            name = name.decode()
            need(kind == 'blob' and mode in ('100644','100755'), 'ordinary original tracked file')
            value = self.file(ROOT/name, blob=blob)
            matched.append((name,blob,value['sha256']))
            if '/results/LANGUAGE/' in name:
                category['language_files'] += 1
            if '/results/SOURCES/' in name:
                category['source_archives'] += 1
        need(matched, 'original Git checkpoint available')
        index = json_data(RESULTS/'LANGUAGE/INDEX.json')
        need(index['word_count'] == 21 and index['files_per_word'] == 4 and len(index['words']) == 21, 'original language export dimensions')
        exported = 0
        for word in index['words']:
            need(len(word['files']) == 4, 'four original exports per word')
            for ref in word['files'].values():
                self.reference(ref); exported += 1
        for ref in index['inputs'].values():
            self.reference(ref)
        original = json_data(RESULTS/'FINAL-AUDIT.json')
        need(original['status'] == 'PASS' and original['result_count'] == 62, 'unchanged original r11 audit')
        return dict(status='PASS', original_commit=commit, tracked_files_checked=len(matched),
                    tracked_inventory_sha256=sha(json.dumps(matched,separators=(',',':')).encode()),
                    language_exports=exported, category_counts=dict(category),
                    original_audit=self.files[str((RESULTS/'FINAL-AUDIT.json').relative_to(ROOT))],
                    historical_source_archive_status=original['historical_source_archive_status'],
                    historical_missing_archives=len(original['missing_source_archives']),
                    scope='Original files match their pre-continuation Git blobs; historical missing source bytes are not retroactively repaired or concealed')

    def registry_and_handback(self):
        path = ROUND/'EXPERIMENTS.json'
        self.file(path); registry = json_data(path)
        entries = {v['id']:v for v in registry['experiments']}
        need(set(entries) == set(PREREGS), 'complete five-family continuation registry')
        self.reference(registry['original_registry'])
        for family in PREREGS:
            value = entries[family]
            need(value['preregistration'] == 'results/CONTINUATION-01/'+PREREGS[family], 'registry protocol path')
            if family == 'G1-PAIRED-GRAMMAR':
                need(value['status'] == 'EXPLORATORY' and value['execution'] == 'UNRUN', 'G1 explicitly unrun exploratory')
                reason = value.get('reason', value.get('stop_reason',''))
                need('objective' in reason.lower() and 'achiev' in reason.lower(), 'G1 reason: alternative-route objective achieved')
                need(not value.get('result_files') and not (ROUND/family).exists(), 'G1 no fabricated experiment receipts')
                continue
            attempt = 'v2' if family == 'V1-FILL-ADMISSION' else 'v1'
            rows = [self.receipts[family,attempt,s] for s in SEEDS]
            need(value['status'] == rows[0]['status'] == rows[1]['status'] and value['confirmed'] is True, 'confirmed registry verdict')
            expected = {'results/CONTINUATION-01/'+family+'/'+attempt+'/seed-'+str(s)+'/RESULT.json' for s in SEEDS}
            need(set(value['result_files']) == expected, 'registry current receipt selection')
            if family == 'V1-FILL-ADMISSION':
                history = value['attempt_history']
                need(len(history) == 1 and history[0]['attempt'] == 'v1' and history[0]['status'] == 'ERROR', 'failed attempt history')
                self.file(PKG/history[0]['release_receipt'], history[0]['release_sha256'])
        claim_path, report_path = ROUND/'CLAIM.json', ROUND/'RESULTS.md'
        for name in ('CLAIM.json','RESULTS.md','HANDBACK.md','PREDICTIONS.json'):
            self.file(ROUND/name)
        predictions = json_data(ROUND/'PREDICTIONS.json')
        self.local_references(predictions)
        if (ROUND/'README.md').exists():
            self.file(ROUND/'README.md')
        claim = json_data(claim_path)
        self.local_references(claim)
        headline = self.get('V1-FILL-ADMISSION','v2',SEEDS[0])['headline']
        # Support the final report's flat or nested headline schema, but require
        # an explicit rational/decimal value and conditional/reuse disclosure.
        declared = claim.get('headline', claim)
        kappa = declared.get('kappa', declared.get('kappa_decimal'))
        need(kappa is not None and Fraction(kappa) == Fraction(headline['kappa']), 'CLAIM exact released kappa')
        text = json.dumps(claim,sort_keys=True).lower()
        need('conditional' in text and 'inherit' in text and 'native' in text, 'CLAIM explicit conditional and native provenance scope')
        candidate = self.get('C3-CROSS-CALL-EXCHANGE','v1',SEEDS[0])['candidate']['fill_artifact']
        need(candidate['sha256'] in text, 'CLAIM binds selected candidate SHA256')
        report = report_path.read_text().lower()
        need('g1' in report and 'unrun' in report and 'conditional' in report, 'report records G1 unrun and conditional scope')
        need(registry.get('no_active_experiments') is True, 'continuation registry closed')
        return dict(status='PASS', registry_families=len(entries), G1=dict(status='EXPLORATORY',execution='UNRUN',reason=entries['G1-PAIRED-GRAMMAR'].get('reason',entries['G1-PAIRED-GRAMMAR'].get('stop_reason'))),
                    handback_files={name:self.files[str((ROUND/name).relative_to(ROOT))]
                                    for name in ('CLAIM.json','RESULTS.md','HANDBACK.md','PREDICTIONS.json')})

    def continuation_inventory(self):
        # Hash reviews, checkpoint/source metadata and every auxiliary output as
        # well as explicitly referenced artifacts. The new audit excludes itself
        # so repeated verification has an identical stable payload.
        count = 0
        for path in sorted(ROUND.rglob('*')):
            if path.is_file() and path != ROUND/'FINAL-AUDIT.json':
                self.file(path); count += 1
        artifacts = sorted(list(ROUND.rglob('FILL.json.gz')) + list(ROUND.rglob('PROFILE.json')))
        need(len(artifacts) == 8, 'all four candidate fill/profile pairs retained')
        return dict(status='PASS', hashed_files=count, candidate_artifact_files=len(artifacts))

    def run(self):
        for name, method in [('data_pins',self.data_pins),('protocols',self.protocol_records),
                             ('source_archives',self.source_archives),('results',self.results),
                             ('same_call',self.same_call),('cross_call',self.cross_call),
                             ('validation',self.validation),('resources',self.resource_records),
                             ('original_preservation',self.original_preservation),
                             ('registry_and_handback',self.registry_and_handback),
                             ('continuation_inventory',self.continuation_inventory)]:
            self.section(name,method)
        size = sum(p.stat().st_size for p in RESULTS.rglob('*')
                   if p.is_file() and p != ROUND/'FINAL-AUDIT.json')
        if size >= LIMIT_BYTES:
            self.errors.append(dict(section='storage',message='results tree is not below 200 MiB'))
        return dict(schema_version=1,status='PASS' if not self.errors else 'ERROR',
                    round='CONTINUATION-01',reviewed_utc=datetime.now(timezone.utc).isoformat(),
                    checker=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__).read_bytes())),
                    errors=self.errors,sections=self.sections,checked_file_count=len(self.files),
                    checked_files=dict(sorted(self.files.items())),result_bytes_excluding_this_audit=size,
                    result_limit_bytes=LIMIT_BYTES,original_audit_overwritten=False,
                    source_attribution=[dict(path=k,**v) for k,v in self.original_pins.items()],
                    scientific_scope='Integrity and saved-certificate consistency only. No experiment, candidate census, native replay, solver, moment/root evaluator, or fetched code executed. The finite improvement retains its stated inherited conditions.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',help='Write the first immutable audit, or verify the existing audit without replacing it')
    args = parser.parse_args()
    output = ROUND/'FINAL-AUDIT.json'
    source = Path(__file__).read_bytes()
    archive = ROUND/'SOURCES'/(sha(source)+'.py.gz')
    if args.write and not archive.exists():
        with archive.open('xb') as handle:
            handle.write(gzip.compress(source,mtime=0))
    if output.exists():
        need(archive.is_file() and sha(gzip.decompress(archive.read_bytes())) == sha(source),
             'the final checker source must have its exact immutable byte archive')
    result = Review().run()
    raw = (json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    audit_bytes = output.stat().st_size if output.exists() else (len(raw) if args.write else 0)
    if result['result_bytes_excluding_this_audit'] + audit_bytes >= LIMIT_BYTES:
        result['errors'].append(dict(section='storage',message='audit would exceed 200 MiB total results'))
        result['status'] = 'ERROR'
        raw = (json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    matched = None
    if output.exists():
        saved = json_data(output)
        stable = lambda value:{k:v for k,v in value.items() if k != 'reviewed_utc'}
        matched = stable(saved) == stable(result)
        if not matched:
            result['status'] = 'ERROR'
            result['errors'].append(dict(section='immutable_audit',message='Current stable audit differs from preserved FINAL-AUDIT.json; no bytes were overwritten'))
    elif args.write:
        with output.open('xb') as handle:
            handle.write(raw)
    print(json.dumps(dict(status=result['status'],errors=result['errors'],
                         checked_file_count=result['checked_file_count'],
                         result_bytes=result['result_bytes_excluding_this_audit']+audit_bytes,
                         existing_audit_stable_match=matched,
                         output=str(output.relative_to(PKG)) if output.exists() else None),sort_keys=True))
    return 0 if result['status']=='PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
