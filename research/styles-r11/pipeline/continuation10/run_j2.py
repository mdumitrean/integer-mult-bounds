"""Registered exact commuting shared-carrier census; one bounded central pool at a time."""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import os
import resource
import sys
import time
import traceback

sys.dont_write_bytecode = True
for key in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS',
            'NUMEXPR_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'):
    os.environ[key] = '1'
HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-10'
SEEDS = (53017, 106013)
S = M = P = None
STATE = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime


def write(path, value, immutable=True):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()
    packed = gzip.compress(raw, mtime=0) if path.name.endswith('.gz') else raw
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb' if immutable else 'wb') as stream:
        stream.write(packed)
    return dict(path=str(path.relative_to(PKG)), sha256=sha(path), bytes=len(packed),
                payload_sha256=hashlib.sha256(raw).hexdigest())


def clean(value):
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, dict):
        ignored = {'seed', 'cpu_seconds', 'wall_seconds', 'elapsed_seconds', 'seconds',
                   'recorded_utc', 'output_dir', 'schedule'}
        out = {k: clean(v) for k, v in value.items() if k not in ignored}
        if 'path' in out and 'sha256' in out:
            out['path'] = '<separate-artifact-path-with-identical-bytes>'
        return out
    return value


def worker(spec):
    kind = spec['kind']
    if kind == 'controls':
        return M.controls_task(spec)
    if kind == 'baseline':
        return S.baseline_task(spec)
    if kind == 'census':
        return M.census_task(spec)
    if kind == 'prices':
        return M.shard_task(spec)
    if kind == 'retention':
        result = M.validate_selected(spec)
        need(result['status'] == 'PASS_CANDIDATE', 'retained canonical word construction')
        ref = result['word']
        path = (PKG / ref['path']).resolve()
        need(path.is_relative_to(PKG / 'data/continuation-10/candidates'), 'candidate confinement')
        need(sha(path) == ref['sha256'], 'retained exact word bytes')
        raw = json.loads(gzip.decompress(path.read_bytes()))
        W, A = S._SOURCE._modules()
        attribution = STATE['records'][spec['provider']]['attribution']
        audit = A.local_admission(raw, attribution)
        need(audit['status'] == 'PASS' and audit['audit']['checked_columns'] == 632 and
             audit['audit']['orientations'] == {'forward': 'PASS', 'dual': 'PASS'},
             'retained full632-column forward and dual audit')
        rejected = {}
        for name in ('wrong_scalar', 'omitted_paid_child', 'omitted_cleanup'):
            wrong = deepcopy(raw)
            if name == 'wrong_scalar':
                gate = next(g for g in wrong['A'][int(wrong.get('prelude_events', 0)):] if g[0] == 'add')
                gate[3] *= -1
            elif name == 'omitted_paid_child':
                profile = wrong['report']['local_profile']
                rank = min((r for r in profile if profile[r] > 0), key=int)
                profile[rank] -= 1
            else:
                need(wrong['cleanup'], 'nonempty inverse cleanup')
                wrong['cleanup'].pop()
            try:
                A.local_admission(wrong, attribution)
            except (AssertionError, ValueError):
                rejected[name] = True
            else:
                rejected[name] = False
            need(rejected[name], 'retained semantic mutation must reject: ' + name)
        result['independent_local_admission'] = audit
        result['independent_rejecting_controls'] = rejected
        result['fresh_native_admission'] = 'UNRUN_REQUIRED'
        result['complete_supplier_outer_admission'] = 'UNRUN_REQUIRED'
        result['kappa_claim'] = False
        return result
    raise ValueError('Unregistered worker kind: ' + kind)


