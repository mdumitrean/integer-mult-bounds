"""Administrative verification of immutable S3 outputs; standard library only.

This does not import scientific modules, enumerate source candidates, recompute
child costs, or run a control/experiment. It checks saved evidence and bindings.
"""
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import gzip
import hashlib
import json
import math
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
DATA = PKG / 'data/continuation-14'
RUN_DIR = DATA / 's3-v1'
ROUND = PKG / 'results/CONTINUATION-14'
SEEDS = (74017, 148027)
PROVIDERS = ('base', 'extra')
CLASSES = ('FORWARD_MATCHED', 'FORWARD_SPLIT', 'REVERSE_MATCHED', 'REVERSE_SPLIT')
checks = Counter()
failures = []
files = {}
start_cpu, start_wall = time.process_time(), time.monotonic()


def check(name, okay, context=None):
    checks[name] += 1
    if not okay:
        failures.append(dict(check=name, context=context))


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.name.endswith('.gz') else raw)


def ref(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(PKG)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def verify(reference):
    path = (PKG / reference['path']).resolve()
    check('reference_confinement', path.is_relative_to(PKG), reference['path'])
    if str(path) not in files:
        raw = path.read_bytes()
        files[str(path)] = dict(path=str(path.relative_to(PKG)), bytes=len(raw),
                               sha256=hashlib.sha256(raw).hexdigest())
    observed = files[str(path)]
    check('reference_sha256', observed['sha256'] == reference['sha256'], reference['path'])
    if 'bytes' in reference:
        check('reference_bytes', observed['bytes'] == reference['bytes'], reference['path'])
    if 'payload_sha256' in reference:
        raw = path.read_bytes()
        payload = gzip.decompress(raw) if path.name.endswith('.gz') else raw
        check('reference_payload_sha256', hashlib.sha256(payload).hexdigest() == reference['payload_sha256'], reference['path'])
    return path


def clean(value):
    if isinstance(value, list):
        return [clean(x) for x in value]
    if isinstance(value, dict):
        ignored = {'seed', 'cpu_seconds', 'wall_seconds', 'elapsed_seconds', 'seconds',
                   'recorded_utc', 'output_dir', 'schedule'}
        result = {k: clean(v) for k, v in value.items() if k not in ignored}
        if 'path' in result and 'sha256' in result:
            result['path'] = '<separate-artifact-path-with-identical-bytes>'
        return result
    return value


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-11, abs_tol=1e-6)


run_path = RUN_DIR / 'RUN.json'
run = read(run_path)
registration_path = ROUND / 'S3/PREREGISTRATION.json'
protocol = read(registration_path)
manifest_path = verify(protocol['initial_implementation_pins'])
manifest = read(manifest_path)
registration_sha = ref(registration_path)['sha256']
check('frozen_registration', protocol['state'] == 'FROZEN')
check('fixed_seeds', protocol['seeds'] == list(SEEDS))
check('fixed_label_and_shard_domain', protocol['domain']['labels_per_carrier_anchor'] == 80 and
      protocol['shards_per_provider'] == 192)
check('complete_confirmed_null', run['status'] == 'NULL' and run['confirmed'] and
      run['failure'] is None and run['incomplete_phase'] is None)
for name, reference in protocol['inputs'].items():
    verify(reference)
source_rows = []
for name, expected in manifest['sha256'].items():
    path = ROOT / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    check('current_frozen_source_sha256', actual == expected, name)
    archive = verify(manifest['archives'][expected])
    archived = hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest()
    check('archived_frozen_source_sha256', archived == expected, name)
    source_rows.append(dict(path=name, sha256=expected, current_matches=actual == expected,
                            archive_matches=archived == expected))
implementation = read(RUN_DIR / 'IMPLEMENTATION.json')
check('implementation_manifest_binding', implementation['script_sha256'] == manifest['sha256'] and
      implementation['implementation_pins_sha256'] == protocol['initial_implementation_pins']['sha256'] and
      implementation['preregistration_sha256'] == registration_sha)
for reference in run['detailed_evidence']:
    verify(reference)
