"""Provenance, immutable run records, preregistration and decision bookkeeping."""
from datetime import datetime, timezone
import hashlib
import gzip
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
RESULTS = PKG / 'results'
STATUSES = {'PASS', 'NULL', 'TIMEOUT', 'ERROR', 'EXPLORATORY'}


def utcnow():
    return datetime.now(timezone.utc).isoformat()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value, *, immutable=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if immutable and path.exists():
        raise FileExistsError('immutable result already exists: ' + str(path))
    temp = path.with_name('.tmp-' + path.name)
    temp.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
    os.replace(temp, path)


def pins():
    return json.loads((PKG / 'data/words/PINS.json').read_text())['files']


def provenance(names=None):
    items = pins()
    names = list(items) if names is None else names
    return [dict(path=name, **items[name]) for name in names]


def source_manifest():
    # Preserve the bytes used by each run even while unrelated modules evolve.
    manifest = {}
    directory = RESULTS / 'SOURCES'
    directory.mkdir(parents=True, exist_ok=True)
    for path in sorted((PKG / 'pipeline').glob('*.py')):
        content = path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        manifest[str(path.relative_to(ROOT))] = digest
        archive = directory / (digest + '.py.gz')
        if not archive.exists():
            archive.write_bytes(gzip.compress(content, mtime=0))
    return manifest


def registry_update(experiment, status, **extra):
    if status not in STATUSES | {'planned', 'running'}:
        raise ValueError(status)
    path = PKG / 'EXPERIMENTS.json'
    data = json.loads(path.read_text())
    row = next(x for x in data['experiments'] if x['id'] == experiment)
    row.update(status=status, updated_utc=utcnow(), **extra)
    write_json(path, data)


def preregistration(milestone, experiment):
    path = RESULTS / milestone / 'PREREGISTRATION.json'
    data = json.loads(path.read_text())
    assert experiment in data['experiments'], experiment
    return path, data['experiments'][experiment]


def run_record(experiment, milestone, seed, status, statistics,
               *, n=0, null=None, wall_seconds=0, cpu_seconds=0,
               peak_rss_bytes=None, words=None, decision=None,
               run_id=None, additional=None, scripts=None):
    assert status in STATUSES
    preg, protocol = preregistration(milestone, experiment)
    script = source_manifest() if scripts is None else scripts
    result = dict(schema_version=1, experiment=experiment, milestone=milestone,
                  recorded_utc=utcnow(), seed=seed, n_permutations=n,
                  word_blob_ids={p['path']: p['git_blob'] for p in provenance(words)},
                  source_attribution=provenance(words), script_sha256=script,
                  script_manifest_sha256=hashlib.sha256(json.dumps(script, sort_keys=True).encode()).hexdigest(),
                  preregistration_sha256=sha256(preg),
                  wall_seconds=wall_seconds, cpu_seconds=cpu_seconds,
                  peak_rss_bytes=peak_rss_bytes, statistics=statistics,
                  null_summary=null or {'model': 'none (exact check)', 'mean': None, 'sd': None, 'empirical_p': None},
                  decision=decision or {'pass_bar': protocol.get('pass_bar'), 'verdict': status},
                  status=status, confirmation_required=True,
                  scope='Finite scoped evaluation; potential kappa levers are census targets only.')
    if additional:
        result.update(additional)
    path = RESULTS / experiment / (run_id or ('seed-' + str(seed))) / 'RESULT.json'
    write_json(path, result, immutable=True)
    return path


def confirm(experiment, paths):
    runs = [json.loads(Path(p).read_text()) for p in paths]
    statuses = {r['status'] for r in runs}
    ok = len({r['seed'] for r in runs}) >= 2 and len(statuses) == 1
    status = runs[0]['status'] if ok else 'EXPLORATORY'
    registry_update(experiment, status,
                    confirmed=ok and status in {'PASS', 'NULL'},
                    result_files=[str(Path(p).relative_to(PKG)) for p in paths],
                    confirmation_note='Two different seeds agree.' if ok else 'Decisions differ or confirmation is missing.')
    return status


def bh_fdr(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    q = [1.0] * len(ps)
    ceiling = 1.0
    for j in range(len(order) - 1, -1, -1):
        i = order[j]
        ceiling = min(ceiling, ps[i] * len(ps) / (j + 1))
        q[i] = ceiling
    return q


def permutation_summary(real, samples, *, larger_better=True):
    import statistics
    samples = list(samples)
    exceed = sum(x >= real if larger_better else x <= real for x in samples)
    return dict(mean=statistics.mean(samples), sd=statistics.pstdev(samples),
                empirical_p=(1 + exceed) / (1 + len(samples)), n=len(samples),
                score_direction='larger' if larger_better else 'smaller',
                minimum=min(samples), maximum=max(samples))
