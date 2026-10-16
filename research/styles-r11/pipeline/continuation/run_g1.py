"""Central, serialized launcher for frozen G1-PAIRED-GRAMMAR.

Run only after coordinator review. Every parallel phase uses pipeline/pool.py;
all results, compact nominee addresses and source bytes are retained immutably.
This runner never imports or executes fetched PR code and never claims complete
native/owner/outer admission from a paired algebraic certificate.
"""
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
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
for _key in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS',
             'NUMEXPR_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[_key] = '1'
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE),str(HERE.parent)]
import records as R
import pool
import latest_fill as F
import admission as A
import rewrite_search as G

ROUND = R.RESULTS / 'CONTINUATION-01'
EXPERIMENT = 'G1-PAIRED-GRAMMAR'
PREG = ROUND / 'G1/PREREGISTRATION.json'
CLARIFICATION = ROUND / 'G1/IMPLEMENTATION-CLARIFICATION.json'
SEEDS = (11031,29063)
TRANSFORM_HELPERS = (424,428,412,331,299,320,511,304,499)
ADMISSION_CAP = 16
MAX_NEW_ARTIFACT_BYTES = 100_000_000
MAX_TOTAL_RESULTS_BYTES = 200_000_000
FINAL_ARTIFACT_RESERVE_BYTES = 20_000_000
_CONTROL = {}
_ATTRIBUTION = []


def need(condition,message):
    if not condition:
        raise ValueError(message)


def cpu():
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time()+children.ru_utime+children.ru_stime


