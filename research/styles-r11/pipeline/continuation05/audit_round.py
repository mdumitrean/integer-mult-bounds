"""Audit saved CONTINUATION-05 bytes and receipts; never import scientific code.

Run only after the coordinator closes the registry. ``--write`` creates the
immutable AUDIT.json once; repeating it verifies the same stable audit payload.
Neither this program nor its imports execute any fetched source or experiment.
"""
from collections import Counter
from datetime import datetime, timezone
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-05'
BASE = '394748784ff4ddc6a281ef8aaf2951de4e5b20e9'
FAMILIES = (('R2', 'R2-B-RESTORE'),)
ACQUISITION_SHA = 'e5ad48ac05e897dcc2e073d29be451cfd1493ba3077e7e2de0f9460aa11a7d71'
MANIFEST_SHA = '124bd80e6253256b716716abcde518fec172e6cd855377295875a0fc8dd96db2'
EXECUTION_FIELDS = {'seed', 'cpu_seconds', 'wall_seconds', 'elapsed_seconds',
                    'seconds', 'recorded_utc', 'output_dir', 'schedule',
                    'delivered_payloads'}


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def scientific(value):
    """Compare all saved science, normalizing only execution data/output paths.

    Candidate bytes remain compared through their SHA256 and byte count. The
    independently hash-checked paths differ between seed output directories.
    """
    if isinstance(value, list):
        return [scientific(v) for v in value]
    if isinstance(value, dict):
        ignored = set(EXECUTION_FIELDS)
        if (isinstance(value.get('path'), str) and 'sha256' in value and
                value['path'].startswith('results/CONTINUATION-05/')):
            ignored.add('path')
        return {k: scientific(v) for k, v in value.items() if k not in ignored}
    return value


def reference(ref):
    path = (PKG / ref['path']).resolve()
    need(path.is_relative_to(PKG), 'artifact confinement')
    raw = path.read_bytes()
    need(sha(raw) == ref['sha256'], 'artifact hash: ' + ref['path'])
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'artifact byte count: ' + ref['path'])
    return path


def artifact_refs(value):
    """Validate named current-round outputs without interpreting their science."""
    found = set()
    if isinstance(value, dict):
        if (isinstance(value.get('path'), str) and 'sha256' in value and
                value['path'].startswith('results/CONTINUATION-05/')):
            path = reference(value)
            found.add(str(path.relative_to(PKG)))
        for child in value.values():
            found.update(artifact_refs(child))
    elif isinstance(value, list):
        for child in value:
            found.update(artifact_refs(child))
    return found


