"""Administrative S3 registration and source archival, with no scientific imports."""
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path
import ast
import gzip
import hashlib
import json

PKG = Path(__file__).resolve().parents[2]
ROOT = PKG.parents[1]
ROUND = PKG / 'results/CONTINUATION-14'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ref(path):
    return dict(path=str(path.relative_to(PKG)), sha256=sha(path), bytes=path.stat().st_size)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def main():
    recorded = datetime.now(timezone.utc).isoformat()
    review_path = ROUND / 'planning/SPLIT-REVIEW.json'
    review = json.loads(review_path.read_text())
    assert review['status'] == 'PASS_STATIC', 'independent implementation review before freeze'
    for name in ('split_residual.py', 'run_split.py'):
        source = PKG / 'pipeline/continuation14' / name
        assert review['source_sha256'][str(source.relative_to(ROOT))] == sha(source), 'review binds final implementation bytes'
    previous_path = PKG / 'results/CONTINUATION-12/R2/IMPLEMENTATION-PINS-v1.json'
    previous = json.loads(previous_path.read_text())
    paths = {ROOT / name for name in previous['sha256']}
    paths.update((PKG / 'pipeline/continuation14').glob('*.py'))
    paths.add(PKG / 'pipeline/resources13/measured_pool.py')
    archives, pins = dict(previous['archives']), {}
    for path in sorted(paths):
        raw = path.read_bytes()
        ast.parse(raw, filename=str(path))
        digest = hashlib.sha256(raw).hexdigest()
        relative = str(path.relative_to(ROOT))
        if relative in previous['sha256']:
            assert digest == previous['sha256'][relative], 'historical source must remain byte-immutable'
        pins[relative] = digest
        if digest not in archives:
            target = PKG / 'data/continuation-14/source-archives' / (digest + '.py.gz')
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(gzip.compress(raw, mtime=0))
            archives[digest] = ref(target)
        assert gzip.decompress((PKG / archives[digest]['path']).read_bytes()) == raw
    pin_path = PKG / 'data/continuation-14/IMPLEMENTATION-PINS-v1.json'
    save(pin_path, dict(schema_version=1, frozen_utc=recorded, sha256=pins, archives=archives,
        previous_manifest=ref(previous_path), imports_before_freeze=False,
        scientific_preparation_before_freeze=False,
        archive_policy='All scientific sources and inherited dependencies authenticated before import; fetched PR code remains inert.'))
    # Retain the audited adapter's exact baseline and recording conventions.
    protocol = json.loads((PKG / 'results/CONTINUATION-12/R2/PREREGISTRATION.json').read_text())
    protocol.update(experiment='S3-SPLIT-RESIDUAL-CARRIER', milestone='CONTINUATION-14/S3',
        registered_utc=recorded, scope='Finite exact audit of two ordered rank-two source-basis shear classes on pinned PR3042 words, priced at the unchanged source-reported PR3054/3051 diagnostic endpoint. A favorable result is a census target, not a kappa or formal-pattern claim.',
        changed_premise='CONT12 R2 required equal frames for both residual-target reads in carrier-first order. Release that equality and add the explicitly reversed order proved by inversion and orthogonal complementation. Both classes and all80 labels are fixed before execution. This is not a census of incomparable frames or arbitrary gate orders.',
        seeds=[74017, 148027], shards_per_provider=192, initial_implementation_pins=ref(pin_path),
        science_launch_cutoff_utc='2026-10-17T00:48:00+00:00',
        round_checkpoint_utc='2026-10-17T01:03:04+00:00')
    protocol['comparison']['complex_endpoint'] = str(Fraction('0.001729737950064278551242'))
    domain = protocol['domain']
    domain.update(
        factor='For rows(a,b),(c,d), choose either carrier and anchor, dyadic q=b/a and nonzero e=d-cq. Forward order: j+=q*k@X,u+=a*j@Y,v+=c*j@P,v+=e*k@Q,j-=q*k@Z with X<=Y<=P<=Q<=Z. Reverse order: j+=q*k@Zprime-perp,v+=e*k@Qprime-perp,v+=c*j@Pprime-perp,u+=a*j@Yprime-perp,j-=q*k@Xprime-perp, obtained from the inverse coefficients and complementary reversed boundaries.',
        corners='80 labeled corners:40 per order. Five middle vertices (A1,A2),(K,A2),(U1,J),(U1,U2),(A1,U2); X in{L,Y}, Q in{P,U2}, Z in{Q,D}. Preserve duplicate labels. Reverse frames use exact F2 orthogonal complements in ambient dimension9. Original exit equalities are lower-face restrictions after reversing and are checked on original complete chains.',
        invoice='Complete14-term block tariff plus fixed context contacts and first outside successors. Charge k at X,Q,Z and v at P,Q even when distinct. Check actual subspaces, complete changed-window forward and dual maps, and canonical full word/cleanup parity for retained candidates.',
        labels_per_carrier_anchor=80, maximum_labels_per_provider=8000000,
        inherited_control_labels='Forward0..19 are the old matched-frame subclass. Reverse40..59 have a new execution order and are not inherited negative controls.',
        excluded_domain='Nonconsecutive target-contact pairs, more than four selected original gates, arbitrary resynthesis, incomparable middle frames, other middle gate orders, changed widths, helpers, buffers, exterior or fresh native/outer admission.')
    inputs = protocol['inputs']
    for key in ('source_checkpoint', 'source_checkpoint_review', 'scalar_and_frame_proof', 'static_review'):
        inputs.pop(key, None)
    inputs.update({key: ref(PKG / path) for key, path in dict(
        source_checkpoint='data/continuation-14/checkpoint/RECEIPT.json',
        source_checkpoint_review='data/continuation-14/checkpoint/REVIEW.json',
        scalar_and_frame_proof='results/CONTINUATION-14/planning/SPLIT-RESIDUAL-PROOF.md',
        static_review='results/CONTINUATION-14/planning/SPLIT-REVIEW.json',
        task='results/CONTINUATION-14/TASK.json',
        inherited_rank2_registration='results/CONTINUATION-12/R2/PREREGISTRATION.json',
        resource_policy='results/RESOURCE-SCALING-13/RESULTS.md').items()})
    protocol['controls'] = [
        'Inherited signed dyadic identities for both carriers and anchors; nondyadic quotient, zero determinant, wrong residual, omitted undo and hidden context controls must reject.',
        'Forward strict-concavity fixture dimensions0<2<4<5, rows(1,1),(1,-1): old3H2+2H3 versus new2H2+H3+H4+H1. Check both anchors and carriers; all inherited forward matched labels fail to improve. Strict gain need not hold for both anchors on this fixed-role fixture.',
        'Reverse strict fixture dimensions0<1<2: old5H1 versus new3H1+H2; reverse matched labels are allowed to improve because their execution order is new.',
        'Independent tiny GF2 exhaustive ordered-chain oracle versus all40 corners for each class, nonnested geometry and exact exit equalities, complement billing, inverse scalar signs and literal reverse middle order.',
        'Missing surviving-k contact, successor, unequal subspaces at equal rank, noncommuting crossing, warp/prelude and stale gate/preimage negatives.',
        'Both pinned providers pass unchanged canonical profiles and all632 independent-input forward/dual columns on both seeds.',
        'Retained candidates pass exact window identity, direct versus optimized invoice, canonical full-profile/cleanup parity, all632 columns, and wrong-scalar/omitted-paid-child/omitted-cleanup rejection. Fresh native and outer admission remain required.']
    protocol['phases'].update(prices='768 queued tasks:192 canonical plan-ordinal shards per provider and seed. Each label occurs once per seed. Repeated seeds check execution, not independent statistical samples.')
    protocol.update(
        null_bar='Complete nonempty registered80-label union, every sign resolved or exact infeasibility recorded, no favorable row on either provider, all controls and baselines pass, and both seed decisions agree. NULL closes only the pinned consecutive-contact, stable-gather, two ordered-chain classes.',
        stop_rules='Stop at the completed paired outcome. No outcome-driven extension of the frozen family. PLAN6 pattern criteria and prior lane stops remain binding. Two consecutive scoped scientific NULLs stop a lane; at most one separately justified changed-premise pivot in this round. Controls, caps or budget failures stop dependent work and preserve evidence.',
        overlap=dict(active_claim='Discussion2612comment18983666 covers broad multi-consumer covector/re-timing work; the00:05 body also closes author-local restore-only searches. S3 is a complementary bounded cost/feasibility audit and does not assert nonoverlap or novelty.', prior_art='Standard source-basis shear, PR3044 shared restore covectors, earlier read merge/split searches and fixed-scalar/frame optima remain attributed. The changed scalar order/production is explicit.'),
        resources=dict(cpu_budget_seconds_family=24000, round_cpu_budget_seconds=48000,
            expected_workers=120, workers='Measured policy: min(120, available allocated cores minus8, memory capacity after16GiB reserve using1.20*max(parent RSS,1.5GiB worker estimate), task count). All workers run through immutable pipeline/pool.py via the hash-bound measured adapter.',
            allocated_cores=128, reserved_cores=8, timeout_seconds=300, rss_gib=4,
            estimated_worker_rss_gib=1.5, parent_load_once=True, one_pool_at_a_time=True, solver_calls=0,
            result_bytes_cap=200000000, new_result_bytes_cap=220000, new_data_bytes_cap=1073741824,
            resource_accounting='Project memory before preparation and each launch; measure worker RSS and live memory every0.5s, terminate on reserve/cap violation, save CPU/wall after join. No instantaneous-utilization claim from skewed samples.'),
        pattern_claim=False, kappa_claim=False)
    preg = ROUND / 'S3/PREREGISTRATION.json'
    save(preg, protocol)
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    assert registry['no_active_experiments'] and not registry['experiments']
    registry['experiments'].append(dict(id=protocol['experiment'], status='planned', execution='REGISTERED',
        preregistration=str(preg.relative_to(PKG)), preregistration_sha256=sha(preg), implementation_pins=ref(pin_path)))
    registry['status'] = 'REGISTERED_READY'
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_SCIENCE', preregistration_sha256=sha(preg),
        implementation_pins_sha256=sha(pin_path), source_files=len(pins), registered_utc=recorded)))


if __name__ == '__main__':
    main()
