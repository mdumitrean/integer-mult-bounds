"""Reconcile immutable F1 receipts after the registered mechanical storage repair.

Only administrative saved-byte verification and exact certificate arithmetic are
called. No scientific producer, optimizer, pool, native audit or candidate
construction is imported or rerun. The original v1 ERROR is never overwritten.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import time
import traceback

PKG = Path(__file__).resolve().parents[2]
ROUND = PKG / 'results/CONTINUATION-08'
DEST = ROUND / 'F1-RECONCILIATION/v1'
AUDITOR_SHA = '553269128e13727e95e06e298a625f4af058941461ee1cf8ba44defb395d6ef6'
REVIEW_SHA = '3e3195cf642562e7f9c169715d70a39222d7ac9070435dc127fbc52171bb8c9f'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    started = time.process_time()
    sources = {'auditor': AUDITOR_SHA, 'reconciler': digest(Path(__file__).read_bytes())}
    try:
        auditor_path = Path(__file__).with_name('audit_round.py')
        if digest(auditor_path.read_bytes()) != AUDITOR_SHA:
            raise ValueError('administrative auditor differs from the frozen reconciliation pin')
        spec = importlib.util.spec_from_file_location('continuation08_saved_byte_audit', auditor_path)
        A = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(A)
        registry = A.read(ROUND / 'EXPERIMENTS.json')
        row = next(x for x in registry['experiments'] if x['id'] == A.FAMILY)
        A.need(len(row['attempts']) == 1 and row['attempts'][0]['attempt'] == 'v1' and
               row['attempts'][0]['status'] == 'ERROR', 'exact original ERROR attempt preserved')
        original = A.read(PKG / 'data/words/PINS.json')['files']
        storage = A.audit_relocation()
        checked = A.audit_attempt(row, row['attempts'][0], original, reconcile=True)
        domain = checked['domain']
        A.need(checked['reconciled_saved_decision'] == 'NULL' and
               domain['selected_pairs'] == domain['unvalidated_paired'] == domain['unresolved_rows'] == 0,
               'complete registered saved domain has no favorable or unresolved candidate')
        oldrun = ROUND / A.FAMILY / 'v1'
        oldmeta = A.read(oldrun / 'RUN.json')
        oldresults = {A.read(A.reference(ref))['seed']: A.read(A.reference(ref))
                      for ref in oldmeta['results']}
        A.need(set(oldresults) == A.SEEDS and
               oldresults[min(A.SEEDS)]['source_attribution'] == oldresults[max(A.SEEDS)]['source_attribution'],
               'same complete source attribution across both original seed receipts')

        def ref(path):
            path = Path(path)
            raw = A.resolve_path(path).read_bytes()
            return {'path': str(path.relative_to(PKG)), 'sha256': digest(raw), 'bytes': len(raw)}

        review_path = ROUND / 'planning/SAVED-RESULT-REVIEW.json'
        A.need(digest(review_path.read_bytes()) == REVIEW_SHA, 'exact independent saved-certificate review')
        review = A.read(review_path)
        A.need(review['review_status'] == 'PASS_SAVED_RECEIPT_REVIEW' and review['attempt_rewritten'] is False and
               review['candidate_words_reconstructed'] is False,
               'independent review remains a saved-certificate review only')
        inputs = {
            'original_run': ref(oldrun / 'RUN.json'),
            'original_results': oldmeta['results'],
            'preregistration': ref(ROUND / 'F1/PREREGISTRATION.json'),
            'implementation_pins': ref(ROUND / 'F1/IMPLEMENTATION-PINS-v1.json'),
            'storage_registration': ref(ROUND / 'F1/STORAGE-RECONCILIATION-v1.json'),
            'relocation': ref(ROUND / A.FAMILY / 'RELOCATION.json'),
            'independent_saved_review': ref(review_path),
        }
        prior_errors = sorted((ROUND / 'F1-RECONCILIATION').glob('ADMIN-ERROR-*.json'))
        inputs['preserved_administrative_errors'] = [ref(p) for p in prior_errors]
        failed_cpu = sum(A.read(p)['administrative_cpu_seconds'] for p in prior_errors)
        A.references(inputs)
        elapsed = time.process_time() - started
        total_admin_cpu = elapsed + failed_cpu
        recorded = datetime.now(timezone.utc).isoformat()
        common = dict(schema_version=1, experiment='F1-RECONCILIATION', milestone='CONTINUATION-08',
                      status='NULL', confirmed=True, scientific_decision_agreement=True,
                      original_attempt_status='ERROR', scientific_rerun=False,
                      scientific_cpu_seconds_added=0, n_permutations=0,
                      source_sha256=sources, inputs=inputs, domain=domain,
                      decision=dict(pattern_claim=False, kappa_claim=False,
                                    rule='Original F1 completed-domain zero-favorable/zero-unresolved rule; both seeds agree.',
                                    scope='Protocol-specific finite A/B carrier-factorization NULL only.'),
                      recorded_utc=recorded)
        outputs = {}
        result_refs = []
        for seed in sorted(A.SEEDS):
            old = oldresults[seed]
            result = dict(common, seed=seed, cpu_seconds=0,
                          administrative_cpu_seconds_shared_run=total_admin_cpu,
                          source_attribution=old['source_attribution'], provenance=old['provenance'],
                          word_blob_ids=old['word_blob_ids'], script_sha256=old['script_sha256'],
                          preregistration_sha256=old['preregistration_sha256'],
                          implementation_pins_sha256=old['implementation_pins_sha256'],
                          source_experiment_cpu_seconds=old['cpu_seconds'],
                          task_receipts=old['task_receipts'],
                          administrative_kind='Saved-receipt reconciliation, not a new scientific run')
            path = DEST / ('seed-' + str(seed)) / 'RESULT.json'
            raw = encoded(result)
            outputs[path] = raw
            result_refs.append(dict(path=str(path.relative_to(PKG)), sha256=digest(raw), bytes=len(raw)))
        meta = dict(common, kind='Post-result administrative saved-receipt reconciliation',
                    administrative_cpu_seconds=total_admin_cpu, results=result_refs,
                    successful_verification_cpu_seconds=elapsed,
                    prior_failed_administrative_cpu_seconds=failed_cpu,
                    original_scientific_cpu_seconds=oldmeta['total_cpu_seconds'],
                    original_scientific_cpu_counted_once=True,
                    source_attribution=oldresults[min(A.SEEDS)]['source_attribution'],
                    checked_attempt=checked, storage_preservation=storage,
                    independent_saved_review_sha256=REVIEW_SHA)
        runpath = DEST / 'RUN.json'
        outputs[runpath] = encoded(meta)
        if runpath.exists():
            saved = A.read(runpath)
            A.need(saved['domain'] == domain and saved['source_sha256'] == sources and
                   saved['inputs'] == inputs and saved['status'] == 'NULL' and saved['confirmed'],
                   'immutable reconciliation still agrees with saved evidence')
            for result_ref in saved['results']:
                A.reference(result_ref)
            print(json.dumps(dict(status='PASS', decision='NULL', overwritten=False,
                                  run=ref(runpath)), sort_keys=True))
            return
        A.need(not any(p.exists() for p in outputs), 'no partial reconciliation output may be overwritten')
        added = sum(map(len, outputs.values()))
        global_bytes = sum(p.stat().st_size for p in (PKG / 'results').rglob('*') if p.is_file())
        round_bytes = sum(p.stat().st_size for p in ROUND.rglob('*') if p.is_file())
        A.need(global_bytes + added < 200000000 and round_bytes + added < 4000000,
               'new small receipts obey final compact storage limits')
        if args.write:
            for path, raw in outputs.items():
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open('xb') as stream:
                    stream.write(raw)
        reg = dict(status='NULL', confirmed=True,
                   result_files=[x['path'] for x in result_refs],
                   run=str(runpath.relative_to(PKG)), administrative_cpu_seconds=total_admin_cpu)
        print(json.dumps(dict(status='PASS', decision='NULL', written=args.write,
                              source_sha256=sources, run_sha256=digest(outputs[runpath]),
                              reconciliation=reg, domain=domain, new_result_bytes=added), sort_keys=True))
    except Exception as exc:
        failure = dict(schema_version=1, status='ERROR', kind='Administrative verification error',
                       recorded_utc=datetime.now(timezone.utc).isoformat(), scientific_rerun=False,
                       scientific_cpu_seconds_added=0, source_sha256=sources,
                       administrative_cpu_seconds=time.process_time()-started,
                       error_type=type(exc).__name__, error=str(exc), traceback=traceback.format_exc())
        if args.write:
            parent = ROUND / 'F1-RECONCILIATION'
            parent.mkdir(parents=True, exist_ok=True)
            path = parent / ('ADMIN-ERROR-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
            with path.open('xb') as stream:
                stream.write(encoded(failure))
        print(json.dumps(failure, sort_keys=True))
        raise


if __name__ == '__main__':
    main()
