"""Read-only saved-receipt audit for continuation08; no scientific imports.

Run after the round registry and reports close. --write creates AUDIT.json once;
subsequent invocations compare the stable body without rewriting the receipt.
Source archives may live in earlier rounds and are authenticated by both their
compressed byte digest and the frozen source payload digest.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-08'
BASE = 'f9671de10c8bb72fa4b3956f734e902f47a400df'
FAMILY = 'F1-CARRIER-FACTORIZATIONS'
SEEDS = {41117, 83003}
PROVIDERS = {'base', 'extra'}
IGNORE = {'seed', 'cpu_seconds', 'wall_seconds', 'elapsed_seconds', 'seconds',
          'recorded_utc', 'output_dir', 'schedule'}
CHECKED_REFS = set()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def clean(value):
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        out = {k: clean(v) for k, v in value.items() if k not in IGNORE}
        if 'path' in out and 'sha256' in out:
            out['path'] = '<separate-path-identical-bytes>'
        return out
    return value


def local_path(name):
    p = Path(name)
    p = (ROOT / p if str(p).startswith('research/styles-r11/') else PKG / p).resolve()
    need(p.is_relative_to(PKG), 'artifact path confined to r11: ' + name)
    return p


def reference(ref):
    p = local_path(ref['path'])
    raw = p.read_bytes()
    need(digest(raw) == ref['sha256'], 'artifact SHA256: ' + str(p))
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'artifact byte count')
    if 'payload_sha256' in ref:
        payload = gzip.decompress(raw) if p.suffix == '.gz' else raw
        need(digest(payload) == ref['payload_sha256'], 'artifact payload SHA256')
    if 'git_blob' in ref:
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
             == ref['git_blob'], 'artifact Git blob')
    CHECKED_REFS.add(str(p.relative_to(PKG)))
    return p


def references(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            if value['path'].startswith(('data/', 'results/', 'pipeline/', 'research/styles-r11/')):
                reference(value)
        for v in value.values():
            references(v)
    elif isinstance(value, list):
        for v in value:
            references(v)


def credits(result, original):
    rows = result['source_attribution']
    by_path = {x['path']: x for x in rows}
    need(len(by_path) == len(rows), 'unique attribution identities')
    for name, pin in original.items():
        need(name in by_path and all(by_path[name].get(k) == v for k, v in pin.items()),
             'all21 original PINS source credits')
    return len(rows)


def acquisition(ref):
    path = reference(ref)
    value = read(path)
    files = value['files']
    need(isinstance(files, list), 'acquisition list schema')
    total = 0
    for row in files:
        name = row.get('local_path', row.get('path'))
        pin = {k: row[k] for k in ('sha256', 'bytes', 'git_blob') if k in row}
        pin['path'] = name
        p = reference(pin)
        need(p.suffix != '.py', 'fetched programs stored only as inert text')
        total += p.stat().st_size
    return dict(path=str(path.relative_to(PKG)), sha256=digest(path.read_bytes()),
                files=len(files), payload_bytes=total, author=value.get('author', value.get('author_login')))


def archives(pins, implementation):
    mapping = pins['source_archives']
    need(implementation['source_archives'] == mapping, 'implementation/archive-reference agreement')
    need(set(mapping) == set(pins['sha256'].values()), 'all frozen source payloads archived')
    historical = []
    for name, expected in pins['sha256'].items():
        archive = reference(mapping[expected])
        need(digest(gzip.decompress(archive.read_bytes())) == expected, 'exact frozen source preimage')
        p = local_path(name)
        if not p.exists() or digest(p.read_bytes()) != expected:
            need(name.endswith(('/audit_round.py', '/final_checkpoint.py', '/checkpoint_sources.py')),
                 'scientific source changed after freeze: ' + name)
            historical.append(name)
    return dict(unique_source_payloads=len(mapping), historical_administrative_preimages=historical,
                reused_earlier_archives=sum(not local_path(x['path']).is_relative_to(ROUND)
                                          for x in mapping.values()))


def address_key(row):
    address = row['address']
    return (('A', 'B').index(address[0]), *address[1:])


def saved_domain(tasks, seed_results, protocol, meta, run):
    census = {(s['seed'], s['provider']): v for phase, s, v, _ in tasks if phase == 'census'}
    price = {(s['seed'], s['provider'], s['shard']): v
             for phase, s, v, _ in tasks if phase == 'prices'}
    need(set(census) == {(s, p) for s in SEEDS for p in PROVIDERS}, 'both complete source censuses')
    need(set(price) == {(s, p, i) for s in SEEDS for p in PROVIDERS for i in range(64)},
         'all64 shards for each seed/provider')
    summaries = {}
    favorable = {}
    for provider in sorted(PROVIDERS):
        twins = [census[s, provider] for s in sorted(SEEDS)]
        need(clean(twins[0]) == clean(twins[1]), 'two-seed exact census equality')
        c = twins[0]
        candidates = c['candidates']
        need(c['complete'] and c['status'] == 'PASS' and not c['restore_search'], 'fixed A/B domain only')
        need(len(candidates) == c['counts']['candidates'] and
             len({x['candidate_id'] for x in candidates}) == len(candidates), 'unique exhaustive candidate inventory')
        need(candidates == sorted(candidates, key=address_key), 'canonical numeric domain order')
        need(digest(canonical(candidates).encode()) == c['domain_sha256'], 'exact census domain digest')
        need(len(candidates) == 8*c['counts']['admissible_carrier_choices'], 'all eight labels per allowed carrier')
        per_seed = {}
        for seed in sorted(SEEDS):
            rows = []
            totals = Counter()
            for shard in range(64):
                v = price[seed, provider, shard]
                need(v['status'] == 'PASS' and v['complete'] and v['shard'] == shard and v['shards'] == 64,
                     'complete disjoint shard specification')
                need(v['domain_sha256'] == c['domain_sha256'], 'shard binds the registered canonical census')
                need(digest(canonical(v['rows']).encode()) == v['shard_rows_sha256'], 'exact saved shard row hash')
                expected = list(range(shard, len(candidates), 64))
                need([x['ordinal'] for x in v['rows']] == expected, 'all and only assigned canonical ordinals')
                for row in v['rows']:
                    src = candidates[row['ordinal']]
                    need(all(row[k] == src[k] for k in ('candidate_id', 'pair_key', 'address')),
                         'price row binds exact candidate address')
                    moment = row.get('moment_delta')
                    if row['status'] == 'REJECTED_GUARD':
                        need(row.get('guard_failures') and row.get('profile_delta') is None,
                             'guard rejection has explicit witness')
                    else:
                        need(moment is not None, 'resolved price has saved interval')
                        lo, hi = Fraction(moment['lower']), Fraction(moment['upper'])
                        need(lo <= hi and moment['endpoint'] == protocol['comparison']['complex_endpoint'],
                             'saved exact interval and fixed comparator')
                        need(sum(int(r)*n for r, n in row['profile_delta'].items()) == 0,
                             'saved signed profile has exact zero mass')
                        if row['status'] == 'PASS_CANDIDATE':
                            need(hi < 0, 'favorable row certified strictly negative')
                        elif row['status'] == 'NO_GAIN':
                            need(not row['profile_delta'] or lo >= 0, 'nonnegative row actually resolved')
                        else:
                            need(row['status'] == 'EXPLORATORY' and lo < 0 <= hi,
                                 'unresolved sign remains exploratory')
                need(v['favorable'] == [x for x in v['rows'] if x['status'] == 'PASS_CANDIDATE'],
                     'all favorable rows retained in compact output')
                counts = Counter(x['status'] for x in v['rows'])
                need(v['counts']['candidates'] == len(v['rows']), 'saved shard candidate total')
                need(v['counts'].get('unresolved', v['counts'].get('EXPLORATORY', 0)) == counts['EXPLORATORY'],
                     'unresolved counter matches actual saved rows')
                for name in ('PASS_CANDIDATE', 'NO_GAIN', 'REJECTED_GUARD', 'EXPLORATORY'):
                    if name in v['counts']:
                        need(v['counts'][name] == counts[name], 'saved per-status shard count')
                rows.extend(v['rows'])
                totals.update(v['counts'])
            rows.sort(key=lambda row: row['ordinal'])
            need([x['ordinal'] for x in rows] == list(range(len(candidates))), 'no domain omission or duplication')
            per_seed[seed] = rows
            need(dict(totals) == seed_results[seed]['statistics']['counts_by_provider'][provider],
                 'RESULT aggregate equals every saved shard')
        need(per_seed[min(SEEDS)] == per_seed[max(SEEDS)], 'all price rows agree across seeds')
        favorable[provider] = {x['candidate_id']: x for x in per_seed[min(SEEDS)]
                               if x['status'] == 'PASS_CANDIDATE'}
        summaries[provider] = dict(candidates=len(candidates), shards_per_seed=64,
                                  status_counts=dict(Counter(x['status'] for x in per_seed[min(SEEDS)])))
    selection = read(run / 'SELECTION.json')
    common = sorted(set(favorable['base']) & set(favorable['extra']),
                    key=lambda cid: address_key(favorable['base'][cid]))
    selected = common[:protocol['retained_pair_limit']]
    need(selection['paired_favorable'] == len(common) and
         selection['selected_pair_keys'] == [favorable['base'][x]['pair_key'] for x in selected] and
         selection['unretained_paired_favorable'] == len(common)-len(selected),
         'first8 canonical matched candidates without post-hoc ranking')
    retained = {(s['seed'], s['provider'], s['candidate_id']): v
                for phase, s, v, _ in tasks if phase == 'retention'}
    need(set(retained) == {(s, p, cid) for s in SEEDS for p in PROVIDERS for cid in selected},
         'all retained candidates validated with both providers and seeds')
    for cid in selected:
        for provider in sorted(PROVIDERS):
            twins = [retained[s, provider, cid] for s in sorted(SEEDS)]
            need(clean(twins[0]) == clean(twins[1]), 'two-seed retained-word validation agreement')
            for v in twins:
                need(v['status'] == 'PASS_CANDIDATE', 'retained canonical construction passes')
                audit = v['independent_local_admission']
                need(audit['status'] == 'PASS' and audit['audit']['checked_columns'] == 632 and
                     audit['audit']['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
                     'all632 independent retained-word columns in both orientations')
                need(v['independent_rejecting_controls'] ==
                     dict(wrong_scalar=True, omitted_paid_child=True, omitted_cleanup=True),
                     'all three scientific mutation controls reject')
                need(not v['kappa_claim'] and v['fresh_native_admission'] == 'UNRUN_REQUIRED' and
                     v['complete_supplier_outer_admission'] == 'UNRUN_REQUIRED', 'finite scope preserved')
                reference(v['word'])
    unresolved = sum(s['status_counts'].get('EXPLORATORY', 0) for s in summaries.values())
    total = sum(s['candidates'] for s in summaries.values())
    expected = ('EXPLORATORY' if unresolved else 'PASS' if selected else 'EXPLORATORY'
                if any(favorable.values()) or total == 0 else 'NULL')
    need(meta['status'] == expected, 'registered scientific disposition from saved coverage and exact signs')
    return dict(providers=summaries, selected_pairs=len(selected), unvalidated_paired=len(common)-len(selected),
                unresolved_rows=unresolved, decision_from_saved_records=expected)


def audit_attempt(row, attempt, original):
    version = attempt['attempt']
    run = ROUND / FAMILY / version
    meta = read(run / 'RUN.json')
    preg_path = ROUND / 'F1/PREREGISTRATION.json'
    protocol = read(preg_path)
    pins_path = ROUND / 'F1' / ('IMPLEMENTATION-PINS-' + version + '.json')
    pins = read(pins_path)
    implementation = read(run / 'IMPLEMENTATION.json')
    need(protocol['state'] == 'FROZEN' and set(protocol['seeds']) == SEEDS, 'exact frozen family and seeds')
    need(implementation['script_sha256'] == pins['sha256'] and
         implementation['preregistration_sha256'] == digest(preg_path.read_bytes()) and
         implementation['implementation_pins_sha256'] == digest(pins_path.read_bytes()), 'source/protocol freeze bindings')
    source_report = archives(pins, implementation)
    frozen_time = pins.get('registered_utc', pins.get('recorded_utc'))
    need(frozen_time is not None and pins.get('freeze_before_import_or_preparation') is True,
         'implementation frozen before preparation')
    need(datetime.fromisoformat(protocol['registered_utc']) <= datetime.fromisoformat(frozen_time),
         'registration precedes source freeze')
    need(implementation['parent_load_once'] is True and set(implementation['prepared']) == {'constructor'},
         'one recorded parent preparation')
    references(protocol['inputs'])
    references(implementation['provenance'])
    phases = {phase: read(run / (phase.upper() + '-TASKS.json.gz')) for phase in meta['completed_by_phase']}
    visits = {phase: set() for phase in phases}
    results, tasks, statuses, rss, seconds = {}, [], Counter(), [], []
    for ref in meta['results']:
        result = read(reference(ref))
        seed = result['seed']
        need(seed in SEEDS and seed not in results, 'unique registered result seed')
        results[seed] = result
        need(datetime.fromisoformat(result['recorded_utc']) >= datetime.fromisoformat(frozen_time),
             'source freeze precedes scientific result')
        need(result['status'] == meta['status'] == attempt['status'], 'all attempt dispositions agree')
        need(result['script_sha256'] == pins['sha256'] and
             result['preregistration_sha256'] == digest(preg_path.read_bytes()) and
             result['implementation_pins_sha256'] == digest(pins_path.read_bytes()), 'RESULT freezes exact source and protocol')
        need(result['source_attribution'] == implementation['source_attribution'], 'all source credits preserved in each RESULT')
        credits(result, original)
        need(not result['decision']['pattern_claim'] and not result['decision']['kappa_claim'] and
             result['n_permutations'] == 0, 'finite census is not a pattern or kappa claim')
        references(result.get('inputs', {}))
        for task_ref in result['task_receipts']:
            path = reference(task_ref)
            phase = path.parent.name
            need(phase in phases, 'task belongs to a launched phase')
            ordinal = int(path.name.split('.')[0].split('-')[-1])
            need(ordinal not in visits[phase] and 0 <= ordinal < len(phases[phase]), 'unique task receipt address')
            visits[phase].add(ordinal)
            spec = phases[phase][ordinal]
            need(spec['seed'] == seed, 'task owned by its RESULT seed')
            receipt = read(path)
            statuses[receipt['status']] += 1
            rss.append(receipt.get('peak_rss_bytes') or 0)
            seconds.append(receipt.get('seconds') or 0)
            if receipt['status'] == 'OK':
                value = receipt['result']
                need(value['seed'] == seed, 'task output seed')
                references(value)
                tasks.append((phase, spec, value, receipt))
            else:
                need(meta['failure'] is not None, 'infrastructure exception cannot become scientific rejection')
    need(set(results) == SEEDS, 'both distinct seed RESULTs retained')
    cpu = sum(v['cpu_seconds'] for v in results.values())
    need(abs(cpu-meta['total_cpu_seconds']) < 1e-5 and abs(cpu-attempt['cpu_seconds']) < 1e-5,
         'all experimental CPU is accounted')
    need(abs(meta['total_wall_seconds']-attempt['wall_seconds']) < 1e-8, 'wall accounting')
    need(meta['workers'] == 61, 'central61-worker pool')
    for phase, seen in visits.items():
        need(len(seen) == meta['completed_by_phase'][phase], 'all completed receipts included once')
    projections = []
    for path in sorted(run.glob('*MEMORY-PROJECTION.json')):
        value = read(path)
        need(value['workers'] == min(120, int(value['ram_gib']//4)) == 61 and
             value['reserved_cores'] >= 8, 'registered RAM/core worker rule')
        need(value['worker_rss_cap_gib'] == 4 and value['projected_peak_gib'] < value['ram_gib'],
             'per-worker RSS and projected peak bounds')
        projections.append(dict(path=str(path.relative_to(PKG)), sha256=digest(path.read_bytes()),
                                projected_peak_gib=value['projected_peak_gib']))
    need(len(projections) == len(phases)+1, 'parent and every pool launch were projected')
    need(max(rss, default=0) <= 4*1024**3 and max(seconds, default=0) <= 301,
         'recorded RSS and300-second task limits')
    summary = dict(attempt=version, status=meta['status'], pool_tasks=sum(map(len, visits.values())),
                   completed_by_phase=meta['completed_by_phase'], pool_status_counts=dict(statuses),
                   cpu_seconds=cpu, wall_seconds=meta['total_wall_seconds'],
                   max_worker_rss_bytes=max(rss, default=0), max_task_seconds=max(seconds, default=0),
                   source_archives=source_report, memory_projections=projections,
                   source_credits_per_result={str(s): len(v['source_attribution']) for s, v in results.items()})
    if meta['failure'] is not None:
        need(meta['status'] in {'ERROR', 'TIMEOUT'} and not meta['confirmed'], 'failed attempt preserved as failure')
        summary['failure'] = meta['failure']
        return summary
    need(all(v['confirmed'] and v['scientific_decision_agreement'] and v['failure'] is None
             for v in results.values()) and meta['confirmed'], 'two-seed scientific decision agreement')
    for phase, spec, value, _ in tasks:
        if phase in ('controls', 'baseline', 'census', 'prices'):
            need(value['status'] == 'PASS', 'all primary checks and shards completed')
        if phase == 'baseline':
            finite = value['local_admission']['audit']
            need(finite['checked_columns'] == finite['independent_inputs'] == 632 and
                 finite['orientations'] == {'forward': 'PASS', 'dual': 'PASS'} and
                 finite['restored_cold'] == finite['zero_buffers'] == 91, 'all baseline semantic columns and buffers')
    expected = dict(controls=2, baseline=4, census=4, prices=256)
    if 'retention' in phases:
        expected['retention'] = len(phases['retention'])
        need(0 < expected['retention'] <= 32 and expected['retention'] % 4 == 0, 'bounded paired retention')
    need(meta['completed_by_phase'] == expected, 'exact registered phase coverage')
    for phase, seen in visits.items():
        need(seen == set(range(len(phases[phase]))), 'no omitted task in completed phase')
    for seed, result in results.items():
        need(result['statistics'] == meta['statistics'][str(seed)], 'RUN/RESULT statistics equality')
    need(clean(results[min(SEEDS)]['statistics']) == clean(results[max(SEEDS)]['statistics']),
         'two-seed aggregate statistics equality')
    summary['domain'] = saved_domain(tasks, results, protocol, meta, run)
    return summary


def preserved_base():
    tree = subprocess.check_output(['git', 'ls-tree', '-rz', BASE, '--', 'research/styles-r11/'], cwd=ROOT)
    count = 0
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t', 1)
        _, kind, blob = info.split()
        need(kind == b'blob', 'ordinary pre-round evidence file')
        raw = (ROOT / name.decode()).read_bytes()
        need(hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest().encode() == blob,
             'immutable prior evidence: ' + name.decode())
        count += 1
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, text=True).splitlines()
    need(all(p.startswith('research/styles-r11/') for p in changed+untracked), 'authorized write confinement')
    return count


def build_audit():
    CHECKED_REFS.clear()
    registry = read(ROUND / 'EXPERIMENTS.json')
    task = read(ROUND / 'TASK.json')
    need(task['base_work_commit'] == BASE and registry['no_active_experiments'], 'closed scientific pools and exact round base')
    need('RUNNING' not in registry['status'].upper(), 'registry closed before audit')
    original = read(PKG / 'data/words/PINS.json')['files']
    need(len(original) == 21, 'original PINS cardinality')
    row = next(x for x in registry['experiments'] if x['id'] == FAMILY)
    need(row['execution'] in {'COMPLETED', 'INCOMPLETE'} and row['status'] in {'PASS', 'NULL', 'EXPLORATORY', 'ERROR', 'TIMEOUT'},
         'final scoped family disposition')
    preg = ROUND / 'F1/PREREGISTRATION.json'
    need(row['preregistration_sha256'] == digest(preg.read_bytes()), 'registry preregistration hash')
    reports = [audit_attempt(row, attempt, original) for attempt in row['attempts']]
    need(reports[-1]['status'] == row['status'] and
         abs(sum(x['cpu_seconds'] for x in reports)-row['cpu_seconds']) < 1e-5, 'all attempts included in registry')
    need(row['cpu_seconds'] < task['round_cpu_budget_seconds'], 'round scientific CPU budget')
    acquisitions = []
    protocol = read(preg)
    for name, ref in protocol['inputs'].items():
        if name.endswith('_acquisition'):
            acquisitions.append(acquisition(ref))
    preserved = preserved_base()
    documents = {name: digest((ROUND/name).read_bytes()) for name in
                 ('RESULTS.md', 'HANDBACK.md', 'PREDICTIONS.json', 'EXPERIMENTS.json', 'TASK.json')}
    checkpoints = {}
    for label in ('checkpoint', 'final-checkpoint'):
        path = PKG / 'data/continuation-08' / label / 'RECEIPT.json'
        if not path.exists():
            need(label != 'checkpoint', 'initial source checkpoint required')
            continue
        receipt = read(path)
        need(not receipt['errors'], 'source checkpoint errors disclosed')
        for relative, pin in receipt['files'].items():
            need(digest((path.parent/relative).read_bytes()) == pin['sha256'], 'checkpoint saved-byte digest')
        checkpoints[label] = dict(sha256=digest(path.read_bytes()), canonical_main=receipt['canonical_main'],
                                  priority_revision=receipt['priority_revision'], files=len(receipt['files']))
    destination = ROUND / 'AUDIT.json'
    global_bytes = sum(p.stat().st_size for p in (PKG/'results').rglob('*') if p.is_file() and p != destination)
    round_bytes = sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file() and p != destination)
    need(global_bytes < 200000000 and round_bytes < 4000000, 'global200MB and round4MB artifact caps')
    return dict(schema_version=1, status='PASS', kind='Administrative saved-byte audit; no scientific reruns',
                script_sha256=digest(Path(__file__).read_bytes()), base_work_commit=BASE,
                preserved_pre_round_files=preserved, experiments={FAMILY: reports},
                total_pool_tasks=sum(x['pool_tasks'] for x in reports),
                total_experimental_cpu_seconds=sum(x['cpu_seconds'] for x in reports),
                acquisitions=acquisitions, source_checkpoints=checkpoints, final_documents=documents,
                local_artifact_references_checked=len(CHECKED_REFS),
                results_bytes_excluding_audit=global_bytes, round_bytes_excluding_audit=round_bytes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    started = time.process_time()
    stable = build_audit()
    path = ROUND / 'AUDIT.json'
    if path.exists():
        need(read(path)['stable'] == stable, 'immutable administrative audit still agrees')
        print(json.dumps(dict(status='PASS', sha256=digest(path.read_bytes()), overwritten=False)))
        return
    value = dict(recorded_utc=datetime.now(timezone.utc).isoformat(),
                 administrative_cpu_seconds=time.process_time()-started, stable=stable)
    raw = (json.dumps(value, indent=2, sort_keys=True)+'\n').encode()
    need(stable['results_bytes_excluding_audit']+len(raw) < 200000000 and
         stable['round_bytes_excluding_audit']+len(raw) < 4000000, 'artifact caps include audit bytes')
    if args.write:
        with path.open('xb') as stream:
            stream.write(raw)
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()