results = [read(verify(r)) for r in run['results']]
check('one_result_each_seed', sorted(r['seed'] for r in results) == sorted(SEEDS))
for result in results:
    check('result_registration_source_bindings', result['preregistration_sha256'] == registration_sha and
          result['implementation_pins_sha256'] == protocol['initial_implementation_pins']['sha256'] and
          result['script_sha256'] == manifest['sha256']['research/styles-r11/pipeline/continuation14/run_split.py'])
    check('result_complete_decision', result['status'] == 'NULL' and result['confirmed'] and
          result['scientific_decision_agreement'] and result['failure'] is None)
    check('result_scope_no_claim', not result['decision']['pattern_claim'] and not result['decision']['kappa_claim'])
    check('result_original_attribution_retained', bool(result['source_attribution']) and bool(result['word_blob_ids']))
    provenance = read(verify(result['provenance']))
    check('provenance_input_equality', provenance == implementation['provenance'])
    check('result_statistics_run_binding', result['statistics'] == run['statistics'][str(result['seed'])])
check('result_seed_statistics_agree', clean(results[0]['statistics']) == clean(results[1]['statistics']))
check('result_cpu_sums_to_run', close(sum(r['cpu_seconds'] for r in results), run['total_cpu_seconds']))

task_entries = {}
for result in results:
    task_manifest = read(verify(result['task_manifest']))
    for entry in task_manifest:
        path = verify(entry['artifact'])
        check('unique_task_manifest_reference', str(path) not in task_entries, str(path))
        task_entries[str(path)] = entry
expected_phases = {'controls': 2, 'baseline': 4, 'census': 4, 'prices': 768}
phase_specs = {}
task_index = {}
task_summaries = []
for phase, count in expected_phases.items():
    specs = read(RUN_DIR / (phase.upper() + '-TASKS.json.gz'))
    phase_specs[phase] = specs
    check('phase_expected_task_count', len(specs) == count == run['completed_by_phase'][phase], phase)
    check('phase_receipt_file_count', len(list((RUN_DIR / phase).glob('task-*.json.gz'))) == count, phase)
    for index, spec in enumerate(specs):
        path = RUN_DIR / phase / ('task-%05d.json.gz' % index)
        entry = task_entries[str(path)]
        check('task_spec_manifest_binding', entry['spec'] == spec, str(path))
        item = read(path)
        check('task_completed_ok', item['status'] == 'OK', str(path))
        check('task_resource_limits', 0 <= item['cpu_seconds'] and 0 <= item['seconds'] <= protocol['resources']['timeout_seconds'] and
              0 < item['peak_rss_bytes'] <= protocol['resources']['rss_gib'] * (1 << 30), str(path))
        key = (phase, spec['seed'], spec.get('provider'), spec.get('shard'))
        check('unique_task_coordinate', key not in task_index, key)
        task_index[key] = path
        check('task_seed_provider_binding', item['result']['seed'] == spec['seed'] and
              (not spec.get('provider') or item['result']['provider'] == spec['provider']), str(path))
        task_summaries.append(dict(path=str(path.relative_to(PKG)), phase=phase, seed=spec['seed'],
                                   provider=spec.get('provider'), shard=spec.get('shard'),
                                   status=item['status'], cpu_seconds=item['cpu_seconds'],
                                   wall_seconds=item['seconds'], peak_rss_bytes=item['peak_rss_bytes']))
check('all_tasks_exactly_manifested', len(task_index) == len(task_entries) == sum(expected_phases.values()))
control_results = [read(task_index['controls', seed, None, None])['result'] for seed in SEEDS]
check('controls_status_and_equality', all(r['status'] == 'PASS' for r in control_results) and
      clean(control_results[0]) == clean(control_results[1]))
check('control_totals_reconcile', all(sum(r['checks_by_family'].values()) == r['checks'] for r in control_results))
baseline_summary = {}
for provider in PROVIDERS:
    twins = [read(task_index['baseline', seed, provider, None])['result'] for seed in SEEDS]
    check('baseline_seed_equality', all(r['status'] == 'PASS' for r in twins) and clean(twins[0]) == clean(twins[1]), provider)
    baseline_summary[provider] = clean(twins[0])

