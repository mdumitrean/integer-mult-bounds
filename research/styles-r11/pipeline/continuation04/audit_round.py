"""Administrative byte/receipt audit; does not run a scientific experiment."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG/'results/CONTINUATION-04'
BASE = '875e31d7346ba87b640edb7c9155e928b742d187'


def need(test, message):
    if not test:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def reference(ref):
    path = (PKG/ref['path']).resolve()
    need(path.is_relative_to(PKG), 'artifact confinement')
    raw = path.read_bytes()
    need(sha(raw) == ref['sha256'], 'artifact hash: '+ref['path'])
    if 'bytes' in ref:
        need(len(raw) == ref['bytes'], 'artifact byte count')
    return path


def main():
    start = time.process_time()
    registry = read(ROUND/'EXPERIMENTS.json')
    need(registry['no_active_experiments'], 'all pools terminal')
    original = read(PKG/'data/words/PINS.json')['files']
    reports, total_tasks, total_cpu, archives = {}, 0, 0., set()
    for label, experiment in (('E1','E1-ADJACENT-EXPANSIONS'), ('E2','E2-OTHER-CORRECTION-POSITIONS')):
        row = next(x for x in registry['experiments'] if x['id'] == experiment)
        need(row['execution'] == 'COMPLETED', 'complete family execution')
        run = ROUND/experiment/'v1'
        meta = read(run/'RUN.json')
        protocol_path = ROUND/label/'PREREGISTRATION.json'
        protocol, implementation = read(protocol_path), read(run/'IMPLEMENTATION.json')
        preg_sha = sha(protocol_path.read_bytes())
        need(preg_sha == row['preregistration_sha256'] == implementation['preregistration_sha256'], 'frozen registration')
        need(datetime.fromisoformat(protocol['registered_utc']) <= datetime.fromisoformat(implementation['frozen_utc']), 'preregistration precedes preparation')
        need(meta['source_implementation_sha256'] == sha((run/'IMPLEMENTATION.json').read_bytes()), 'run implementation binding')
        frozen_path = ROUND/label/'IMPLEMENTATION-PINS-v1.json'
        frozen = read(frozen_path)
        need(sha(frozen_path.read_bytes()) == implementation['implementation_pins_sha256'], 'pre-execution pin binding')
        need(datetime.fromisoformat(frozen['recorded_utc']) <= datetime.fromisoformat(implementation['frozen_utc']), 'source freeze precedes execution')
        for name, expected in implementation['script_sha256'].items():
            need(frozen['sha256'].get(name) == expected, 'executed source was prepinned: '+name)
            need(sha((ROOT/name).read_bytes()) == expected, 'executed source unchanged: '+name)
            archive = ROUND/'SOURCES'/(expected+'.py.gz')
            need(sha(gzip.decompress(archive.read_bytes())) == expected, 'archived exact source bytes')
            archives.add(expected)
        for ref in protocol['inputs'].values():
            path = (ROOT if ref['path_base'] == 'repository' else PKG)/ref['path']
            need(sha(path.read_bytes()) == ref['sha256'], 'registered input bytes unchanged')
        phases = {name:read(run/(name.upper()+'-TASKS.json.gz')) for name in meta['completed_by_phase']}
        seen, seeds, statuses, cpu, peaks, max_seconds = set(), set(), set(), 0., [], 0.
        counts, profile_kinds = Counter(), Counter()
        for ref in meta['results']:
            result = read(reference(ref))
            seed = result['seed']
            need(seed not in seeds, 'distinct confirmation seed')
            seeds.add(seed); statuses.add(result['status']); cpu += result['cpu_seconds']
            need(result['preregistration_sha256'] == preg_sha, 'seed registration binding')
            need(result['script_sha256'] == implementation['script_sha256'], 'seed implementation binding')
            need(result['source_provenance'] == implementation['source_provenance'], 'seed source-credit binding')
            credits = {x['path']:x for x in result['source_attribution']}
            for name, credit in original.items():
                need(name in credits and all(credits[name].get(k) == v for k,v in credit.items()), 'all inherited source credits retained')
            need(len(credits) == 23, '21 original plus two current word credits')
            for task in result['task_receipts']:
                path = reference(task)
                need(str(path) not in seen, 'unique task receipt')
                seen.add(str(path))
                phase = path.parent.name
                index = int(path.name.split('.')[0].split('-')[-1])
                spec = phases[phase][index]
                receipt = read(path)
                need(receipt['status'] == 'OK', 'all completed pool tasks OK')
                value = receipt['result']
                need(value['seed'] == seed == spec['seed'], 'task belongs to recorded seed')
                peaks.append(receipt['peak_rss_bytes'])
                max_seconds = max(max_seconds, receipt['seconds'])
                counts[phase, value['status']] += 1
                if phase == 'price' and value.get('moment_delta') is not None:
                    profile_kinds['identical' if value['moment_delta']['exact_profile_identity'] else 'different'] += 1
        need(seeds == set(protocol['seeds']), 'both registered seeds present')
        need(statuses == {meta['status']} == {row['status']}, 'all status records agree')
        need(abs(cpu-meta['total_cpu_seconds']) < 1e-5, 'per-seed CPU accounting closes')
        need(len(seen) == sum(meta['completed_by_phase'].values()), 'all pool receipts accounted for')
        for phase, specs in phases.items():
            need(len(specs) == meta['completed_by_phase'][phase], 'complete phase coverage')
            projection = read(run/(phase.upper()+'-MEMORY-PROJECTION.json'))
            need(projection['workers'] == 61 and projection['reserved_cores'] == 8, 'registered worker allocation')
            need(projection['projected_peak_gib'] < projection['ram_gib'], 'projected memory within RAM')
            need(projection['projected_per_worker_gib'] < 4 and projection['worker_rss_cap_gib'] == 4, 'per-worker memory cap')
        need(max(peaks,default=0) < 4*(1<<30) and max_seconds < 300, 'observed tasks within caps')
        reports[experiment] = dict(status=meta['status'],confirmed=meta['confirmed'],seeds=sorted(seeds),
            pool_tasks=len(seen),outcomes=[dict(phase=p,status=s,count=n) for (p,s),n in sorted(counts.items())],
            priced_profile_kinds=dict(profile_kinds),cpu_seconds=cpu,wall_seconds=meta['total_wall_seconds'],
            peak_rss_bytes=max(peaks,default=0),longest_task_seconds=max_seconds,source_credits_per_result=23)
        total_tasks += len(seen); total_cpu += cpu
    need(total_cpu < 14400, 'round CPU budget')
    acquisition = read(PKG/'data/continuation-04/pr2966/ACQUISITION.json')
    for pin in acquisition['files']:
        path = PKG/pin['local_path']
        raw = path.read_bytes()
        need(len(raw)==pin['bytes'] and sha(raw)==pin['sha256'], 'all acquired package bytes preserved')
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==pin['git_blob'], 'acquired Git blob')
        need(path.suffix != '.py', 'fetched programs remain inert text')
    tree = subprocess.check_output(['git','ls-tree','-rz',BASE,'--','research/styles-r11/'],cwd=ROOT)
    preserved = 0
    for entry in tree.split(b'\0'):
        if not entry:
            continue
        info, name = entry.split(b'\t',1)
        _, kind, blob = info.split()
        need(kind==b'blob','ordinary frozen evidence file')
        raw = (ROOT/name.decode()).read_bytes()
        need(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest().encode()==blob, 'pre-round file preserved: '+name.decode())
        preserved += 1
    changed = subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT).decode().splitlines()
    untracked = subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT).decode().splitlines()
    need(all(x.startswith('research/styles-r11/') for x in changed+untracked), 'all edits within authorized subtree')
    size = sum(x.stat().st_size for x in (PKG/'results').rglob('*') if x.is_file())
    need(size < 200000000, 'RUNBOOK results storage cap')
    output = dict(schema_version=1,status='PASS',kind='administrative byte and receipt audit; no new scientific tests',
        recorded_utc=datetime.now(timezone.utc).isoformat(),script_sha256=sha(Path(__file__).read_bytes()),
        base_work_commit=BASE,preserved_pre_round_files=preserved,experiments=reports,
        total_pool_tasks=total_tasks,total_experimental_cpu_seconds=total_cpu,
        distinct_prepinned_source_archives=len(archives),results_bytes_before_audit=size,
        current_source_package_files=len(acquisition['files']),administrative_cpu_seconds=time.process_time()-start)
    with (ROUND/'AUDIT.json').open('x') as handle:
        json.dump(output,handle,indent=2,sort_keys=True);handle.write('\n')
    print(json.dumps(output,sort_keys=True))


if __name__ == '__main__':
    main()
