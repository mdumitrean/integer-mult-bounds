"""Registered exact carrier-factor census; one bounded central pool at a time."""
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
ROUND = PKG / 'results/CONTINUATION-08'
SEEDS = (41117, 83003)
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
        need(path.is_relative_to(PKG / 'data/continuation-08/candidates'), 'candidate confinement')
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
    preg = ROUND / 'F1/PREREGISTRATION.json'
    protocol = json.loads(preg.read_text())
    need(sha(preg) == args.registration_sha256 and protocol['state'] == 'FROZEN', 'frozen preregistration')
    need(tuple(protocol['seeds']) == SEEDS, 'two fixed seeds')
    pins_path = ROUND / 'F1' / ('IMPLEMENTATION-PINS-' + args.attempt + '.json')
    pin_record = json.loads(pins_path.read_text())
    pins = pin_record['sha256']
    for name, expected in pins.items():
        need(sha(ROOT / name) == expected, 'source pin before imports: ' + name)
    need(str(Path(__file__).relative_to(ROOT)) in pins, 'runner is frozen')
    sys.path[:0] = [str(HERE), str(HERE.parent)]
    import source3015 as S
    import carrier_factors as M
    import pool as P
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(r for r in registry['experiments'] if r['id'] == protocol['experiment'])
    need(registry['no_active_experiments'], 'one scientific pool')
    need(row['status'] == 'planned' or row.get('execution') == 'INCOMPLETE', 'new or registered mechanical repair')
    run = ROUND / protocol['experiment'] / args.attempt
    run.mkdir(parents=True, exist_ok=False)
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

    def storage():
        need(sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file()) < 4000000, 'round results4MB cap')
        need(sum(p.stat().st_size for p in (PKG / 'results').rglob('*') if p.is_file()) < 200000000, 'global results200MB cap')

    def launch(name, specs):
        nonlocal phase
        phase = name
        remaining = deadline()
        observed[name] = {}
        write(run / (name.upper() + '-TASKS.json.gz'), specs)

        def checkpoint(index, item):
            ref = write(run / name / ('task-%05d.json.gz' % index), item)
            observed[name][index] = dict(spec=specs[index], item=item, artifact=ref)
            write(run / 'BUDGET-CHECKPOINT.json', dict(recorded_utc=now(), phase=name,
                parent_and_reaped_cpu_seconds=cpu() - started_cpu,
                completed={k: len(v) for k, v in observed.items()}), False)
            if len(specs) < 20 or len(observed[name]) % 32 == 0 or len(observed[name]) == len(specs):
                print(json.dumps(dict(phase=name, completed=len(observed[name]), total=len(specs),
                                      status=item['status'])), flush=True)
        P.run_pool(worker, [(s,) for s in specs], workers=P.worker_count(), timeout=300, rss_gib=4,
                   working_set_gib=1.0, projection_path=run / (name.upper() + '-MEMORY-PROJECTION.json'),
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
        write(run / 'PREPARATION-MEMORY-PROJECTION.json', P.project_memory(P.worker_count(), 4, 1.0))
        for ref in protocol['inputs'].values():
            need(sha(PKG / ref['path']) == ref['sha256'], 'registered input: ' + ref['path'])
        STATE = S.prepare()
        provenance = STATE['provenance']
        provenance['comparison'] = protocol['comparison']
        provenance['comparison_acquisition'] = protocol['inputs']['current_comparison_acquisition']
        attribution = provenance['source_attribution']
        prepared['constructor'] = M.prepare(STATE['records'], protocol['comparison']['complex_endpoint'],
                                            fixtures=STATE['fixtures'], declaration=STATE['declaration'])
        write(run / 'IMPLEMENTATION.json', dict(script_sha256=pins,
            source_archives=pin_record['source_archives'], prepared=prepared, parent_load_once=True,
            source_attribution=attribution, provenance=provenance,
            preregistration_sha256=sha(preg), implementation_pins_sha256=sha(pins_path)))
        checks = launch('controls', [dict(kind='controls', seed=s) for s in SEEDS])
        need(all(v['status'] == 'PASS' for v in checks), 'all registered implementation controls')
        baselines = launch('baseline', [dict(kind='baseline', seed=s, provider=p)
                                        for s in SEEDS for p in ('base', 'extra')])
        need(all(v['status'] == 'PASS' for v in baselines), 'both baseline providers and seeds')
        censuses = launch('census', [dict(kind='census', seed=s, provider=p)
                                    for s in SEEDS for p in ('base', 'extra')])
        need(all(v['status'] == 'PASS' for v in censuses), 'complete finite census')
        for p in ('base', 'extra'):
            twins = [v for v in censuses if v['provider'] == p]
            need(len(twins) == 2 and clean(twins[0]) == clean(twins[1]), 'exact repeated census: ' + p)
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
                    tally = Counter(row['status'] for row in value['rows'])
                    need(value['counts']['candidates'] == len(value['rows']), 'shard candidate count')
                    for outcome in ('PASS_CANDIDATE', 'NO_GAIN', 'REJECTED_GUARD', 'EXPLORATORY'):
                        need(tally[outcome] == value['counts'][outcome], 'explicit shard outcome count')
                    for row_value in value['rows']:
                        ordinal = row_value['ordinal']
                        need(0 <= ordinal < len(domain) and ordinal not in seen and ordinal % 64 == value['shard'],
                             'disjoint exhaustive canonical shard partition')
                        need(row_value['candidate_id'] == domain[ordinal]['candidate_id'] and
                             row_value['address'] == domain[ordinal]['address'], 'literal candidate address binding')
                        seen.add(ordinal)
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
            rule='First at most8 canonical provider-independent addresses; no fitted or root-based ranking')
        write(run / 'SELECTION.json', selection)
        retained = []
        if selected:
            retained = launch('retention', [dict(kind='retention', seed=s, provider=p,
                candidate_id=favorable[p][key]['candidate_id'],
                output_dir=str(PKG / 'data/continuation-08/candidates' / args.attempt / ('seed-' + str(s)) / p))
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
                census_by_provider={v['provider']: {k: x for k, x in v.items() if k not in ('candidates', 'seed', 'cpu_seconds')}
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
            experiment=protocol['experiment'], milestone='CONTINUATION-08/F1', seed=seed, status=status,
            recorded_utc=now(), script_sha256=pins, implementation_pins_sha256=sha(pins_path),
            preregistration_sha256=sha(preg), source_attribution=attribution, provenance=provenance,
            word_blob_ids={p['path']: p.get('git_blob') for p in attribution}, inputs=protocol['inputs'],
            cpu_seconds=sum(x['item'].get('cpu_seconds') or 0 for x in mine) + (overhead if i == 0 else 0),
            wall_seconds=elapsed_wall, peak_rss_bytes=max((x['item'].get('peak_rss_bytes') or 0 for x in mine), default=0),
            statistics=statistics.get(str(seed)), task_receipts=[x['artifact'] for x in mine],
            n_permutations=0, null_summary=dict(kind='exact finite-domain census', model=protocol['null_model']),
            failure=failure, incomplete_phase=phase, scientific_decision_agreement=agreement,
            confirmed=failure is None and agreement,
            decision=dict(verdict=status, pass_bar=protocol['pass_bar'], null_bar=protocol['null_bar'],
                          pattern_claim=False, kappa_claim=False),
            scope='Exact guarded carrier-factor census at fixed exterior; a favorable local word is a census target requiring native/supplier/outer admission.')))
    attempts = row.get('attempts', []) + [dict(attempt=args.attempt, status=status, cpu_seconds=elapsed_cpu,
        wall_seconds=elapsed_wall, result_files=[r['path'] for r in refs])]
    row.update(status=status, execution='COMPLETED' if failure is None else 'INCOMPLETE', attempts=attempts,
        confirmed=failure is None and agreement, result_files=[r['path'] for r in refs],
        cpu_seconds=sum(a['cpu_seconds'] for a in attempts), wall_seconds=sum(a['wall_seconds'] for a in attempts),
        updated_utc=now())
    registry['no_active_experiments'] = True
    write(registry_path, registry, False)
    write(run / 'RUN.json', dict(status=status, confirmed=failure is None and agreement,
        total_cpu_seconds=elapsed_cpu, total_wall_seconds=elapsed_wall, failure=failure,
        incomplete_phase=phase, statistics=statistics, results=refs,
        completed_by_phase={p: len(v) for p, v in observed.items()}, workers=P.worker_count()))
    storage()
    print(json.dumps(dict(status=status, cpu_seconds=elapsed_cpu, wall_seconds=elapsed_wall, failure=failure)), flush=True)
    if failure:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
