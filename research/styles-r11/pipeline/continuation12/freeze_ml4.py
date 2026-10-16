"""Administrative source freeze and preregistration; no scientific imports."""
from datetime import datetime, timezone
from pathlib import Path
import ast
import gzip
import hashlib
import json

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-12'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return dict(path=str(path.relative_to(PKG)), sha256=sha(path), bytes=path.stat().st_size)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def main():
    recorded = datetime.now(timezone.utc).isoformat()
    data_description = json.loads((ROUND / 'planning/DATA-PROTOCOL.json').read_text())
    model_protocol = json.loads((ROUND / 'planning/ML-PROTOCOL.json').read_text())
    paths = set((PKG / 'pipeline').rglob('*.py'))
    # These are existing trusted local dependencies, not newly fetched programs.
    for relative in ('research/t74-r10-hosting-leads/J-dim1/code',
                     'research/t74-r10-hosting-leads/deps/toolkit-rev3',
                     'research/frame-domain-ceiling/vendor/static44/gk',
                     'research/t74-joint-twelve-retired7'):
        paths.update((ROOT / relative).rglob('*.py'))
    # Preserve the previously audited import closure as an additional path set.
    inherited = json.loads((PKG / 'results/CONTINUATION-11/J2/IMPLEMENTATION-PINS-v1.json').read_text())
    paths.update(ROOT / name for name in inherited['sha256'])
    archive_index = {}
    for path in (PKG / 'results').glob('**/SOURCES/*.py.gz'):
        archive_index.setdefault(path.name.removesuffix('.py.gz'), path)
    pins, archives = {}, {}
    for path in sorted(paths):
        if not path.is_file():
            raise FileNotFoundError(path)
        raw = path.read_bytes()
        ast.parse(raw, filename=str(path))
        digest = hashlib.sha256(raw).hexdigest()
        pins[str(path.relative_to(ROOT))] = digest
        if digest in archives:
            continue
        archive = archive_index.get(digest)
        if archive is None:
            archive = PKG / 'data/continuation-12/source-archives' / (digest + '.py.gz')
            archive.parent.mkdir(parents=True, exist_ok=True)
            if archive.exists():
                raise FileExistsError(archive)
            archive.write_bytes(gzip.compress(raw, mtime=0))
        if gzip.decompress(archive.read_bytes()) != raw:
            raise ValueError('source archive mismatch: ' + str(path))
        archives[digest] = ref(archive)
    manifest = dict(schema_version=1, frozen_utc=recorded, sha256=pins, archives=archives,
                    imports_before_freeze=False, scientific_preparation_before_freeze=False,
                    archive_policy='Existing authenticated snapshots reused; new snapshots under continuation-12 data.')
    pin_path = ROUND / 'ML4/IMPLEMENTATION-PINS-v1.json'
    save(pin_path, manifest)
    input_paths = dict(
        original_pins='data/words/PINS.json',
        pr2853='data/heldout/2853/DATA-MANIFEST.json',
        pr2917='data/continuation-01/pr2917/MANIFEST.json',
        pr2979='data/continuation-05/pr2979/ACQUISITION.json',
        pr2979_package='data/continuation-05/pr2979/package/MANIFEST.json',
        latest_checkpoint='data/continuation-12/checkpoint/RECEIPT.json',
        allocation_source='data/continuation-12/allocation-source/ACQUISITION.json',
        data_protocol='results/CONTINUATION-12/planning/DATA-PROTOCOL.json',
        model_protocol='results/CONTINUATION-12/planning/ML-PROTOCOL.json',
        plan='PLAN.md')
    protocol = dict(
        schema_version=1, state='FROZEN', experiment='ML4-HISTORICAL-EXCHANGE',
        milestone='CONTINUATION-12/ML4', registered_utc=recorded,
        scope='Retrospective exact owner-exchange prediction across three related historical T74 allocations. This measures screening associations and their limits; it does not construct or admit a new kappa improvement, establish causality, or provide independent-lineage evidence.',
        changed_premise='Replace selected-success PR-level regression with an outcome-enriched, probability-weighted candidate corpus including gains, ties, losses, and illegal proposals. Previously closed constructor domains are not reopened.',
        sources=[2853, 2917, 2979], seeds=[61001, 122011], corpus_seed=120071,
        data_protocol=data_description['protocol'], feature_schema=data_description['feature_schema'],
        model_protocol=model_protocol, n_permutations=2000,
        inputs={name: ref(PKG / path) for name, path in input_paths.items()},
        initial_implementation_pins=ref(pin_path),
        queue=dict(generation=504, data_controls=2, model_controls=2,
                   observed=72, learning_curves=120, unshuffled_benchmark=2, label_shuffles=4000,
                   policy='All independent tasks of a phase are queued to the single common pool; successful validation advances automatically. No discretionary pause between batches.'),
        controls=['Unchanged complete literal fills/profile/mass/physical family/window audits for all three historical sources.',
                  'Known admitted PR2917 exchange and independent direct literal-predicate checks.',
                  'Synthetic beneficial, harmful, equal-width tie, same-bin tie, capacity, window and family cases.',
                  'Exact S versus uniform union coverage and probabilities; canonical pair and source binding; identical corpus under two execution traversals.',
                  'Weighted ranking tie/perfect/reversed controls, train-only preprocessing, prior correction, nested label-blind panels and within-stratum shuffle counts.',
                  'Full sources, stable physical call/family endpoint split, and explicitly chronological-index pair-purge sensitivity.'],
        assessment='Scientific status remains EXPLORATORY. Integrity controls may PASS. Assess every fixed model and learning curve, including adverse/degenerate results. No model or feature selection from outcomes. Full exact guard oracle is the target definition, not evidence of a discovery. The stratum baseline prevents credit for simply rediscovering necessary gain geometry.',
        pattern_criteria='All five PLAN section6 criteria remain required. This related historical corpus and cost-derived mechanism comparator do not satisfy them; no formal pattern, p-value, q-value, causal effect or kappa claim will be promoted. The 2000 shuffles per seed are descriptive matched benchmarks only.',
        confirmation='Both execution seeds reproduce the same canonical corpus and deterministic observed models/learning curves/unshuffled benchmark. Shuffle sequences are separately seeded. Repeated computation never increases the number of independent observations.',
        stop_rules='A failed control, missing shard, storage/memory projection failure, task error/timeout or budget cutoff stops dependent work and preserves partial receipts. No silent retries or outcome-driven domain/model changes. At most one separately registered changed-premise pivot this round; two consecutive scientific nulls stop their lane. Prior string/constructor/growth stops remain in force.',
        science_launch_cutoff_utc='2026-10-17T00:00:00+00:00', hard_stop_utc='2026-10-17T00:15:00+00:00',
        resources=dict(cpu_budget_seconds_family=110000, round_cpu_budget_seconds=120000,
                       expected_workers=61, workers='min(120,floor(RAM_GiB/4))', allocated_cores=128,
                       reserved_cores=8, per_task_timeout_seconds=300, per_worker_rss_gib=4,
                       fill_worker_rss_gib=6, generation_working_set_gib=0.8, model_working_set_gib=0.8,
                       one_pool=True, parent_load_once=True, blas_threads=1,
                       generation_rows_per_fill_cap=2000000, result_bytes_cap=200000000,
                       new_result_bytes_cap=1000000, new_data_bytes_cap=1073741824,
                       sample_cpu_rss_seconds=2, sample_pss_seconds=10,
                       preparation_projection='Project parent corpus/array memory before allocation; project complete pool peak before every launch. Record measured RSS/PSS and CPU/core-equivalents separately from configured workers.'),
        attribution='Every RESULT retains all original data/words/PINS.json credits and the complete historical source provenance. PR2853, Mason Hale PR2917, Marius-Paul Dumitrean PR2979 and retained predecessor/toolkit/auditor authors remain credited.',
        publication='Only authored small commits and push to mdumitrean/integer-mult-bounds:research/styles-r11-results. No PRs, comments, discussions, or other GitHub writes.',
        ai_assistance='Substantial OpenAI Codex assistance in implementation, checking and analysis; no AI commit-attribution trailers.')
    preg = ROUND / 'ML4/PREREGISTRATION.json'
    save(preg, protocol)
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    row = registry['experiments'][0]
    row.update(preregistration_sha256=sha(preg), implementation_pins=ref(pin_path))
    registry['status'] = 'REGISTERED_READY'
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_SCIENCE', preregistration_sha256=sha(preg),
                          implementation_pins_sha256=sha(pin_path), source_files=len(pins),
                          archives=len(archives), registered_utc=recorded)))


if __name__ == '__main__':
    main()
