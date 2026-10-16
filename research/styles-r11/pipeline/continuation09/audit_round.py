"""Administrative saved-byte audit for continuation09; no scientific imports.

Run after the coordinator closes all receipts, reports and registry. --write
creates AUDIT.json once; repeat verification checks its stable payload without
rewriting immutable bytes. Detailed evidence lives under data from the outset.
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

PKG=Path(__file__).resolve().parents[2]
ROOT=PKG.parents[1]
ROUND=PKG/'results/CONTINUATION-09'
DATA=PKG/'data/continuation-09'
BASE='0f13eb4b75964dd8cd050fbb15cad67956edfb60'
FAMILY='J1-SHARED-CARRIERS'
SEEDS={49019,98009}
PROVIDERS={'base','extra'}
IGNORE={'seed','cpu_seconds','wall_seconds','elapsed_seconds','seconds','recorded_utc','output_dir','schedule'}
CHECKED_REFS=set()
_SPANS={}


def read(path):
    path=Path(path)
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def local_path(name):
    p=Path(name)
    p=(ROOT/p if str(p).startswith('research/styles-r11/') else PKG/p).resolve()
    need(p.is_relative_to(PKG), 'artifact path confined to r11: '+str(name))
    return p


def need(ok, message):
    if not ok:
        raise ValueError(message)



def digest(raw):
    return hashlib.sha256(raw).hexdigest()



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
        p = (ROOT / name).resolve()
        need(p.is_relative_to(ROOT), 'trusted frozen source is repository-confined')
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



def span(frame):
    key = tuple(frame)
    if key not in _SPANS:
        need(all(type(x) is int and 0 <= x < 512 for x in key), 'saved GF2 frame coordinates')
        values = {0}
        for x in key:
            values |= {y ^ x for y in values}
        _SPANS[key] = frozenset(values)
    return _SPANS[key]



def guard_certificate(value):
    predicate = value['predicate']
    if predicate == 'frame_inclusion':
        lower, upper = span(value['lower_frame']), span(value['upper_frame'])
    elif predicate == 'exit_inclusion':
        lower, upper = span(value['actual']), span(value['required'])
    else:
        need(predicate == 'exit_equality' and span(value['actual']) != span(value['required']),
             'saved exit equality is a genuine subspace inequality')
        return
    witness = value['excluded_vector']
    need(witness in lower and witness not in upper, 'saved exclusion vector certifies failed inclusion')



def structural_certificates(census):
    rows = census['exclusions']
    need(digest(canonical(rows).encode()) == census['exclusions_sha256'], 'exact structural exclusion digest')
    counts = census['counts']
    need(len(rows) == counts['exposure_rejected_packets'] + counts['ratio_rejected_carriers'],
         'all counted structural exclusions have witnesses')
    expected_order = sorted(rows, key=lambda r: (('A', 'B').index(r['address'][0]),
                           *r['address'][1:6], r['address'][6] if len(r['address']) > 6 else -1,
                           r['predicate']))
    need(rows == expected_order, 'canonical exclusion order')
    predicates = Counter()
    for row in rows:
        predicates[row['predicate']] += 1
        address = row['address']
        need(address[0] in {'A', 'B'} and address[5] in {'in', 'out'} and
             address[1:5] == sorted(set(address[1:5])), 'literal structural exclusion address')
        if row['predicate'] == 'non_dyadic_transport_ratio':
            q = Fraction(row['ratio'])
            c = {k: Fraction(v) for k, v in row['coefficients'].items()}
            need(len(address) == 7 and address[6] in (0, 1) and q != 0 and
                 (q.numerator, q.denominator) == (row['reduced_numerator'], row['reduced_denominator']) and
                 q.denominator & (q.denominator - 1) != 0 and
                 c['b1']/c['a1'] == c['b2']/c['a2'] == q,
                 'exact reduced nondyadic common-ratio certificate')
            need(len(set(row['carrier_registers'] + row['inner_registers'])) == 4,
                 'four distinct packet registers')
        else:
            need(row['predicate'] in {'intervening_contact', 'intervening_opcode'} and len(address) == 6,
                 'recognized exposure exclusion')
            index, gate, support = row['offending_index'], row['offending_gate'], row['selected_support']
            need(len(support) == len(set(support)) == 4 and
                 address[1] < index < address[4] and index not in address[1:5],
                 'literal unselected intervening gate location')
            if row['predicate'] == 'intervening_opcode':
                need(gate[0] not in {'add', 'scale'}, 'intervening opcode violates admitted alphabet')
            else:
                need(gate[0] in {'add', 'scale'}, 'contact witness has admitted opcode')
                registers = gate[1:3] if gate[0] == 'add' else gate[1:2]
                touched = sorted(set(registers).intersection(support))
                need(touched and touched == row['touched_packet_registers'], 'explicit involved-register contact')
    need(predicates['non_dyadic_transport_ratio'] == counts['ratio_rejected_carriers'] and
         predicates['intervening_contact'] + predicates['intervening_opcode'] == counts['exposure_rejected_packets'],
         'saved structural exclusion class counts')
    return dict(predicates)


def saved_domain(tasks, seed_results, protocol, meta, run, reconcile=False):
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
        excluded = structural_certificates(c)
        need(c['complete'] and c['status'] == 'PASS' and not c['restore_search'], 'fixed A/B domain only')
        need(len(candidates) == c['counts']['candidates'] and
             len({x['candidate_id'] for x in candidates}) == len(candidates), 'unique exhaustive candidate inventory')
        need(candidates == sorted(candidates, key=address_key), 'canonical numeric domain order')
        need(digest(canonical(candidates).encode()) == c['domain_sha256'], 'exact census domain digest')
        need(len(candidates) == 40*c['counts']['admissible_carrier_choices'], 'both orders and twenty labels per allowed carrier')
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
                        for failure in row['guard_failures']:
                            guard_certificate(failure)
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
                            need(lo >= 0, 'nonnegative row actually resolved')
                            need(bool(row['profile_delta']) != moment['exact_profile_identity'],
                                 'exact identity flag agrees with signed profile')
                            if not row['profile_delta']:
                                need(lo == hi == 0, 'identical profile has exact zero moment interval')
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
            if not reconcile:
                need(dict(totals) == seed_results[seed]['statistics']['counts_by_provider'][provider],
                     'RESULT aggregate equals every saved shard')
        need(per_seed[min(SEEDS)] == per_seed[max(SEEDS)], 'all price rows agree across seeds')
        favorable[provider] = {x['candidate_id']: x for x in per_seed[min(SEEDS)]
                               if x['status'] == 'PASS_CANDIDATE'}
        summaries[provider] = dict(candidates=len(candidates), shards_per_seed=64,
                                  structural_exclusion_counts=excluded,
                                  status_counts=dict(Counter(x['status'] for x in per_seed[min(SEEDS)])),
                                  identical_profile_rows=sum(x['status'] == 'NO_GAIN' and not x['profile_delta']
                                                             for x in per_seed[min(SEEDS)]),
                                  strictly_costlier_rows=sum(x['status'] == 'NO_GAIN' and bool(x['profile_delta']) and
                                                            Fraction(x['moment_delta']['lower']) > 0
                                                            for x in per_seed[min(SEEDS)]),
                                  guard_predicate_counts=dict(Counter(g['predicate']
                                      for x in per_seed[min(SEEDS)] for g in x.get('guard_failures', []))))
    selection_path = run / 'SELECTION.json'
    selection = read(selection_path) if selection_path.exists() else None
    common = sorted(set(favorable['base']) & set(favorable['extra']),
                    key=lambda cid: address_key(favorable['base'][cid]))
    selected = common[:protocol['retained_pair_limit']]
    if selection is None:
        need(False,
             'missing selection reconciles only with zero favorable rows')
        selection = dict(paired_favorable=0, selected_pair_keys=[], unretained_paired_favorable=0)
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
    if not reconcile:
        need(meta['status'] == expected, 'registered scientific disposition from saved coverage and exact signs')
    return dict(providers=summaries, selected_pairs=len(selected), unvalidated_paired=len(common)-len(selected),
                unresolved_rows=unresolved, decision_from_saved_records=expected)



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


def control_receipt(value, protocol):
    counts = value['checks_by_family']
    need(value['status'] == 'PASS' and value['checks'] == sum(counts.values()) and
         all(type(n) is int and n > 0 for n in counts.values()), 'all saved control counters passed')
    expected = dict(recognizer_signed_dyadic=288, joint_signed_both_kinds_carriers_orders=288,
                    signed_forward_dual_identity=576, wrong_undo_sign=576, missing_undo=576,
                    wrong_second_target_coefficient=576, all_four_edge_interleavings=24,
                    all_interleavings_complete_census=24, oracle_subspace_count=8,
                    oracle_corner_guard=160, oracle_feasibility=8, oracle_twenty_corner_minimum=24)
    need(all(counts.get(k) == n for k, n in expected.items()), 'fixed signed/interleaving/oracle coverage')
    for name in ('unequal_target_ratios', 'duplicate_edge', 'centre_exclusion', 'missing_edge',
                 'zero_original_coefficient', 'nondyadic_original_coefficient', 'repeated_register_alias',
                 'non_dyadic_orientation', 'admitted_reverse_orientation', 'restore_section_excluded',
                 'extra_involved_contact_rejected', 'disjoint_intervener_admitted',
                 'hidden_warp_barrier_rejected', 'prelude_barrier_rejected', 'stale_source_rejected',
                 'stale_preimage_rejected', 'omitted_successor_charge_detected'):
        need(counts.get(name) == 1, 'registered negative/guard control: ' + name)
    fixture = value['joint_fixture']
    need(fixture['strict_delta'] == {'1': -2, '2': 1} and
         fixture['every_single_factor_exactly_neutral'] and
         fixture['scalar_count_before'] == fixture['scalar_count_after'] == 4,
         'strict joint-only positive fixture preserved')
    need(value['endpoint'] == protocol['comparison']['complex_endpoint'], 'fixed comparison endpoint in controls')
    oracle = value['independent_flag_oracle']
    need(len(oracle) == 8 and len({x['fixture'] for x in oracle}) == 8 and
         Counter(x['ambient'] for x in oracle) == Counter({3: 7, 4: 1}), 'registered 3D/4D control fixtures')
    for item in oracle:
        n = 16 if item['ambient'] == 3 else 67
        need(item['subspaces'] == n and item['complete_cartesian_flag_domain'] == n**4 and
             item['independent_set_arithmetic'] and item['all_successor_charges'] and
             len(item['exact_minima']) == 3, 'exact exhaustive small-flag control scope')
    return dict(total_checks=value['checks'], families=len(counts), exact_flag_fixtures=len(oracle))


def audit_attempt(row, attempt, original):
    version = attempt['attempt']
    run = ROUND / FAMILY / version
    detail = DATA / ('j1-' + version)
    meta = read(run / 'RUN.json')
    preg_path = ROUND / 'J1/PREREGISTRATION.json'
    protocol = read(preg_path)
    addendum_path = ROUND / 'J1/CONTROL-ADDENDUM.json'
    addendum = read(addendum_path)
    pins_path = ROUND / 'J1' / ('IMPLEMENTATION-PINS-' + version + '.json')
    pins = read(pins_path)
    implementation = read(run / 'IMPLEMENTATION.json')
    need(protocol['state'] == addendum['state'] == 'FROZEN' and set(protocol['seeds']) == SEEDS,
         'frozen family, controls and seeds')
    need(addendum['preregistration_sha256'] == digest(preg_path.read_bytes()) and
         pins['control_addendum_sha256'] == digest(addendum_path.read_bytes()) == meta['control_addendum_sha256'],
         'exact pre-execution control addendum')
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
         'source and large objects prepared once in parent')
    references(protocol['inputs'])
    references(implementation['provenance'])
    comparison = implementation['provenance']['comparison']
    need(comparison['pr'] == 3028 and comparison['replicas'] == 148 and
         comparison['physical_families'] == 133117 and comparison['source_reported_only'] and
         comparison['fresh_native_physical_outer'] is False, 'source-reported comparator scope')
    need(meta['detailed_evidence_directory'] == str(detail.relative_to(PKG)), 'declared separate detailed-data namespace')
    indexed = set()
    for ref in meta['detailed_evidence']:
        path = reference(ref)
        need(path.is_relative_to(detail) and path not in indexed, 'unique confined detailed artifact')
        indexed.add(path)
    need(indexed == {p for p in detail.rglob('*') if p.is_file()}, 'all detailed artifact bytes authenticated')
    phases = {phase: read(detail / (phase.upper() + '-TASKS.json.gz')) for phase in meta['completed_by_phase']}
    visits = {phase: set() for phase in phases}
    results, tasks, statuses, rss, seconds = {}, [], Counter(), [], []
    task_cpu = 0.0
    for ref in meta['results']:
        result = read(reference(ref))
        seed = result['seed']
        need(seed in SEEDS and seed not in results, 'distinct registered seed result')
        results[seed] = result
        need(datetime.fromisoformat(result['recorded_utc']) >= datetime.fromisoformat(frozen_time),
             'result follows implementation freeze')
        need(result['status'] == meta['status'] == attempt['status'], 'attempt dispositions agree')
        need(result['script_sha256'] == pins['sha256'] and
             result['preregistration_sha256'] == digest(preg_path.read_bytes()) and
             result['implementation_pins_sha256'] == digest(pins_path.read_bytes()) and
             result['control_addendum_sha256'] == digest(addendum_path.read_bytes()), 'RESULT exact scientific bindings')
        need(result['source_attribution'] == implementation['source_attribution'], 'complete source credits in each RESULT')
        credits(result, original)
        need(any(x.get('pr') == 3028 and x.get('author_login') == 'petalas' for x in result['source_attribution']),
             'Petalas comparison attribution')
        need(not result['decision']['pattern_claim'] and not result['decision']['kappa_claim'] and
             result['n_permutations'] == 0, 'finite census does not claim pattern or kappa admission')
        references(result.get('inputs', {}))
        for task_ref in result['task_receipts']:
            path = reference(task_ref)
            need(path in indexed, 'every RESULT task belongs to complete detailed inventory')
            phase = path.parent.name
            need(phase in phases, 'task belongs to launched phase')
            ordinal = int(path.name.split('.')[0].split('-')[-1])
            need(ordinal not in visits[phase] and 0 <= ordinal < len(phases[phase]), 'unique task address')
            visits[phase].add(ordinal)
            spec = phases[phase][ordinal]
            need(spec['seed'] == seed and spec['kind'] == phase, 'task phase and seed binding')
            receipt = read(path)
            statuses[receipt['status']] += 1
            rss.append(receipt.get('peak_rss_bytes') or 0)
            seconds.append(receipt.get('seconds') or 0)
            task_cpu += receipt.get('cpu_seconds') or 0
            if receipt['status'] == 'OK':
                value = receipt['result']
                need(value['seed'] == seed, 'task output seed')
                references(value)
                tasks.append((phase, spec, value, receipt))
            else:
                need(meta['failure'] is not None, 'infrastructure exception is not a scientific loss')
    need(set(results) == SEEDS, 'both distinct seed RESULTs')
    cpu = sum(x['cpu_seconds'] for x in results.values())
    need(abs(cpu - meta['total_cpu_seconds']) < 1e-5 and abs(cpu - attempt['cpu_seconds']) < 1e-5 and
         task_cpu <= cpu + 1e-5, 'scientific task and parent CPU accounted once')
    need(abs(meta['total_wall_seconds'] - attempt['wall_seconds']) < 1e-8, 'wall accounting')
    need(meta['workers'] == 61, 'central61-worker pool')
    for phase, seen in visits.items():
        need(len(seen) == meta['completed_by_phase'][phase], 'every completed task included once')
    projections = []
    for path in sorted(detail.glob('*MEMORY-PROJECTION.json')):
        value = read(path)
        need(value['workers'] == min(120, int(value['ram_gib']//4)) == 61 and
             value['reserved_cores'] >= 8 and value['worker_rss_cap_gib'] == 4 and
             value['projected_peak_gib'] < value['ram_gib'], 'worker, reserved-core and memory projection rules')
        projections.append(dict(path=str(path.relative_to(PKG)), sha256=digest(path.read_bytes()),
                                projected_peak_gib=value['projected_peak_gib']))
    need(len(projections) == len(phases) + 1, 'parent and every pool launch were projected')
    need(max(rss, default=0) <= 4*1024**3 and max(seconds, default=0) <= 301,
         'recorded4GiB RSS and300second task bounds')
    summary = dict(attempt=version, status=meta['status'], pool_tasks=sum(map(len, visits.values())),
                   completed_by_phase=meta['completed_by_phase'], pool_status_counts=dict(statuses),
                   cpu_seconds=cpu, worker_cpu_seconds=task_cpu, wall_seconds=meta['total_wall_seconds'],
                   max_worker_rss_bytes=max(rss, default=0), max_task_seconds=max(seconds, default=0),
                   source_archives=source_report, memory_projections=projections,
                   detailed_artifacts=len(indexed), detailed_bytes=sum(p.stat().st_size for p in indexed),
                   source_credits_per_result={str(s): len(v['source_attribution']) for s, v in results.items()})
    if meta['failure'] is not None:
        need(meta['status'] in {'ERROR', 'TIMEOUT'} and not meta['confirmed'], 'failed attempt preserved')
        summary['failure'] = meta['failure']
        return summary
    need(all(v['confirmed'] and v['scientific_decision_agreement'] and v['failure'] is None
             for v in results.values()) and meta['confirmed'], 'two-seed scientific decision agreement')
    expected = dict(controls=2, baseline=4, census=4, prices=256)
    if 'retention' in phases:
        expected['retention'] = len(phases['retention'])
        need(0 < expected['retention'] <= 32 and expected['retention'] % 4 == 0, 'bounded paired retention')
    need(meta['completed_by_phase'] == expected, 'complete registered phase coverage')
    controls = {}
    for phase, spec, value, _ in tasks:
        if phase in {'controls', 'baseline', 'census', 'prices'}:
            need(value['status'] == 'PASS', 'all primary controls and shards completed')
        if phase == 'controls':
            controls[str(spec['seed'])] = control_receipt(value, protocol)
        if phase == 'baseline':
            finite = value['local_admission']['audit']
            need(finite['checked_columns'] == finite['independent_inputs'] == 632 and
                 finite['orientations'] == {'forward': 'PASS', 'dual': 'PASS'} and
                 finite['restored_cold'] == finite['zero_buffers'] == 91,
                 'all632 baseline columns and91 restored buffers')
            need(value['word_source_declared_physical_families'] == 66813 and
                 value['comparison_source_declared_physical_families'] == 133117 and
                 value['comparison_replicas'] == 148 and value['fresh_native_physical_outer'] is False,
                 'baseline distinguishes word-source and comparison stock')
    for phase, seen in visits.items():
        need(seen == set(range(len(phases[phase]))), 'no omitted task in completed phase')
    for seed, result in results.items():
        need(result['statistics'] == meta['statistics'][str(seed)], 'RUN/RESULT statistics equality')
    need(clean(results[min(SEEDS)]['statistics']) == clean(results[max(SEEDS)]['statistics']),
         'two-seed aggregate statistics equality')
    for phase in ('controls', 'baseline'):
        groups = {}
        for actual_phase, spec, value, _ in tasks:
            if actual_phase == phase:
                groups.setdefault(spec.get('provider', 'all'), []).append(value)
        need(all(len(v) == 2 and clean(v[0]) == clean(v[1]) for v in groups.values()),
             'saved controls and baseline checks agree across seeds')
    summary['controls'] = controls
    summary['domain'] = saved_domain(tasks, results, protocol, meta, run)
    return summary


def build_audit():
    CHECKED_REFS.clear()
    registry = read(ROUND / 'EXPERIMENTS.json')
    task = read(ROUND / 'TASK.json')
    need(task['base_work_commit'] == BASE and registry['no_active_experiments'], 'closed pools and exact base')
    need('RUNNING' not in registry['status'].upper(), 'closed registry before final audit')
    original = read(PKG / 'data/words/PINS.json')['files']
    need(len(original) == 21, 'all original source credits')
    row = next(x for x in registry['experiments'] if x['id'] == FAMILY)
    need(row['execution'] in {'COMPLETED', 'INCOMPLETE'} and
         row['status'] in {'PASS', 'NULL', 'EXPLORATORY', 'ERROR', 'TIMEOUT'}, 'final scoped disposition')
    preg = ROUND / 'J1/PREREGISTRATION.json'
    need(row['preregistration_sha256'] == digest(preg.read_bytes()), 'registry preregistration pin')
    reports = [audit_attempt(row, attempt, original) for attempt in row['attempts']]
    need(abs(sum(x['cpu_seconds'] for x in reports) - row['cpu_seconds']) < 1e-5,
         'scientific attempts counted once')
    need(row['status'] == reports[-1]['status'] and row['cpu_seconds'] < task['round_cpu_budget_seconds'],
         'final attempt and round CPU budget')
    protocol = read(preg)
    acquisitions = [acquisition(ref) for name, ref in protocol['inputs'].items() if name.endswith('_acquisition')]
    preserved = preserved_base()
    documents = {name: digest((ROUND/name).read_bytes()) for name in
                 ('RESULTS.md', 'HANDBACK.md', 'PREDICTIONS.json', 'EXPERIMENTS.json', 'TASK.json')}
    checkpoints = {}
    for label in ('checkpoint', 'final_checkpoint', 'final-checkpoint'):
        path = DATA / label / 'RECEIPT.json'
        if not path.exists():
            need(label != 'checkpoint', 'initial checkpoint exists')
            continue
        receipt = read(path)
        need(not receipt['errors'], 'source checkpoint reports no suppressed errors')
        for relative, pin in receipt['files'].items():
            need(digest((path.parent/relative).read_bytes()) == pin['sha256'], 'checkpoint exact saved bytes')
        checkpoints[label] = dict(sha256=digest(path.read_bytes()), canonical_main=receipt['canonical_main'],
                                  priority_revision=receipt['priority_revision'], files=len(receipt['files']))
    destination = ROUND / 'AUDIT.json'
    sizes = {name: sum(p.stat().st_size for p in path.rglob('*') if p.is_file() and p != destination)
             for name, path in (('global_results', PKG/'results'), ('round_results', ROUND),
                                ('new_data', DATA), ('new_pipeline', Path(__file__).parent))}
    need(sizes['global_results'] < 200000000 and sizes['round_results'] < 2000000 and
         sizes['round_results'] + sizes['new_data'] + sizes['new_pipeline'] < 100000000,
         'global200MB, round2MB and all-new-evidence100MB caps')
    return dict(schema_version=1, status='PASS', kind='Administrative saved-byte audit; no scientific reruns',
                script_sha256=digest(Path(__file__).read_bytes()), base_work_commit=BASE,
                preserved_pre_round_files=preserved, experiments={FAMILY: reports},
                total_pool_tasks=sum(x['pool_tasks'] for x in reports),
                total_experimental_cpu_seconds=sum(x['cpu_seconds'] for x in reports),
                acquisitions=acquisitions, source_checkpoints=checkpoints, final_documents=documents,
                local_artifact_references_checked=len(CHECKED_REFS), storage_bytes_excluding_audit=sizes)


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
    sizes = stable['storage_bytes_excluding_audit']
    need(sizes['global_results']+len(raw) < 200000000 and sizes['round_results']+len(raw) < 2000000 and
         sizes['round_results']+sizes['new_data']+sizes['new_pipeline']+len(raw) < 100000000,
         'all storage caps include final audit bytes')
    if args.write:
        with path.open('xb') as stream:
            stream.write(raw)
    print(json.dumps(value, sort_keys=True))


if __name__ == '__main__':
    main()