def audit_family(label, experiment, row, original, task_card):
    need(row['execution'] == 'COMPLETED', 'family execution must be terminal')
    run = ROUND / experiment / 'v1'
    meta = read(run / 'RUN.json')
    protocol_path = ROUND / label / 'PREREGISTRATION.json'
    protocol, implementation = read(protocol_path), read(run / 'IMPLEMENTATION.json')
    preg_sha = sha(protocol_path.read_bytes())
    need(preg_sha == row['preregistration_sha256'] == implementation['preregistration_sha256'],
         'frozen registration binding')
    need(datetime.fromisoformat(protocol['registered_utc']) <=
         datetime.fromisoformat(implementation['frozen_utc']), 'registration precedes preparation')
    need(meta['source_implementation_sha256'] == sha((run / 'IMPLEMENTATION.json').read_bytes()),
         'run implementation binding')
    need(implementation.get('parent_load_once') is True, 'once-only parent preparation recorded')
    frozen_path = ROUND / label / 'IMPLEMENTATION-PINS-v1.json'
    frozen = read(frozen_path)
    need(sha(frozen_path.read_bytes()) == implementation['implementation_pins_sha256'],
         'pre-execution source-pin binding')
    need(datetime.fromisoformat(frozen['recorded_utc']) <=
         datetime.fromisoformat(implementation['frozen_utc']), 'source freeze precedes execution')
    archives, archive_only = set(), []
    for name, expected in implementation['script_sha256'].items():
        need(frozen['sha256'].get(name) == expected, 'executed source was prepinned: ' + name)
        archive = ROUND / 'SOURCES' / (expected + '.py.gz')
        need(sha(gzip.decompress(archive.read_bytes())) == expected, 'archived exact source bytes: ' + name)
        archives.add(expected)
        if sha((ROOT / name).read_bytes()) != expected:
            # Historical launch bytes remain authoritative for administrative
            # checkers extended after a run; scientific modules must stay fixed.
            need(name.endswith('/audit_round.py'), 'frozen scientific source changed: ' + name)
            archive_only.append(name)
    for ref in protocol['inputs'].values():
        path = (ROOT if ref['path_base'] == 'repository' else PKG) / ref['path']
        need(sha(path.read_bytes()) == ref['sha256'], 'registered input bytes unchanged')
    phases = {name: read(run / (name.upper() + '-TASKS.json.gz'))
              for name in meta['completed_by_phase']}
    seen, seeds, statuses, cpu, peaks, max_seconds = set(), set(), set(), 0., [], 0.
    counts, profile_kinds, artifacts = Counter(), Counter(), set()
    specs_by_seed, decisions_by_seed, visited_indices = {}, {}, {p: set() for p in phases}
    fields_seen, task_details = set(), []
    for ref in meta['results']:
        result = read(reference(ref))
        seed = result['seed']
        need(seed not in seeds, 'distinct confirmation seeds')
        seeds.add(seed); statuses.add(result['status']); cpu += result['cpu_seconds']
        need(result['preregistration_sha256'] == preg_sha, 'seed registration binding')
        need(result['script_sha256'] == implementation['script_sha256'], 'seed implementation binding')
        need(result['source_provenance'] == implementation['source_provenance'], 'seed credit binding')
        need(result['source_attribution'] == implementation['source_attribution'],
             'complete attributed word set bound by implementation')
        need(result['no_kappa_claim'] is True, 'local evidence does not claim a kappa admission')
        credits = {x['path']: x for x in result['source_attribution']}
        for name, credit in original.items():
            need(name in credits and all(credits[name].get(k) == v for k, v in credit.items()),
                 'all inherited source credits retained')
        need(len(credits) == 23, '21 original plus two current word credits')
        specs_by_seed[seed], decisions_by_seed[seed] = [], []
        artifacts.update(artifact_refs(result))
        for task in result['task_receipts']:
            path = reference(task)
            need(str(path) not in seen, 'unique task receipt')
            seen.add(str(path))
            phase = path.parent.name
            need(phase in phases, 'task phase is registered by the run')
            index = int(path.name.split('.')[0].split('-')[-1])
            need(index not in visited_indices[phase] and 0 <= index < len(phases[phase]),
                 'task index lies in the unique exact phase inventory')
            visited_indices[phase].add(index)
            spec = phases[phase][index]
            receipt = read(path)
            need(receipt['status'] == 'OK', 'completed pool tasks must be OK; no silent errors')
            value = receipt['result']
            need(value['seed'] == seed == spec['seed'], 'task belongs to recorded seed')
            peaks.append(receipt['peak_rss_bytes'])
            max_seconds = max(max_seconds, receipt['seconds'])
            counts[phase, value['status']] += 1
            spec_key = canonical(scientific(spec))
            specs_by_seed[seed].append((phase, spec_key))
            decision = scientific(value)
            fields_seen.update(decision)
            decisions_by_seed[seed].append((phase, spec_key, canonical(decision)))
            task_details.append((phase, spec, value))
            if value.get('moment_delta') is not None:
                delta = value['moment_delta']
                if isinstance(delta, dict) and 'exact_profile_identity' in delta:
                    profile_kinds['identical' if delta['exact_profile_identity'] else 'different'] += 1
            artifacts.update(artifact_refs(value))
            artifacts.update(artifact_refs(spec))
    need(seeds == set(protocol['seeds']) and len(seeds) == 2, 'both distinct registered seeds present')
    need(statuses == {meta['status']} == {row['status']}, 'all scientific status records agree')
    need(meta['status'] in {'NULL', 'EXPLORATORY'}, 'local family cannot promote a new kappa claim')
    need(meta['confirmed'] is True and meta.get('scientific_decision_agreement') is True,
         'recorded scientific confirmation')
    references = {(v['provider'], v['seed']): v for p, _s, v in task_details if p == 'reference'}
    need(set(references) == {(p, s) for p in ('base', 'extra') for s in seeds},
         'all four complete reference-control tasks')
    declared_reference = set(meta['statistics']['reference_only_nominees'])
    observed_reference = {p for p in ('base', 'extra')
                          if references[p, min(seeds)]['outcome'] == 'REFERENCE_GAIN'}
    need(declared_reference == observed_reference, 'reference-only nominee accounting')
    for phase, spec, value in task_details:
        if phase == 'validation':
            need(value['status'] == 'PASS' and
                 value['negative_controls'] == {'omitted_paid_child': True, 'omitted_cleanup': True},
                 'complete local nominee admission and both mutant controls')
            need(value['audit']['audit']['checked_columns'] == 632 and
                 value['audit']['audit']['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
                 'nominee local audit covers all columns in both orientations')
            if spec['candidate_id'] == 'reference':
                expected = references[spec['provider'], spec['seed']]
                need(spec['provider'] in declared_reference and
                     spec['word']['sha256'] == expected['word']['sha256'],
                     'reference validation binds the separately emitted reference word')
    reference_validations = [(s['provider'], s['seed']) for p, s, _v in task_details
                             if p == 'validation' and s['candidate_id'] == 'reference']
    need(sorted(reference_validations) == sorted((p, s) for p in declared_reference for s in seeds),
         'both-seed validation for every reference-only nominee')
    s0, s1 = sorted(seeds)
    need(sorted(specs_by_seed[s0]) == sorted(specs_by_seed[s1]), 'same exact task domains in both seeds')
    need(sorted(decisions_by_seed[s0]) == sorted(decisions_by_seed[s1]),
         'same saved scientific decisions, profiles and named witnesses in both seeds')
    need(abs(cpu - meta['total_cpu_seconds']) < 1e-5, 'per-seed CPU accounting closes')
    need(len(seen) == sum(meta['completed_by_phase'].values()), 'all pool receipts accounted for')
    for phase, specs in phases.items():
        need(len(specs) == meta['completed_by_phase'][phase], 'complete phase task count')
        need(visited_indices[phase] == set(range(len(specs))), 'every phase index covered exactly once')
        projection = read(run / (phase.upper() + '-MEMORY-PROJECTION.json'))
        need(projection['workers'] == 61 and projection['reserved_cores'] == 8 and
             projection['workers'] == min(120, int(projection['ram_gib'] / 4)),
             'registered worker allocation')
        need(projection['projected_peak_gib'] < projection['ram_gib'], 'projected memory within RAM')
        need(projection['projected_per_worker_gib'] <= 4 and projection['worker_rss_cap_gib'] == 4,
             'per-worker memory cap')
    need(max(peaks, default=0) < 4 * (1 << 30) and max_seconds <= 300, 'observed task resource caps')
    return dict(status=meta['status'], confirmed=meta['confirmed'], seeds=sorted(seeds),
        pool_tasks=len(seen), completed_by_phase=meta['completed_by_phase'],
        outcomes=[dict(phase=p, status=s, count=n) for (p, s), n in sorted(counts.items())],
        priced_profile_kinds=dict(profile_kinds), cpu_seconds=cpu, wall_seconds=meta['total_wall_seconds'],
        peak_rss_bytes=max(peaks, default=0), longest_task_seconds=max_seconds,
        source_credits_per_result=23, archived_administrative_preimages=archive_only,
        compared_saved_decision_fields=sorted(fields_seen), artifact_references_checked=len(artifacts),
        reference_controls=len(references), reference_only_nominees=sorted(declared_reference),
        reference_nominee_validations=len(reference_validations),
        scientific_scope='Saved finite local decisions only; no scientific rerun, native/outer proof or kappa claim.'), archives


def build_audit():
    registry, task_card = read(ROUND / 'EXPERIMENTS.json'), read(ROUND / 'TASK.json')
    need(registry['no_active_experiments'], 'all pools terminal')
    need(task_card['base_work_commit'] == BASE, 'registered pre-round evidence base')
    original = read(PKG / 'data/words/PINS.json')['files']
    need(len(original) == 21, 'original complete word source set')
    reports, archives = {}, set()
    retired = [x for x in registry['experiments'] if x['id'] == 'R1-B-REPAIR']
    need(len(retired) == 1 and retired[0]['execution'] == 'NOT_RUN' and
         retired[0]['status'] == 'EXPLORATORY' and retired[0]['confirmed'] is False and
         retired[0]['cpu_seconds'] == retired[0]['wall_seconds'] == 0 and
         retired[0]['result_files'] == [], 'R1 was retired without scientific execution or null claim')
    retired_path = PKG / retired[0]['preregistration']
    need(sha(retired_path.read_bytes()) == retired[0]['preregistration_sha256'],
         'unexecuted R1 preregistration remains frozen')
    need(not list((ROUND / 'R1-B-REPAIR').glob('v*/RUN.json')),
         'no hidden R1 scientific run')
    for label, experiment in FAMILIES:
        rows = [x for x in registry['experiments'] if x['id'] == experiment]
        need(len(rows) == 1, 'one registered family row')
        reports[experiment], used = audit_family(label, experiment, rows[0], original, task_card)
        archives.update(used)
    total_cpu = sum(x['cpu_seconds'] for x in reports.values())
    need(total_cpu < task_card['round_cpu_budget_seconds'], 'round experimental CPU budget')
    source = PKG / 'data/continuation-05/pr2979'
    need(sha((source / 'ACQUISITION.json').read_bytes()) == ACQUISITION_SHA, 'acquisition registration')
    acquisition = read(source / 'ACQUISITION.json')
    need(len(acquisition['files']) == 112 and acquisition['manifest_entries_checked'] == 111,
         'complete bounded source package')
    need(sha((source / 'package/MANIFEST.json').read_bytes()) == MANIFEST_SHA, 'source manifest pin')
    manifest = read(source / 'package/MANIFEST.json')
    pins = {x['path']: x for x in acquisition['files']}
    need(len(manifest) == 111 and set(manifest) == set(pins) - {'MANIFEST.json'}, 'complete manifest coverage')
    for pin in acquisition['files']:
        path = PKG / pin['local_path']
        raw = path.read_bytes()
        need(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'all acquired package bytes preserved')
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest() == pin['git_blob'],
             'exact acquired Git blob')
        need(path.suffix != '.py', 'fetched programs remain inert text')
        if pin['path'] in manifest:
            need(manifest[pin['path']] == pin['sha256'], 'source manifest membership')
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', BASE, '--', 'research/styles-r11/'], cwd=ROOT)
    preserved = 0
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t', 1)
        _, kind, blob = info.split()
        need(kind == b'blob', 'ordinary frozen evidence file')
        raw = (ROOT / name.decode()).read_bytes()
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode() == blob,
             'pre-round evidence preserved: ' + name.decode())
        preserved += 1
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT).decode().splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT).decode().splitlines()
    need(all(x.startswith('research/styles-r11/') for x in changed + untracked), 'authorized write scope')
    audit_path = ROUND / 'AUDIT.json'
    size = sum(x.stat().st_size for x in (PKG / 'results').rglob('*') if x.is_file() and x != audit_path)
    round_size = sum(x.stat().st_size for x in ROUND.rglob('*') if x.is_file() and x != audit_path)
    need(size < 200000000 and round_size < task_card['resources']['round_new_result_bytes_cap'],
         'global and current-round result storage caps')
    return dict(schema_version=1, status='PASS', kind='administrative byte and receipt audit; no scientific reruns',
        script_sha256=sha(Path(__file__).read_bytes()), base_work_commit=BASE,
        preserved_pre_round_files=preserved, experiments=reports,
        retired_without_execution=[dict(id=retired[0]['id'], status='EXPLORATORY',
            execution='NOT_RUN', empirical_null=False,
            preregistration_sha256=retired[0]['preregistration_sha256'])],
        total_pool_tasks=sum(x['pool_tasks'] for x in reports.values()),
        total_experimental_cpu_seconds=total_cpu, distinct_prepinned_source_archives=len(archives),
        results_bytes_excluding_audit=size, round_result_bytes_excluding_audit=round_size,
        current_source_package_files=112, current_source_manifest_entries=111)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true', help='create AUDIT.json once; otherwise inspect only')
    args = parser.parse_args()
    started = time.process_time()
    payload = build_audit()
    destination = ROUND / 'AUDIT.json'
    if destination.exists():
        existing = read(destination)
        need(existing['stable'] == payload, 'immutable audit payload still matches all saved evidence')
        print(json.dumps(dict(status='PASS', immutable_audit=str(destination.relative_to(PKG)),
                              sha256=sha(destination.read_bytes()), overwritten=False), sort_keys=True))
        return
    output = dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
                  administrative_cpu_seconds=time.process_time() - started, stable=payload)
    raw = (json.dumps(output, indent=2, sort_keys=True) + '\n').encode()
    need(payload['results_bytes_excluding_audit'] + len(raw) < 200000000, 'storage cap including audit')
    if args.write:
        with destination.open('xb') as handle:
            handle.write(raw)
    print(json.dumps(output, sort_keys=True))


if __name__ == '__main__':
    main()
