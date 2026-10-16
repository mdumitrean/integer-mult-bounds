"""Administrative audit of saved continuation12 evidence; no scientific imports."""
from datetime import datetime, timezone
from pathlib import Path
import gzip
import hashlib
import json
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-12'
DATA = PKG / 'data/continuation-12'
BASE = '2e8dfbfc56be5a808443643fa9928494e779f43e'
CHECKED = set()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def reference(ref):
    name = ref['path']
    path = (ROOT / name if name.startswith('research/styles-r11/') else PKG / name).resolve()
    need(path.is_relative_to(PKG), 'artifact confined to package')
    raw = path.read_bytes()
    need(hashlib.sha256(raw).hexdigest() == ref['sha256'], 'artifact digest: ' + name)
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'artifact bytes: ' + name)
    if 'payload_sha256' in ref:
        payload = gzip.decompress(raw) if path.suffix == '.gz' else raw
        need(hashlib.sha256(payload).hexdigest() == ref['payload_sha256'], 'payload digest: ' + name)
    CHECKED.add(str(path.relative_to(PKG)))
    return path


def references(value):
    if isinstance(value, dict):
        if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
            if value['path'].startswith(('data/', 'pipeline/', 'results/', 'research/styles-r11/')):
                reference(value)
        for item in value.values():
            references(item)
    elif isinstance(value, list):
        for item in value:
            references(item)


def main():
    start = time.process_time()
    registry = read(ROUND / 'EXPERIMENTS.json')
    need(registry['no_active_experiments'], 'no active science')
    need(all(row.get('execution') in ('COMPLETED', 'INCOMPLETE') for row in registry['experiments']),
         'all registered experiments have preserved terminal attempts')
    originals = read(PKG / 'data/words/PINS.json')['files']
    families = []
    for row in registry['experiments']:
        prereg = PKG / row['preregistration']
        need(sha(prereg) == row['preregistration_sha256'], 'registration unchanged')
        protocol = read(prereg)
        need(protocol['state'] == 'FROZEN', 'registration frozen')
        references(protocol['inputs'])
        manifest_path = reference(row['implementation_pins'])
        manifest = read(manifest_path)
        for name, digest in manifest['sha256'].items():
            need(sha(ROOT / name) == digest, 'scientific source unchanged: ' + name)
            archive = reference(manifest['archives'][digest])
            need(hashlib.sha256(gzip.decompress(archive.read_bytes())).hexdigest() == digest,
                 'archived exact source preimage')
        need(datetime.fromisoformat(protocol['registered_utc']) <= datetime.fromisoformat(row['started_utc']),
             'registration precedes execution')
        need(datetime.fromisoformat(manifest['frozen_utc']) <= datetime.fromisoformat(row['started_utc']),
             'source freeze precedes execution')
        results = [read(PKG / name) for name in row['result_files']]
        need({r['seed'] for r in results} == set(protocol['seeds']), 'both registered seeds preserved')
        for result in results:
            need(result['status'] == row['status'] and result['confirmed'] == row['confirmed'], 'registry/result verdict')
            need(result['preregistration_sha256'] == sha(prereg), 'result registration binding')
            credit = {v['path']: v for v in result['source_attribution']}
            for name, pin in originals.items():
                need(name in credit and all(credit[name].get(k) == v for k, v in pin.items()),
                     'original PINS credit retained: ' + name)
            references(result)
        need(abs(sum(r['cpu_seconds'] for r in results) - row['attempts'][-1]['cpu_seconds']) < 1e-6,
             'seed CPU partition reconciles latest attempt')
        families.append(dict(id=row['id'], status=row['status'], execution=row['execution'],
            confirmed=row['confirmed'], sources=len(manifest['sha256']), results=row['result_files'],
            cpu_seconds=row['cpu_seconds'], wall_seconds=row['wall_seconds']))
    ml = read(DATA / 'ml4-v1/RUN.json')
    tasks = read(DATA / 'ml4-v1/ALL-TASKS.json.gz')
    need(len(tasks) == sum(ml['completed_by_phase'].values()) == 4702, 'ML4 complete task accounting')
    for row in tasks:
        result = read(reference(row))
        need(row['status'] == result['status'] == 'OK', 'ML4 task status')
    raw = read(DATA / 'RAW-ARTIFACTS.json')
    references(raw)
    need(len(raw['files']) == 504 and raw['total_bytes'] == sum(r['bytes'] for r in raw['files']),
         'large local arrays accounted and reproducible')
    tracked_arrays = subprocess.check_output(['git', 'ls-files', 'research/styles-r11/data/continuation-12/ml4-v1/numeric'], cwd=ROOT)
    need(not tracked_arrays, 'large numeric arrays outside Git')
    allowed = ('research/styles-r11/pipeline/continuation12/',
               'research/styles-r11/data/continuation-12/', 'research/styles-r11/results/CONTINUATION-12/')
    changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--'], cwd=ROOT, text=True).splitlines()
    need(all(name.startswith(allowed) for name in changed), 'all pre-round tracked bytes immutable')
    sizes = {name: sum(f.stat().st_size for f in directory.rglob('*') if f.is_file())
             for name, directory in [('results', PKG / 'results'), ('round_results', ROUND), ('round_data', DATA)]}
    need(sizes['results'] < 200000000 and sizes['round_results'] < 1000000 and
         sizes['round_data'] < 1073741824, 'storage caps')
    for name in ('RESULTS.md', 'HANDBACK.md', 'PREDICTIONS.json', 'EXPERIMENTS.json'):
        need((ROUND / name).is_file(), 'required round deliverable: ' + name)
    report = dict(status='PASS_SAVED_EVIDENCE_AUDIT', recorded_utc=datetime.now(timezone.utc).isoformat(),
        scope='Saved bytes, immutable source/input pins, attribution, per-task status, CPU accounting, storage and write scope. No scientific rerun or new admission.',
        base_commit=BASE, families=families, source_attribution_original_files=len(originals),
        checked_artifact_references=len(CHECKED), ml4_tasks=4702,
        large_arrays_local_only=dict(files=504, bytes=raw['total_bytes']),
        old_tracked_files_unchanged=True, changed_paths=len(changed), storage_bytes_before_audit=sizes,
        total_scientific_cpu_seconds=sum(row['cpu_seconds'] for row in registry['experiments']),
        administrative_cpu_seconds=time.process_time()-start,
        machine_policy='61 workers under standing min(120,floor(RAM_GiB/4)); one central pool;8 reserved cores; no inference of memory saturation.',
        telemetry_correction='ML4 instantaneous91.8425 estimate invalid from sampling timestamp skew. Joined-phase CPU/wall and saved RSS/PSS interpretation retained.',
        kappa_claim=False, pattern_claim=False,
        ai_assistance='Substantial OpenAI Codex assistance in implementation and analysis.')
    target = ROUND / 'AUDIT.json'
    with target.open('x') as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(status=report['status'], sha256=sha(target), checked_refs=len(CHECKED),
        scientific_cpu_seconds=report['total_scientific_cpu_seconds'])))


if __name__ == '__main__':
    main()