def main():
    global S, M, P, STATE
    parser = argparse.ArgumentParser()
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--attempt', default='v1')
    args = parser.parse_args()
    need(sys.flags.isolated and not sys.flags.optimize, 'isolated Python with assertions')
    need(sys.pycache_prefix and not Path(sys.pycache_prefix).exists(), 'fresh unused bytecode namespace')
    preg = ROUND / 'J2/PREREGISTRATION.json'
    protocol = json.loads(preg.read_text())
    need(sha(preg) == args.registration_sha256 and protocol['state'] == 'FROZEN', 'frozen preregistration')
    need(tuple(protocol['seeds']) == SEEDS, 'two fixed seeds')
    pins_path = ROUND / 'J2' / ('IMPLEMENTATION-PINS-' + args.attempt + '.json')
    pin_record = json.loads(pins_path.read_text())
    pins = pin_record['sha256']
    for name, expected in pins.items():
        need(sha(ROOT / name) == expected, 'source pin before imports: ' + name)
    need(str(Path(__file__).relative_to(ROOT)) in pins, 'runner is frozen')
    sys.path[:0] = [str(HERE), str(HERE.parent)]
    import source_inputs as S
    import commuting_carrier as M
    import pool as P
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(r for r in registry['experiments'] if r['id'] == protocol['experiment'])
    need(registry['no_active_experiments'], 'one scientific pool')
    need(row['status'] == 'planned' or row.get('execution') == 'INCOMPLETE', 'new or registered mechanical repair')
    run = ROUND / protocol['experiment'] / args.attempt
    run.mkdir(parents=True, exist_ok=False)
    data_run = PKG / 'data/continuation-10' / ('j2-' + args.attempt)
    data_run.mkdir(parents=True, exist_ok=False)
    row.update(status='running', execution='RUNNING', started_utc=now())
    registry['no_active_experiments'] = False
    write(registry_path, registry, False)
    started_cpu, started_wall = cpu(), time.monotonic()
    prior_cpu = sum(r.get('cpu_seconds', 0) for r in registry['experiments'])
    observed, prepared, statistics = {}, {}, {}
    failure = None
    status, phase, agreement = 'EXPLORATORY', None, False
    original = json.loads((PKG / 'data/words/PINS.json').read_bytes())['files']
    attribution = [dict(path=k, **v) for k, v in original.items()]
    provenance = {}

    def deadline():
        if datetime.now(timezone.utc) >= datetime.fromisoformat(protocol['science_launch_cutoff_utc']):
            raise TimeoutError('registered science launch cutoff')
        remaining = min(protocol['resources']['cpu_budget_seconds_family'] - (cpu() - started_cpu),
                        protocol['resources']['round_cpu_budget_seconds'] - prior_cpu - (cpu() - started_cpu))
        if remaining <= 0:
            raise TimeoutError('registered scientific CPU budget')
        return remaining

    def storage(reserve_results=0):
        sizes = {name: sum(p.stat().st_size for p in path.rglob('*') if p.is_file())
                 for name, path in (('round', ROUND), ('global_results', PKG / 'results'),
                                    ('new_data', PKG / 'data/continuation-10'),
                                    ('new_pipeline', HERE))}
        caps = protocol['resources']
        need(sizes['round'] + reserve_results < caps['round_new_results_bytes_cap'], 'round results1.5MB cap with close reserve')
        need(sizes['global_results'] + reserve_results < caps['global_results_bytes_cap'], 'global results200MB cap with close reserve')
        need(sizes['round'] + sizes['new_data'] + sizes['new_pipeline'] + reserve_results < caps['new_evidence_bytes_cap'], 'registered total new evidence256MB cap')
        return sizes

    def launch(name, specs):
        nonlocal phase
        phase = name
        remaining = deadline()
        storage(400000)
        observed[name] = {}
        write(data_run / (name.upper() + '-TASKS.json.gz'), specs)

        def checkpoint(index, item):
            ref = write(data_run / name / ('task-%05d.json.gz' % index), item)
            observed[name][index] = dict(spec=specs[index], item=item, artifact=ref)
            write(data_run / 'BUDGET-CHECKPOINT.json', dict(recorded_utc=now(), phase=name,
                parent_and_reaped_cpu_seconds=cpu() - started_cpu,
                completed={k: len(v) for k, v in observed.items()}), False)
            if len(specs) < 20 or len(observed[name]) % 32 == 0 or len(observed[name]) == len(specs):
                print(json.dumps(dict(phase=name, completed=len(observed[name]), total=len(specs),
                                      status=item['status'])), flush=True)
        P.run_pool(worker, [(s,) for s in specs], workers=P.worker_count(), timeout=300, rss_gib=4,
                   working_set_gib=protocol['resources']['working_set_gib'], projection_path=data_run / (name.upper() + '-MEMORY-PROJECTION.json'),
                   on_result=checkpoint, cpu_budget_seconds=remaining)
        items = [observed[name][i]['item'] for i in range(len(specs))]
        if any(x['status'] == 'TIMEOUT' for x in items):
            raise TimeoutError(name + ' task timeout')
        need(all(x['status'] == 'OK' for x in items), name + ' failed tasks: ' +
             repr([x for x in items if x['status'] != 'OK'])[:12000])
        storage()
        return [x['result'] for x in items]

    try:
        deadline()
        storage(400000)
        write(data_run / 'PREPARATION-MEMORY-PROJECTION.json', P.project_memory(P.worker_count(), 4, protocol['resources']['working_set_gib']))
        for ref in protocol['inputs'].values():
            need(sha(PKG / ref['path']) == ref['sha256'], 'registered input: ' + ref['path'])
        STATE = S.prepare()
        provenance = STATE['provenance']
        need(STATE['endpoint'] == protocol['comparison']['complex_endpoint'], 'exact current comparator')
        provenance['comparison_acquisition'] = protocol['inputs']['current_comparison_acquisition']
        attribution = provenance['source_attribution']
        domains = {}
        for provider in ('base', 'extra'):
            ref = protocol['inputs']['saved_source_census_' + provider]
            packed = (PKG / ref['path']).read_bytes()
            need(hashlib.sha256(packed).hexdigest() == ref['sha256'], 'frozen excluded packet source')
            previous = json.loads(gzip.decompress(packed))
            need(previous['status'] == 'OK', 'source census completed')
            domains[provider] = dict(receipt=previous['result'], source_pin=ref)
        prepared['constructor'] = M.prepare(STATE['records'], protocol['comparison']['complex_endpoint'], domains=domains)
        write(run / 'IMPLEMENTATION.json', dict(script_sha256=pins,
            source_archives=pin_record['source_archives'], prepared=prepared, parent_load_once=True,
            source_attribution=attribution, provenance=provenance,
            preregistration_sha256=sha(preg), implementation_pins_sha256=sha(pins_path)))
        checks = launch('controls', [dict(kind='controls', seed=s) for s in SEEDS])
        need(all(v['status'] == 'PASS' for v in checks), 'all registered implementation controls')
        need(clean(checks[0]) == clean(checks[1]), 'exact repeated controls')
        baselines = launch('baseline', [dict(kind='baseline', seed=s, provider=p)
                                        for s in SEEDS for p in ('base', 'extra')])
        need(all(v['status'] == 'PASS' for v in baselines), 'both baseline providers and seeds')
        for provider in ('base', 'extra'):
            twins = [v for v in baselines if v['provider'] == provider]
            need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact repeated baseline: ' + provider)
        censuses = launch('census', [dict(kind='census', seed=s, provider=p)
                                    for s in SEEDS for p in ('base', 'extra')])
        need(all(v['status'] == 'PASS' for v in censuses), 'complete finite census')
        for p in ('base', 'extra'):
            twins = [v for v in censuses if v['provider'] == p]
            need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact repeated census: ' + p)
            counts = twins[0]['counts']
            need(counts['source_excluded_addresses'] == 2878 and counts['placements_considered'] == 5756,
                 'complete registered saved-address and placement domain')
            need(counts['commuting_placements'] + counts['noncommuting_placements'] +
                 counts['scalar_precondition_rejected_placements'] == counts['placements_considered'],
                 'every placement either commutes or has a typed exclusion')
            need(len(twins[0]['plans']) == counts['commuting_placements'] and
                 {plan['plan_ordinal'] for plan in twins[0]['plans'].values()} == set(range(counts['commuting_placements'])),
                 'complete unique canonical plan ordinals')
            need(counts['admissible_carrier_choices'] + counts['ratio_rejected_carriers'] == 2*counts['commuting_placements'] and
                 counts['candidates'] == len(twins[0]['candidates']) == 40*counts['admissible_carrier_choices'],
                 'every plan has two carrier dispositions and complete order/corner labels')
            need(len(twins[0]['exclusions']) == counts['noncommuting_placements'] +
                 counts['scalar_precondition_rejected_placements'] + counts['ratio_rejected_carriers'],
                 'one exact witness per scalar or carrier exclusion')
            M.install_census(p, twins[0])
        specs = [dict(kind='prices', seed=s, provider=p, shard=i, shards=64)
                 for s in SEEDS for p in ('base', 'extra') for i in range(64)]
        prices = launch('prices', specs)
        need(all(v['status'] == 'PASS' for v in prices), 'every exact-price shard completed')
        for p in ('base', 'extra'):
            twins = [v for v in censuses if v['provider'] == p]
            need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact repeated census: ' + p)
            domain = twins[0]['candidates']
            for seed in SEEDS:
                seen = set()
                for value in prices:
                    if value['provider'] != p or value['seed'] != seed:
                        continue
                    need(value['domain_sha256'] == twins[0]['domain_sha256'], 'price/census domain binding')
                    need(value['plans_sha256'] == twins[0]['plans_sha256'], 'price/census crossing-plan binding')
                    for field in ('tariff_certificates', 'guard_certificates', 'window_certificates'):
                        need(M.digest(value[field]) == value[field + '_sha256'],
                             'canonical compact certificate collection: ' + field)
                    need(M.digest(value['rows']) == value['shard_rows_sha256'], 'canonical shard row binding')
                    plan_ids = {domain[r['ordinal']]['plan_id'] for r in value['rows']}
                    need(set(value['window_certificates']) == plan_ids, 'every priced plan has one complete window certificate')
                    for plan_id, certificate in value['window_certificates'].items():
                        plan = twins[0]['plans'][plan_id]
                        need(M.digest(certificate['whole_window_boundaries']) == certificate['whole_window_boundaries_sha256'],
                             'whole-window boundary certificate binding')
                        need(certificate['interval_sha256'] == plan['interval_sha256'] and
                             certificate['crossings_sha256'] == plan['crossings_sha256'],
                             'whole-window certificate binds exact source interval and crossings')
                    used_tariffs, used_failures = set(), set()
                    tally = Counter(row['status'] for row in value['rows'])
                    need(value['counts']['candidates'] == len(value['rows']), 'shard candidate count')
                    for outcome in ('PASS_CANDIDATE', 'NO_GAIN', 'REJECTED_GUARD', 'EXPLORATORY'):
                        need(tally[outcome] == value['counts'][outcome], 'explicit shard outcome count')
                    for row_value in value['rows']:
                        ordinal = row_value['ordinal']
                        need(0 <= ordinal < len(domain) and ordinal not in seen and domain[ordinal]['plan_ordinal'] % 64 == value['shard'],
                             'disjoint exhaustive canonical shard partition')
                        need(row_value['candidate_id'] == domain[ordinal]['candidate_id'] and
                             row_value.get('address', domain[ordinal]['address']) == domain[ordinal]['address'] and
                             row_value['plan_id'] == domain[ordinal]['plan_id'] and
                             row_value['plan_ordinal'] == domain[ordinal]['plan_ordinal'], 'literal candidate address and plan binding')
                        if row_value['status'] == 'REJECTED_GUARD':
                            ident = row_value['failure_id']
                            certificate = value['guard_certificates'][ident]
                            need(certificate and M.digest(certificate) == ident,
                                'nonempty exact guard certificate binding')
                            used_failures.add(ident)
                        else:
                            ident = row_value['tariff_id']
                            certificate = value['tariff_certificates'][ident]
                            need(M.digest(certificate) == ident, 'exact tariff certificate binding')
                            delta, moment = certificate['profile_delta'], certificate['moment_delta']
                            need(all(0 < int(k) <= 9 and type(v) is int for k, v in delta.items()) and
                                 sum(int(k)*v for k, v in delta.items()) == 0, 'complete window rank mass')
                            lower, upper = Fraction(moment['lower']), Fraction(moment['upper'])
                            need(lower <= upper and moment['endpoint'] == protocol['comparison']['complex_endpoint'],
                                 'registered endpoint and rational interval ordering')
                            if not delta:
                                need(lower == upper == 0, 'identical complete profile gives exact zero delta')
                            expected = 'PASS_CANDIDATE' if upper < 0 else 'NO_GAIN' if not delta or lower >= 0 else 'EXPLORATORY'
                            need(row_value['status'] == expected, 'registered exact moment disposition')
                            used_tariffs.add(ident)
                        seen.add(ordinal)
                    need(used_tariffs == set(value['tariff_certificates']) and
                         used_failures == set(value['guard_certificates']), 'all compact certificates referenced')
                    positives = {r['candidate_id']: r for r in value['rows'] if r['status'] == 'PASS_CANDIDATE'}
                    need(len(value['favorable']) == len(positives), 'every favorable row exposed for paired selection')
                    for expanded in value['favorable']:
                        compact = positives[expanded['candidate_id']]
                        source_candidate = domain[compact['ordinal']]
                        tariff = value['tariff_certificates'][compact['tariff_id']]
                        need(expanded['address'] == source_candidate['address'] and
                             expanded['pair_key'] == source_candidate['pair_key'] and
                             expanded['profile_delta'] == tariff['profile_delta'] and
                             expanded['moment_delta'] == tariff['moment_delta'], 'expanded favorable row exact binding')
                need(seen == set(range(len(domain))), 'all registered candidates priced exactly once')
            for shard in range(64):
                twins = [v for v in prices if v['provider'] == p and v['shard'] == shard]
                need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact repeated price shard')
        favorable = {}
        for p in ('base', 'extra'):
            values = [candidate for value in prices if value['seed'] == SEEDS[0] and value['provider'] == p
                      for candidate in value['favorable']]
            favorable[p] = {json.dumps(c['pair_key'], separators=(',', ':')): c for c in values}
            need(len(favorable[p]) == len(values), 'unique favorable addresses')
        def address_key(key):
            address = favorable['base'][key]['address']
            return (('A', 'B').index(address[0]), *address[1:])
        common = sorted(set(favorable['base']) & set(favorable['extra']), key=address_key)
        selected = common[:protocol['retained_pair_limit']]
        selection = dict(paired_favorable=len(common), favorable_by_provider={p: len(v) for p, v in favorable.items()},
            selected_pair_keys=[favorable['base'][k]['pair_key'] for k in selected],
            unretained_paired_favorable=len(common) - len(selected),
            rule='First at most8 canonical provider-independent addresses, including both fixed placements; no fitted or root-based ranking')
        write(run / 'SELECTION.json', selection)
        retained = []
        if selected:
            retained = launch('retention', [dict(kind='retention', seed=s, provider=p,
                candidate_id=favorable[p][key]['candidate_id'],
                output_dir=str(PKG / 'data/continuation-10/candidates' / args.attempt / ('seed-' + str(s)) / p))
                for s in SEEDS for key in selected for p in ('base', 'extra')])
            for p in ('base', 'extra'):
                for key in selected:
                    candidate_id = favorable[p][key]['candidate_id']
                    twins = [v for v in retained if v['provider'] == p and v['candidate_id'] == candidate_id]
                    need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact retained candidate repetition')
        for seed in SEEDS:
            totals = {p: Counter() for p in ('base', 'extra')}
            for value in prices:
                if value['seed'] == seed:
                    totals[value['provider']].update(value['counts'])
            statistics[str(seed)] = dict(counts_by_provider={p: dict(c) for p, c in totals.items()},
                census_by_provider={v['provider']: {k: x for k, x in v.items() if k not in ('candidates', 'exclusions', 'plans', 'seed', 'cpu_seconds')}
                                    for v in censuses if v['seed'] == seed},
                selection=selection, retained_provider_words=sum(v['seed'] == seed for v in retained),
                comparison_endpoint=protocol['comparison']['complex_endpoint'],
                pattern_claim=False, kappa_claim=False)
        # Counter names are part of the constructor/runner interface, frozen together.
        aggregate = Counter()
        for value in prices:
            if value['seed'] == SEEDS[0]:
                aggregate.update(value['counts'])
        if aggregate.get('EXPLORATORY', 0):
            status = 'EXPLORATORY'
        elif selected:
            status = 'PASS'
        elif any(favorable.values()) or aggregate.get('candidates', 0) == 0:
            status = 'EXPLORATORY'
        else:
            status = 'NULL'
        need(clean(statistics[str(SEEDS[0])]) == clean(statistics[str(SEEDS[1])]), 'exact scientific decision repeat')
        agreement = True
        phase = None
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error), traceback=traceback.format_exc()[-18000:])
        status = 'TIMEOUT' if isinstance(error, (TimeoutError, P.PoolCpuBudgetExceeded)) else 'ERROR'
    elapsed_cpu, elapsed_wall = cpu() - started_cpu, time.monotonic() - started_wall
    saved = [value for values in observed.values() for value in values.values()]
    overhead = max(0, elapsed_cpu - sum(x['item'].get('cpu_seconds') or 0 for x in saved))
    refs = []
    for i, seed in enumerate(SEEDS):
        mine = [x for x in saved if x['spec']['seed'] == seed]
        refs.append(write(run / ('seed-' + str(seed)) / 'RESULT.json', dict(schema_version=1,
            experiment=protocol['experiment'], milestone='CONTINUATION-10/J2', seed=seed, status=status,
            recorded_utc=now(), script_sha256=pins, implementation_pins_sha256=sha(pins_path),
            preregistration_sha256=sha(preg), source_attribution=attribution, provenance=provenance,
            word_blob_ids={p['path']: p.get('git_blob') for p in attribution if 'word' in p['path'].lower()}, inputs=protocol['inputs'],
            cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine) + (overhead if i == 0 else 0),
            wall_seconds=elapsed_wall, peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine), default=0),
            statistics=statistics.get(str(seed)), task_receipts=[x['artifact'] for x in mine],
            n_permutations=0, null_summary=dict(kind='exact finite-domain census', model=protocol['null_model']),
            failure=failure, incomplete_phase=phase, scientific_decision_agreement=agreement,
            confirmed=failure is None and agreement,
            decision=dict(verdict=status, pass_bar=protocol['pass_bar'], null_bar=protocol['null_bar'],
                          pattern_claim=False, kappa_claim=False),
            scope='Exact left/right adjacent-commutation exposure and complete window tariff at fixed exterior; a favorable local word is a census target requiring native/supplier/outer admission.')))
    attempts = row.get('attempts', []) + [dict(attempt=args.attempt, status=status, cpu_seconds=elapsed_cpu,
        wall_seconds=elapsed_wall, result_files=[r['path'] for r in refs])]
    row.update(status=status, execution='COMPLETED' if failure is None else 'INCOMPLETE', attempts=attempts,
        confirmed=failure is None and agreement, result_files=[r['path'] for r in refs],
        cpu_seconds=sum(a['cpu_seconds'] for a in attempts), wall_seconds=sum(a['wall_seconds'] for a in attempts),
        updated_utc=now())
    registry['no_active_experiments'] = True
    registry['status'] = 'SCIENCE_COMPLETE' if failure is None else 'PRESERVED_ERROR'
    write(registry_path, registry, False)
    write(run / 'RUN.json', dict(status=status, confirmed=failure is None and agreement,
        total_cpu_seconds=elapsed_cpu, total_wall_seconds=elapsed_wall, failure=failure,
        incomplete_phase=phase, statistics=statistics, results=refs,
        completed_by_phase={p: len(v) for p, v in observed.items()}, workers=P.worker_count(),
        detailed_evidence_directory=str(data_run.relative_to(PKG)),
        detailed_evidence=[dict(path=str(p.relative_to(PKG)), sha256=sha(p), bytes=p.stat().st_size)
                           for p in sorted(data_run.rglob('*')) if p.is_file()],
        storage_before_run_receipt=storage()))
    storage()
    print(json.dumps(dict(status=status, cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall, failure=failure)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