outcomes = {}
descriptive = {}
source_attribution = {}
scientific_shard_hashes = []
for provider in PROVIDERS:
    census_twins = [read(task_index['census', seed, provider, None])['result'] for seed in SEEDS]
    check('census_seed_equality', clean(census_twins[0]) == clean(census_twins[1]), provider)
    census = census_twins[0]
    del census_twins
    source_attribution[provider] = census['source_attribution']
    source_path = verify(census['source_pin'])
    check('source_semantic_binding', digest(read(source_path)) == census['parent_semantic_sha256'], provider)
    domain, plans, counts = census['candidates'], census['plans'], census['counts']
    for key in ('plans', 'exclusions'):
        check('census_collection_hash', digest(census[key]) == census[key + '_sha256'], (provider, key))
    check('census_domain_hash', digest(domain) == census['domain_sha256'] == census['candidate_set_sha256'], provider)
    check('census_complete', census['status'] == 'PASS' and census['complete'], provider)
    check('packet_placement_coverage', counts['placements_considered'] == 2 * counts['source_packets'] and
          counts['placements_considered'] == counts['commuting_placements'] + counts['noncommuting_placements'] +
          counts['scalar_precondition_rejected_placements'], provider)
    check('ratio_choice_coverage', counts['admissible_carrier_anchor_choices'] + counts['ratio_rejected_carrier_anchor_choices'] ==
          4 * counts['commuting_placements'], provider)
    check('eighty_labels_each_choice', len(domain) == counts['candidates'] == 80 * counts['admissible_carrier_anchor_choices'], provider)
    check('plan_ordinal_coverage', len(plans) == counts['commuting_placements'] and
          sorted(p['plan_ordinal'] for p in plans.values()) == list(range(len(plans))), provider)
    check('exclusion_inventory', len(census['exclusions']) == counts['noncommuting_placements'] +
          counts['scalar_precondition_rejected_placements'] + counts['ratio_rejected_carrier_anchor_choices'], provider)
    check('declared_domain_caps', counts['source_packets'] <= protocol['domain']['maximum_structural_packets_per_provider'] and
          len(domain) <= protocol['domain']['maximum_labels_per_provider'], provider)
    for plan_id, plan in plans.items():
        check('plan_identity_source_binding', plan_id == plan['plan_id'] == digest(dict(
              parent_semantic_sha256=census['parent_semantic_sha256'], address=plan['address'])), provider)
        check('saved_crossing_hash', digest(plan['crossings']) == plan['crossings_sha256'], plan_id)
    check('unique_candidate_ids', len({r['candidate_id'] for r in domain}) == len(domain), provider)
    choices = defaultdict(set)
    for ordinal, candidate in enumerate(domain):
        address = candidate['address']
        check('candidate_literal_id', candidate['candidate_id'] == candidate['pair_key'] == '.'.join(map(str, address)), ordinal)
        check('candidate_class_corner_binding', len(address) == 10 and 0 <= address[-1] < 80 and
              candidate['frame_class'] == CLASSES[address[-1] // 20] and
              candidate['production_order'] == ('carrier_first' if address[-1] < 40 else 'reverse_chain'), ordinal)
        plan = plans[candidate['plan_id']]
        check('candidate_plan_binding', candidate['plan_ordinal'] == plan['plan_ordinal'] and address[:7] == plan['address'], ordinal)
        choices[tuple(address[:-1])].add(address[-1])
    check('all_choice_corner_sets', len(choices) == counts['admissible_carrier_anchor_choices'] and
          all(c == set(range(80)) for c in choices.values()), provider)
    coverage = {seed: bytearray(len(domain)) for seed in SEEDS}
    totals = {seed: Counter() for seed in SEEDS}
    summaries = {seed: defaultdict(Counter) for seed in SEEDS}
    for shard in range(192):
        pair = [read(task_index['prices', seed, provider, shard])['result'] for seed in SEEDS]
        check('price_seed_equality', clean(pair[0]) == clean(pair[1]), (provider, shard))
        scientific_shard_hashes.append(dict(provider=provider, shard=shard,
                                             sha256=digest(clean(pair[0]))))
        for seed, result in zip(SEEDS, pair):
            check('shard_complete_and_bound', result['status'] == 'PASS' and result['complete'] and result['shards'] == 192 and
                  result['domain_sha256'] == census['domain_sha256'] and result['plans_sha256'] == census['plans_sha256'] and
                  result['parent_semantic_sha256'] == census['parent_semantic_sha256'], (provider, seed, shard))
            check('no_new_primitive_admission', result['primitive_cost_included'] is False and result['canonical_full_words_built'] == 0)
            for key in ('tariff_certificates', 'guard_certificates', 'window_certificates'):
                check('certificate_collection_hash', digest(result[key]) == result[key + '_sha256'], (provider, seed, shard, key))
            check('row_collection_hash', digest(result['rows']) == result['shard_rows_sha256'], (provider, seed, shard))
            saved_intervals = {}
            for ident, cert in result['tariff_certificates'].items():
                check('individual_tariff_hash', digest(cert) == ident)
                delta, moment = cert['profile_delta'], cert['moment_delta']
                check('complete_delta_mass', all(0 < int(rank) <= 9 and type(n) is int for rank, n in delta.items()) and
                      sum(int(rank) * n for rank, n in delta.items()) == 0)
                lower, upper = Fraction(moment['lower']), Fraction(moment['upper'])
                check('saved_moment_interval', lower <= upper and moment['endpoint'] == protocol['comparison']['complex_endpoint'])
                if not delta:
                    check('exact_profile_zero_interval', lower == upper == 0 and moment['exact_profile_identity'])
                expected = 'PASS_CANDIDATE' if upper < 0 else 'NO_GAIN' if not delta or lower >= 0 else 'EXPLORATORY'
                saved_intervals[ident] = (expected, 'identity' if not delta else 'strictly_costlier' if lower > 0 else 'nonnegative',
                                           tuple(sorted((int(k), v) for k, v in delta.items())))
            for ident, cert in result['guard_certificates'].items():
                check('individual_guard_hash', bool(cert) and digest(cert) == ident)
            used_tariffs, used_guards, used_plans = set(), set(), set()
            tally = Counter()
            for row in result['rows']:
                ordinal = row['ordinal']
                check('ordinal_range', 0 <= ordinal < len(domain))
                candidate = domain[ordinal]
                check('unique_exhaustive_shard_membership', not coverage[seed][ordinal] and
                      candidate['plan_ordinal'] % 192 == shard, (provider, seed, ordinal))
                coverage[seed][ordinal] = 1
                check('row_candidate_binding', all(row[k] == candidate[k] for k in
                      ('candidate_id', 'plan_id', 'plan_ordinal', 'frame_class')), (provider, seed, ordinal))
                used_plans.add(row['plan_id'])
                if row['status'] == 'REJECTED_GUARD':
                    used_guards.add(row['failure_id'])
                    check('row_guard_reference', row['failure_id'] in result['guard_certificates'])
                    disposition = 'guard_rejected'
                    delta = ()
                else:
                    ident = row['tariff_id']
                    used_tariffs.add(ident)
                    expected, disposition, delta = saved_intervals[ident]
                    check('row_saved_interval_disposition', row['status'] == expected)
                tally[row['status']] += 1
                tally[row['frame_class']] += 1
                summaries[seed][row['frame_class']][disposition] += 1
                if delta:
                    summaries[seed]['profile_deltas'][str(delta)] += 1
                section, placement = candidate['address'][0], candidate['address'][6]
                summaries[seed]['section_placement'][f'{section}:{placement}:{disposition}'] += 1
            check('all_shard_certificates_referenced', used_tariffs == set(result['tariff_certificates']) and
                  used_guards == set(result['guard_certificates']) and used_plans == set(result['window_certificates']))
            for plan_id, cert in result['window_certificates'].items():
                check('window_full_boundary_hash', digest(cert['whole_window_boundaries']) == cert['whole_window_boundaries_sha256'])
                check('window_source_plan_binding', cert['interval_sha256'] == plans[plan_id]['interval_sha256'] and
                      cert['crossings_sha256'] == plans[plan_id]['crossings_sha256'])
                check('saved_window_bills_valid', cert['original_window_bill']['valid'] and cert['fixed_contact_bill']['valid'])
            for key in (*CLASSES, 'PASS_CANDIDATE', 'NO_GAIN', 'REJECTED_GUARD', 'EXPLORATORY'):
                check('shard_count_reconciliation', tally[key] == result['counts'][key], (provider, seed, shard, key))
            check('shard_row_plan_counts', len(result['rows']) == result['counts']['candidates'] and
                  len(used_plans) == result['counts']['plans'])
            check('no_favorable_rows_hidden', len(result['favorable']) == tally['PASS_CANDIDATE'] == 0)
            totals[seed].update(result['counts'])
    for seed in SEEDS:
        check('all_domain_ordinals_once', all(coverage[seed]) and sum(coverage[seed]) == len(domain), (provider, seed))
        check('run_counts_from_independent_rows', dict(totals[seed]) == run['statistics'][str(seed)]['counts_by_provider'][provider], (provider, seed))
        check('complete_null_disposition', totals[seed]['NO_GAIN'] == len(domain) and
              totals[seed]['PASS_CANDIDATE'] == totals[seed]['EXPLORATORY'] == totals[seed]['REJECTED_GUARD'] == 0)
    check('descriptive_two_seed_equality', summaries[SEEDS[0]] == summaries[SEEDS[1]], provider)
    outcomes[provider] = dict(census=counts, rows_each_seed=dict(totals[SEEDS[0]]))
    descriptive[provider] = {k: dict(v) for k, v in summaries[SEEDS[0]].items()}

resource_summary = {}
for phase in expected_phases:
    projection = read(RUN_DIR / (phase.upper() + '-MEMORY-PROJECTION.json'))
    metric = run['phase_metrics'][phase]
    own = [r for r in task_summaries if r['phase'] == phase]
    check('phase_workers_projection', metric['workers'] == projection['workers'] <= min(120, len(own)), phase)
    check('reserved_cpu_cores', projection['reserved_cores'] == 8 and projection['allocated_cores'] == 128)
    check('memory_projection_formula', close(projection['reserved_per_worker_gib'], 1.2 * max(
          projection['estimated_worker_rss_gib'], projection['parent_current_rss_gib'])) and
          projection['projected_increment_gib'] <= projection['memory']['available_bytes'] / (1 << 30) - 16)
    check('hard_worker_rss_cap', projection['worker_rss_cap_gib'] == 4 and projection['reserved_per_worker_gib'] < 4)
    trace = [json.loads(line) for line in (RUN_DIR / (phase.upper() + '-RESOURCE-TRACE.jsonl')).read_text().splitlines()]
    check('resource_trace_present', bool(trace), phase)
    check('trace_memory_and_worker_caps', all(r['memory']['available_bytes'] >= 16 * (1 << 30) and
          r['maximum_worker_rss_bytes'] <= 4 * (1 << 30) and
          0 <= r['running_workers'] <= r['live_workers'] <= projection['workers'] for r in trace), phase)
    check('phase_cpu_average_reconciles', close(metric['average_core_equivalents'], metric['cpu_seconds'] / metric['wall_seconds']))
    check('task_cpu_within_phase_total', sum(r['cpu_seconds'] for r in own) <= metric['cpu_seconds'] + 1e-6, phase)
    resource_summary[phase] = dict(metric, task_cpu_seconds=sum(r['cpu_seconds'] for r in own),
        task_max_rss_bytes=max(r['peak_rss_bytes'] for r in own),
        trace_samples=len(trace), maximum_sampled_live_workers=max(r['live_workers'] for r in trace),
        maximum_sampled_running_workers=max(r['running_workers'] for r in trace),
        minimum_sampled_available_gib=min(r['memory']['available_bytes'] for r in trace) / (1 << 30),
        maximum_sampled_worker_rss_mib=max(r['maximum_worker_rss_bytes'] for r in trace) / (1 << 20),
        projection_reserved_per_worker_gib=projection['reserved_per_worker_gib'],
        projection_increment_gib=projection['projected_increment_gib'])
check('scientific_cpu_budget', run['total_cpu_seconds'] <= protocol['resources']['cpu_budget_seconds_family'])
check('phase_cpu_within_run_total', sum(v['cpu_seconds'] for v in run['phase_metrics'].values()) <= run['total_cpu_seconds'] + 1e-6)
check('all_expected_phases_only', run['completed_by_phase'] == expected_phases)
selection = read(ROUND / protocol['experiment'] / 'v1/SELECTION.json')
check('zero_selection', selection['paired_favorable'] == 0 and selection['selected_pair_keys'] == [] and
      all(v == 0 for v in selection['favorable_by_provider'].values()))
check('no_retention_or_candidate_claim', 'retention' not in run['completed_by_phase'] and
      all(s['retained_provider_words'] == 0 and not s['kappa_claim'] and not s['pattern_claim'] for s in run['statistics'].values()))

detail_path = DATA / 'S3-SAVED-EVIDENCE-AUDIT.json'
compact_path = ROUND / 'AUDIT.json'
detail = dict(schema_version=1, status='PASS' if not failures else 'FAIL',
    audit_kind='Saved-evidence administrative verification; no scientific module imports or experimental reruns',
    recorded_utc=datetime.now(timezone.utc).isoformat(), auditor_script=ref(Path(__file__)),
    run=ref(run_path), registration=ref(registration_path), implementation_manifest=ref(manifest_path),
    checks=sum(checks.values()), checks_by_category=dict(checks), failures=failures,
    authenticated_files=list(sorted(files.values(), key=lambda r: r['path'])), frozen_sources=source_rows,
    task_summary=task_summaries, scientific_shard_hashes=scientific_shard_hashes,
    source_attribution=source_attribution, controls_each_seed=control_results[0]['checks'],
    controls_by_category=control_results[0]['checks_by_family'], baseline_summary=baseline_summary,
    outcomes=outcomes, descriptive_saved_rows=descriptive, resource_summary=resource_summary,
    compute=dict(scientific_cpu_seconds=run['total_cpu_seconds'], scientific_wall_seconds=run['total_wall_seconds'],
                 scientific_cpu_includes='parent and reaped workers through the end of scientific phases',
                 audit_cpu_seconds=time.process_time()-start_cpu, audit_wall_seconds=time.monotonic()-start_wall),
    limits=['Hashes, partitions, stored rational-interval dispositions and seed agreement independently checked.',
            'The child-cost interval derivation, scalar commutation census and finite-frame optimizer were not rerun.',
            'Duplicate corner labels and repeated executions are not independent examples.',
            'The NULL covers only the pinned finite packet, stable-gather and two ordered-chain frame domain.',
            'No changed word was retained; native, supplier and outer admission were not run for a candidate.',
            'Resource samples are sequential; phase CPU/wall is an aggregate core-equivalent measure.'])
with detail_path.open('x') as stream:
    json.dump(detail, stream, sort_keys=True, separators=(',', ':')); stream.write('\n')
compact = dict(schema_version=1, status=detail['status'], audit_kind=detail['audit_kind'],
    recorded_utc=detail['recorded_utc'], run=ref(run_path), registration=ref(registration_path),
    implementation_manifest=ref(manifest_path), detailed_audit=ref(detail_path),
    checks=detail['checks'], failures=failures, distinct_authenticated_files=len(files),
    frozen_source_files=len(source_rows), task_receipts=len(task_summaries), pricing_shards=768,
    labels_per_provider_seed=184640, total_execution_rows=4*184640,
    controls_each_seed=control_results[0]['checks'], confirmed_status='NULL',
    source_attribution=source_attribution, outcomes=outcomes, resource_summary=resource_summary,
    scientific_cpu_seconds=run['total_cpu_seconds'], scientific_wall_seconds=run['total_wall_seconds'],
    audit_cpu_seconds=detail['compute']['audit_cpu_seconds'], scope_limits=detail['limits'])
encoded = (json.dumps(compact, sort_keys=True, separators=(',', ':')) + '\n').encode()
round_bytes = sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file())
global_bytes = sum(p.stat().st_size for p in (PKG / 'results').rglob('*') if p.is_file())
if round_bytes + len(encoded) >= protocol['resources']['new_result_bytes_cap'] or global_bytes + len(encoded) >= protocol['resources']['result_bytes_cap']:
    raise RuntimeError('compact administrative audit would exceed registered results cap')
with compact_path.open('xb') as stream:
    stream.write(encoded)
print(json.dumps(dict(status=detail['status'], checks=detail['checks'], failures=failures,
                     compact=ref(compact_path), detailed=ref(detail_path),
                     controls_each_seed=control_results[0]['checks'], outcomes=descriptive,
                     resources=resource_summary, audit_cpu_seconds=detail['compute']['audit_cpu_seconds'])))
