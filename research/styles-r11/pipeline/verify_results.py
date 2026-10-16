#!/usr/bin/env python3
"""Read-only integrity review of immutable experiment receipts and provenance.

This verifies recorded evidence, not a fresh scientific test. It does not run
solvers, import fetched files, regenerate samples, or change experiment verdicts.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import records as R


def review(require_complete=True):
    errors, notes = [], []
    pins = R.pins()
    for name, pin in pins.items():
        path = R.ROOT / name if '/' in name else R.PKG / 'data/words' / name
        raw = path.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        if hashlib.sha256(raw).hexdigest() != pin['sha256'] or blob != pin['git_blob']:
            errors.append('pinned word identity changed: ' + name)
    registrations = {R.sha256(p): p for p in R.RESULTS.glob('**/*PREREGISTRATION*.json')}
    registrations.update({R.sha256(p): p for p in R.RESULTS.glob('**/PREREGISTRATION.json')})
    records, missing_sources = {}, {}
    required = {'experiment','milestone','seed','word_blob_ids','source_attribution',
                'script_sha256','preregistration_sha256','n_permutations',
                'wall_seconds','cpu_seconds','peak_rss_bytes','statistics',
                'null_summary','decision','status'}
    archives = {}
    for path in R.RESULTS.glob('**/RESULT.json'):
        relative = str(path.relative_to(R.PKG))
        value = json.loads(path.read_text())
        records[relative] = value
        absent = required - value.keys()
        if absent:
            errors.append(relative + ': missing fields ' + repr(sorted(absent)))
            continue
        if value['status'] not in R.STATUSES:
            errors.append(relative + ': invalid status')
        if value['preregistration_sha256'] not in registrations:
            errors.append(relative + ': missing original preregistration')
        else:
            frozen = json.loads(registrations[value['preregistration_sha256']].read_text())
            if value['experiment'] not in frozen['experiments']:
                errors.append(relative + ': experiment absent from preregistration')
            if frozen.get('registered_utc','') > value.get('recorded_utc','z'):
                errors.append(relative + ': preregistration postdates result')
        for metric in ('cpu_seconds','wall_seconds','n_permutations'):
            if value[metric] < 0:
                errors.append(relative + ': negative ' + metric)
        for source in value['source_attribution']:
            name = source['path']
            if name in pins:
                for key, expected in pins[name].items():
                    if source.get(key) != expected:
                        errors.append(relative + ': changed PINS attribution ' + name + ':' + key)
            if value['word_blob_ids'].get(name) != source['git_blob']:
                errors.append(relative + ': blob/attribution mismatch ' + name)
        manifest = value['script_sha256']
        if hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest() != value.get('script_manifest_sha256'):
            errors.append(relative + ': script manifest digest mismatch')
        for source, digest in manifest.items():
            archive = R.RESULTS / 'SOURCES' / (digest + '.py.gz')
            if digest not in archives:
                if archive.exists():
                    archives[digest] = hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest
                elif (R.ROOT/source).exists() and R.sha256(R.ROOT/source) == digest:
                    archives[digest] = True
                else:
                    archives[digest] = None
            if archives[digest] is False:
                errors.append(relative + ': corrupt source archive ' + digest)
            elif archives[digest] is None:
                missing_sources.setdefault(digest,dict(path=source,receipts=[]))['receipts'].append(relative)
        if value.get('statistics',{}).get('not_run'):
            if value['n_permutations'] or value['cpu_seconds'] or value['status'] != 'EXPLORATORY':
                errors.append(relative + ': unrun item reported as executed')
    registry = json.loads((R.PKG/'EXPERIMENTS.json').read_text())['experiments']
    for row in registry:
        if require_complete and row['status'] in ('planned','running'):
            errors.append(row['id'] + ': incomplete registry status')
        linked = row.get('result_files',[])
        if row['status'] in ('PASS','NULL'):
            if not row.get('confirmed'):
                errors.append(row['id'] + ': unconfirmed scientific decision')
            runs = [records[p] for p in linked if p in records]
            if len({r['seed'] for r in runs}) < 2 or {r['status'] for r in runs} != {row['status']}:
                errors.append(row['id'] + ': invalid second-seed confirmation')
        for link in linked:
            if link not in records:
                errors.append(row['id'] + ': missing result ' + link)
    total_bytes = sum(p.stat().st_size for p in R.RESULTS.rglob('*') if p.is_file())
    if total_bytes >= 200*1000*1000:
        errors.append('results/ reaches the 200 MB limit')
    projections=[]
    for path in R.RESULTS.glob('**/*MEMORY-PROJECTION*.json'):
        projections.append(str(path.relative_to(R.PKG)))
    if missing_sources:
        notes.append('Historical manifest entries without an archive/current match need Git-history recovery or an explicit scope review.')
    return dict(status='PASS' if not errors and not missing_sources else 'REVIEW_REQUIRED',
        reviewed_utc=R.utcnow(),errors=errors,notes=notes,
        pinned_word_count=len(pins),result_count=len(records),experiment_count=len(registry),
        receipt_status_counts=dict(Counter(r['status'] for r in records.values())),
        recorded_cpu_seconds=sum(r.get('cpu_seconds',0) for r in records.values()),
        recorded_cpu_hours=sum(r.get('cpu_seconds',0) for r in records.values())/3600,
        compute_scope='Sum of measured RESULT receipts, including failures and validation runs. Consult explicit missing worker-CPU caveats for the native P3 abort; orchestration/review time is not included.',
        result_bytes=total_bytes,source_digest_count=len(archives),missing_source_archives=missing_sources,
        memory_projection_files=projections,
        source_attribution=R.provenance(),
        scientific_scope='Integrity review only; does not promote exploratory, skipped, or protocol-specific results.')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--allow-incomplete',action='store_true')
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=review(require_complete=not args.allow_incomplete)
    if args.output:
        if not args.output.resolve().is_relative_to(R.RESULTS):
            raise ValueError('review output must remain inside results/')
        R.write_json(args.output,result,immutable=True)
    print(json.dumps({k:v for k,v in result.items() if k not in ('source_attribution','memory_projection_files','missing_source_archives')},indent=2))
    print('missing_source_archives',len(result['missing_source_archives']))
    raise SystemExit(bool(result['errors']))