def _json_bytes(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def _results_bytes():
    return sum(path.stat().st_size for path in R.RESULTS.rglob('*') if path.is_file())


def source_snapshot(directory):
    paths = set((R.PKG/'pipeline').rglob('*.py'))
    for module in tuple(sys.modules.values()):
        path = getattr(module,'__file__',None)
        if path:
            path = Path(path).resolve()
            if path.is_relative_to(R.ROOT/'research') and path.suffix=='.py':
                paths.add(path)
    result = {}
    for path in sorted(paths):
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        result[str(path.relative_to(R.ROOT))] = digest
        archive = directory/(digest+'.py.gz')
        archive.parent.mkdir(parents=True,exist_ok=True)
        if not archive.exists():
            with archive.open('xb') as handle:
                handle.write(gzip.compress(raw,mtime=0))
    return result


def _gzip_json(path,value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    raw = _json_bytes(value)
    data = gzip.compress(raw,mtime=0)
    with path.open('xb') as handle:
        handle.write(data)
    return dict(path=str(path.relative_to(R.PKG)),sha256=hashlib.sha256(data).hexdigest(),
                decoded_sha256=hashlib.sha256(raw).hexdigest(),bytes=len(data),decoded_bytes=len(raw))


def _physical_invoice(raw,declared_buffers,declared_stock):
    helpers = raw['report']['R']-len(raw['removed'])
    actual_buffers = len(raw['helper_final'])
    actual_stock = 66304+helpers+len(raw['centers'])+actual_buffers+2
    need(declared_buffers==actual_buffers,'private zero buffer invoice disagrees with literal endpoint set')
    need(declared_stock==actual_stock,'physical stock omits an explicitly charged component')
    return dict(live_families=66304,helpers=helpers,centres=len(raw['centers']),
                private_zero_buffers=actual_buffers,coefficient_work=2,physical_families=actual_stock,
                scope='Exact buffer/stock binding only; native and complete supplier admission remain separate')


def _fresh_invoice(raw,attribution):
    W = G._wordio()
    value = deepcopy(raw)
    word = W.WordData(value,attribution,assert_profile=False)
    value['report']['local_profile'] = {str(r):n for r,n in word.paid.items()}
    value['report']['width_inventory'] = {str(r):n for r,n in sorted(Counter(
        len(word.end[r])-len(word.start[r]) for r in word.helpers).items())}
    value['cleanup'] = W.derived_borrow_cleanup(word)
    return value


def _expected_rejection(name,call,expected):
    try:
        call()
    except G.ExactBudgetExceeded:
        raise
    except (ValueError,RuntimeError,AssertionError) as exc:
        reason = str(exc)
        need(any(label in reason for label in expected),
             'mutation rejected for an unregistered reason: '+name+': '+reason[:500])
        return dict(name=name,status='PASS_REJECTED',reason=type(exc).__name__+': '+reason[:500],
                    expected_diagnostic=list(expected))
    raise ValueError('negative control was accepted: '+name)


def control_task(spec):
    """One provider/seed, with all positive and negative registered controls."""
    started = time.process_time()
    provider,seed = spec['provider'],spec['seed']
    source = _CONTROL[provider]
    attribution = source['attribution']
    baseline = A.local_admission(source['expected_raw'],attribution)
    need(baseline['audit']['checked_columns']==632,'all632 independent baseline columns')
    positive = G.calibration_task(dict(parent_raw=source['parent_raw'],expected_raw=source['expected_raw'],
        transforms=source['transforms'],attribution=attribution,seed=seed))
    first = source['transforms'][0]
    literal,proof = G.apply_to_raw(source['parent_raw'],first,attribution)
    first_audit = A.local_admission(literal,attribution)
    signed = deepcopy(first)
    need(signed['after'][-1][0]=='add','source-bound sign mutation selects an addition')
    signed['after'][-1][3] *= -1
    controls = [_expected_rejection('wrong_output_shear_sign',
        lambda:G.apply_to_raw(source['parent_raw'],signed,attribution),
        ('M v = y','alpha y = 1','u S = e_h^T','T y = e_h','C v = 0'))]
    omitted = deepcopy(literal)
    need(omitted['compensation'],'nonempty exact compensation control')
    removed = omitted['compensation'].pop(0)
    omitted = _fresh_invoice(omitted,attribution)
    controls.append(_expected_rejection('omitted_compensation',
        lambda:A.local_admission(omitted,attribution),('target map failed','all-column endpoint failure')))
    controls[-1]['removed_gate'] = removed
    malformed = deepcopy(literal)
    malformed['helper_final'][str(first['helper'])] = []
    # The frame chain fails before the report is consulted, so a stale histogram
    # cannot supply the reason for this mutation's rejection.
    controls.append(_expected_rejection('corrupted_terminal_frame',
        lambda:_fresh_invoice(malformed,attribution),('frame violation',)))
    buffers = len(literal['helper_final'])
    stock = 66304+408+8+buffers+2
    invoice = _physical_invoice(literal,buffers,stock)
    controls.append(_expected_rejection('uncharged_private_buffer',
        lambda:_physical_invoice(literal,buffers-1,stock-1),('private zero buffer invoice',)))
    return dict(status='PASS',provider=provider,seed=seed,baseline=baseline,
                positive_nine_stage=positive,positive_first_stage_audit=first_audit,
                positive_paired_certificate=proof['status'],negative_controls=controls,
                complete_buffer_binding=invoice,source_attribution=attribution,
                cpu_seconds=time.process_time()-started,
                scope='Exact local algebra, literal frames and buffer invoice controls; no fresh native replay')


def _address_key(row):
    return (row['helper'],row['normal'],row['mode'],tuple(row['basis_indices']))


def validate_task(spec):
    """Both provider witnesses and fresh independent semantic admission."""
    started = time.process_time()
    output,hashes = {},{}
    directory = Path(spec['directory'])
    for provider in sorted(spec['addresses']):
        address = spec['addresses'][provider]
        raw,transform,certificate = G.reconstruct_nominee(address)
        attribution = _CONTROL[provider]['attribution']
        local = A.local_admission(raw,attribution)
        need(local['audit']['checked_columns']==632,'all632 nominee input columns')
        buffers = len(raw['helper_final'])
        need(buffers==83,'exactly one additional private buffer on the82-endpoint source')
        invoice = _physical_invoice(raw,buffers,66304+408+8+buffers+2)
        word_artifact = _gzip_json(directory/('WORD-'+provider+'.json.gz'),raw)
        transform_artifact = _gzip_json(directory/('TRANSFORM-'+provider+'.json.gz'),transform)
        certificate_artifact = _gzip_json(directory/('CERTIFICATE-'+provider+'.json.gz'),certificate)
        output[provider] = dict(address=address,local_admission=local,physical_binding=invoice,
                                word=word_artifact,transform=transform_artifact,certificate=certificate_artifact)
        hashes[provider] = G.semantic_sha(raw)
    need(set(output)=={'gauge44','extra'},'both provider variants required')
    return dict(status='PASS_LOCAL_PAIRED_PRODUCTION',seed=spec['seed'],identity=spec['identity'],
                providers=output,word_semantic_sha256=hashes,cpu_seconds=time.process_time()-started,
                complete_allocation='PENDING_SEPARATE_V2',fresh_native_admission='PENDING_SEPARATE_V2',
                complete_supplier_and_outer='PENDING_SEPARATE_V2',
                source_attribution=_ATTRIBUTION)


def dispatch_task(spec):
    if spec['kind']=='control':
        return control_task(spec)
    if spec['kind']=='screen':
        return G.screen_task(spec)
    if spec['kind']=='validate':
        return validate_task(spec)
    raise ValueError('unknown G1 task kind')


def _deadline(protocol):
    if datetime.now(timezone.utc)>=datetime.fromisoformat(protocol['hard_stop_utc']):
        raise TimeoutError('two-week hard stop reached')


def main(attempt='v1'):
    global _ATTRIBUTION
    protocol = json.loads(PREG.read_text())
    clarification = json.loads(CLARIFICATION.read_text())
    need(protocol['state']=='FROZEN' and tuple(protocol['seeds'])==SEEDS,'frozen family and seed binding')
    need(clarification['preregistration_sha256']==R.sha256(PREG),'clarification/preregistration binding')
    need(clarification['admission_retention_cap']==ADMISSION_CAP,'frozen artifact retention cap')
    for relative,digest in clarification['implementation_sha256'].items():
        need(R.sha256(R.ROOT/relative)==digest,'frozen G1 implementation source: '+relative)
    _deadline(protocol)
    need(attempt.startswith('v') and attempt[1:].isdigit(),'explicit immutable attempt name')
    run = ROUND/EXPERIMENT/attempt
    if run.exists():
        raise FileExistsError('immutable attempt already exists: '+str(run))
    registry_path = ROUND/'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = next(x for x in registry['experiments'] if x['id']==EXPERIMENT)
    need(row['status']=='planned','unplanned repeated launch')
    run.mkdir(parents=True)
    row.update(status='running',started_utc=R.utcnow())
    R.write_json(registry_path,registry)
    c0,w0 = cpu(),time.monotonic()
    _ATTRIBUTION = R.provenance()+F.provenance()['source_attribution']
    initial_results_bytes = _results_bytes()
    artifact_budget = min(MAX_NEW_ARTIFACT_BYTES,
                         MAX_TOTAL_RESULTS_BYTES-initial_results_bytes-FINAL_ARTIFACT_RESERVE_BYTES)
    observed = {'controls':{},'screen':{},'validation':{}}
    task_lists,manifest,prepared = {},{},{}
    failure = None
    used_artifact_bytes = 0
    selection = dict(status='NOT_REACHED')
    coverage = {}

    def launch(phase,specs):
        nonlocal used_artifact_bytes
        _deadline(protocol)
        task_lists[phase] = specs
        R.write_json(run/(phase.upper()+'-TASKS.json'),specs,immutable=True)
        remaining = protocol['resources']['cpu_budget_seconds_family']-(cpu()-c0)
        if remaining<=0:
            raise TimeoutError('registered G1 total CPU budget exhausted before '+phase)
        def checkpoint(index,item):
            nonlocal used_artifact_bytes
            spec = specs[index]
            data = _json_bytes(item)
            encoded = gzip.compress(data,mtime=0)
            if used_artifact_bytes+len(encoded)>artifact_budget:
                raise RuntimeError('G1 artifact budget exceeded; incomplete family, no NULL')
            path = run/phase/('task-%05d.json.gz'%index)
            artifact = _gzip_json(path,item)
            used_artifact_bytes += artifact['bytes']
            observed[phase][index] = dict(item=item,artifact=artifact,spec=spec)
            result = item.get('result',{})
            print(json.dumps(dict(phase=phase,index=index,seed=spec['seed'],pool_status=item['status'],
                status=result.get('status'),nominees=len(result.get('witnesses',[])),
                cpu_seconds=item.get('cpu_seconds'))),flush=True)
        pool.run_pool(dispatch_task,[(spec,) for spec in specs],workers=pool.worker_count(),
                      timeout=protocol['resources']['task_timeout_seconds'],rss_gib=4,
                      working_set_gib=1,projection_path=run/(phase.upper()+'-MEMORY-PROJECTION.json'),
                      on_result=checkpoint,cpu_budget_seconds=remaining)
        need(len(observed[phase])==len(specs),'incomplete '+phase+' pool coverage')
        failed = [i for i,value in observed[phase].items() if value['item']['status']!='OK']
        if failed:
            statuses = [observed[phase][i]['item']['status'] for i in failed]
            if 'TIMEOUT' in statuses:
                raise TimeoutError(phase+' worker timeout: '+repr(failed))
            raise RuntimeError(phase+' worker error: '+repr(failed))

    try:
        need(artifact_budget>0,'insufficient global results storage budget before preparation')
        prepared['source'] = F.prepare(pr=2917)
        record = F.get_record()
        source_pin = dict(pr=2917,commit=protocol['baseline_commit'],
                          manifest_sha256=protocol['source_manifest_sha256'],
                          manifest_path=str(record['directory']/'MANIFEST.json'))
        prepared['admission'] = A.prepare(record,source_pin)
        _ATTRIBUTION = R.provenance()+F.provenance()['source_attribution']
        for provider,relative in record['word_files'].items():
            tag = 'base' if provider=='gauge44' else 'extra'
            attribution = deepcopy(record['file_pins'][relative])
            attribution.update(inherited_source_attribution=deepcopy(_ATTRIBUTION))
            _CONTROL[provider] = dict(parent_raw=record['data']['data/PARENT-'+tag+'.json.gz'],
                expected_raw=record['data'][relative],attribution=attribution,
                transforms=[record['data']['data/TRANSFORM-%d.json'%h] for h in TRANSFORM_HELPERS])
        prepared['grammar'] = G.prepare({pid:dict(raw=x['expected_raw'],attribution=x['attribution'])
                                         for pid,x in _CONTROL.items()})
        manifest = source_snapshot(ROUND/'SOURCES')
        R.write_json(run/'IMPLEMENTATION.json',dict(script_sha256=manifest,prepared=prepared,
            preregistration_sha256=R.sha256(PREG),clarification_sha256=R.sha256(CLARIFICATION),
            source_attribution=_ATTRIBUTION,frozen_utc=R.utcnow()),immutable=True)
        controls = [dict(kind='control',provider=pid,seed=seed)
                    for seed in SEEDS for pid in sorted(_CONTROL)]
        launch('controls',controls)
        need(all(x['item']['result']['status']=='PASS' for x in observed['controls'].values()),
             'all enabled calibration controls must pass before search')
        specs = [dict(kind='screen',**spec) for seed in SEEDS for spec in G.task_specs(seed)]
        launch('screen',specs)
        for seed in SEEDS:
            for provider in _CONTROL:
                for mode in G.MODES:
                    results = [v['item']['result'] for v in observed['screen'].values()
                               if v['item']['result']['seed']==seed
                               and v['item']['result']['provider']==provider
                               and v['item']['result']['mode']==mode]
                    normal_list = [normal for value in results for normal in value['normals']]
                    group_list = [value['group'] for value in results]
                    expected_groups = [i for i,value in enumerate(G._WORDS[provider]['groups'])
                                       if value['mode']==mode]
                    need(sorted(normal_list)==list(range(1,512)),
                         'exact511 unique normal coverage: '+str((seed,provider,mode)))
                    need(len(group_list)==len(set(group_list)) and sorted(group_list)==expected_groups,
                         'every registered output group exactly once: '+str((seed,provider,mode)))
                    need(all(value['status'] in ('NOMINEES','NULL_BOUNDED_GRAMMAR') and
                             (value['status']=='NOMINEES')==bool(value['witnesses']) for value in results),
                         'recognized and internally consistent bounded census status')
                    coverage[str(seed)+':'+provider+':'+mode] = dict(unique_normals=511,
                        all_normals_exact=True,groups_once=True,groups=len(group_list))
        R.write_json(run/'COVERAGE.json',coverage,immutable=True)
        inventories = {(seed,pid):{} for seed in SEEDS for pid in _CONTROL}
        for value in observed['screen'].values():
            result = value['item']['result']
            bucket = inventories[result['seed'],result['provider']]
            for nominee in result['witnesses']:
                key = _address_key(nominee)
                need(key not in bucket,'duplicate compact nominee identity')
                bucket[key] = nominee
        for provider in _CONTROL:
            first,second = inventories[SEEDS[0],provider],inventories[SEEDS[1],provider]
            need(first==second,'second seed nominee identities or exact invoices disagree: '+provider)
        common = sorted(set.intersection(*(set(bucket) for bucket in inventories.values())))
        selected = common[:ADMISSION_CAP]
        selection = dict(status='FROZEN_SELECTION',order='helper, normal, mode, canonical basis indices',
            total_nominees_by_seed_provider={str(seed)+':'+pid:len(bucket) for (seed,pid),bucket in inventories.items()},
            matched_both_provider_identities=len(common),retained_identities=[list(k[:3])+[list(k[3])] for k in selected],
            retained_count=len(selected),truncated_matched_identities=max(0,len(common)-ADMISSION_CAP),
            unmatched_by_seed_provider={str(seed)+':'+pid:len(set(bucket)-set(common))
                                       for (seed,pid),bucket in inventories.items()},
            unretained_compact_nominees_preserved=True,
            scientific_decision='EXPLORATORY whenever any nominal direction still requires complete admission')
        R.write_json(run/'NOMINEE-SELECTION.json',selection,immutable=True)
        validation = []
        for seed in SEEDS:
            for index,key in enumerate(selected):
                directory = run/('seed-'+str(seed))/'nominees'/('%02d'%index)
                validation.append(dict(kind='validate',seed=seed,identity=list(key[:3])+[list(key[3])],
                    addresses={pid:inventories[seed,pid][key] for pid in sorted(_CONTROL)},directory=str(directory)))
        if validation:
            launch('validation',validation)
            need(all(x['item']['result']['status']=='PASS_LOCAL_PAIRED_PRODUCTION'
                     for x in observed['validation'].values()),'retained exact semantic validation')
            byseed = {seed:{} for seed in SEEDS}
            for value in observed['validation'].values():
                result = value['item']['result']
                byseed[result['seed']][json.dumps(result['identity'])] = result['word_semantic_sha256']
            need(byseed[SEEDS[0]]==byseed[SEEDS[1]],'second-seed reconstructed candidate identity mismatch')
    except BaseException:
        failure = traceback.format_exc()[-12000:]

    measured_results_bytes = _results_bytes()
    if measured_results_bytes>=MAX_TOTAL_RESULTS_BYTES:
        failure = (failure or '')+'\nGlobal results storage cap exceeded; incomplete family, no NULL.'
    total_cpu,total_wall = cpu()-c0,time.monotonic()-w0
    attributable = sum((v['item'].get('cpu_seconds') or 0) for phase in observed.values() for v in phase.values())
    overhead = max(0,total_cpu-attributable)
    records = []
    for number,seed in enumerate(SEEDS):
        items = {phase:[v for v in values.values() if v['spec']['seed']==seed]
                 for phase,values in observed.items()}
        screen = [v['item']['result'] for v in items['screen'] if v['item']['status']=='OK']
        nominees = sum(len(value['witnesses']) for value in screen)
        expected = {phase:sum(s['seed']==seed for s in specs) for phase,specs in task_lists.items()}
        complete = failure is None and all(len(items[phase])==expected.get(phase,0) for phase in items)
        if failure:
            status = 'TIMEOUT' if ('Timeout' in failure or 'CpuBudgetExceeded' in failure) else 'ERROR'
        elif nominees:
            status = 'EXPLORATORY'
        else:
            status = 'NULL' if complete else 'EXPLORATORY'
        statistics = dict(calibration_complete=complete or ('screen' in task_lists),
            expected_tasks=expected,collected_tasks={phase:len(values) for phase,values in items.items()},
            compact_nominees=nominees,selection=selection,
            attempted_constructions=sum(x['attempted_constructions'] for x in screen),
            scoped_rejections=dict(sum((Counter(x['rejections']) for x in screen),Counter())),
            covered_hyperplanes_by_provider_mode={pid+':'+mode:sum(len(x['normals']) for x in screen
                if x['provider']==pid and x['mode']==mode) for pid in _CONTROL for mode in G.MODES},
            truncated_basis_pairs=sum(x['spaces']['truncated_basis_pairs']*len(x['normals']) for x in screen),
            truncated_pivots=sum(x['truncated_pivots_per_pair']*x['spaces']['retained_basis_pairs']*len(x['normals']) for x in screen),
            artifact_checkpoints={phase:[v['artifact'] for v in values] for phase,values in items.items()},
            local_validated_nominees=[v['item'].get('result') for v in items['validation'] if v['item']['status']=='OK'],
            remaining_admission='V2 exact complete fill, fresh native/physical/supplier/outer obligations for any nominee',
            all_compact_nominees_preserved=True)
        statistics['exact_coverage'] = {key:value for key,value in coverage.items() if key.startswith(str(seed)+':')}
        receipt = dict(schema_version=1,experiment=EXPERIMENT,milestone='CONTINUATION-01',
            recorded_utc=R.utcnow(),seed=seed,n_permutations=0,status=status,
            word_blob_ids={p['path']:p['git_blob'] for p in _ATTRIBUTION},source_attribution=_ATTRIBUTION,
            script_sha256=manifest,script_manifest_sha256=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest(),
            preregistration_sha256=R.sha256(PREG),clarification_sha256=R.sha256(CLARIFICATION),statistics=statistics,
            wall_seconds=total_wall,cpu_seconds=sum((v['item'].get('cpu_seconds') or 0) for values in items.values() for v in values)
                +(overhead if number==0 else 0),
            peak_rss_bytes=max([v['item'].get('peak_rss_bytes') or 0 for values in items.values() for v in values]+[0]),
            null_summary=dict(model='none: finite constructive grammar',mean=None,sd=None,empirical_p=None),
            decision=dict(pass_bar=protocol['experiments'][EXPERIMENT]['pass_bar'],verdict=status),
            confirmation_required=True,launch_failure=failure,
            scope='Bounded canonical paired directions only. Any nominal candidate is EXPLORATORY until complete separate admission.')
        R.write_json(run/('seed-'+str(seed))/'RESULT.json',receipt,immutable=True)
        records.append(receipt)
    same = len({x['status'] for x in records})==1
    status = records[0]['status'] if same else 'EXPLORATORY'
    row.update(status=status,confirmed=same and status=='NULL',updated_utc=R.utcnow(),cpu_seconds=total_cpu,
        result_files=[str((run/('seed-'+str(s))/'RESULT.json').relative_to(R.PKG)) for s in SEEDS],
        confirmation_note='Both seeds use the same frozen exact bases/caps and different traversal. All nominee hashes/invoices must agree; positive admission remains separate.')
    R.write_json(registry_path,registry)
    R.write_json(run/'RUN.json',dict(status=status,total_cpu_seconds=total_cpu,total_wall_seconds=total_wall,
        failure=failure,collected={p:len(v) for p,v in observed.items()},compact_checkpoint_bytes=used_artifact_bytes,
        initial_total_results_bytes=initial_results_bytes,checkpoint_budget_bytes=artifact_budget,
        total_results_bytes_before_final_receipts=measured_results_bytes,
        note='Native/complete allocation admission is never inferred from local production success'),immutable=True)
    need(_results_bytes()<MAX_TOTAL_RESULTS_BYTES,'global final results storage cap')
    print(json.dumps(dict(experiment=EXPERIMENT,status=status,cpu_seconds=total_cpu,
                         wall_seconds=total_wall,failure=failure)),flush=True)
    if failure:
        raise SystemExit(1)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',default='v1')
    args = parser.parse_args()
    main(args.attempt)
