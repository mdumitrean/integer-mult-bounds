"""Administrative rank-two preregistration/source freeze; no scientific imports."""
from datetime import datetime, timezone
from fractions import Fraction
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
    with path.open('x') as stream:
        stream.write(json.dumps(value, sort_keys=True, indent=2) + '\n')


def main():
    recorded = datetime.now(timezone.utc).isoformat()
    review = json.loads((ROUND / 'planning/RANK2-REVIEW.json').read_text())
    assert review['status'] == 'PASS_STATIC', 'independent implementation review must pass before freeze'
    previous = json.loads((ROUND / 'ML4/IMPLEMENTATION-PINS-v1.json').read_text())
    paths = {ROOT / name for name in previous['sha256']}
    paths.update((PKG / 'pipeline/continuation12').glob('*.py'))
    archives = dict(previous['archives'])
    pins = {}
    for path in sorted(paths):
        raw = path.read_bytes()
        ast.parse(raw, filename=str(path))
        digest = hashlib.sha256(raw).hexdigest()
        relative = str(path.relative_to(ROOT))
        if relative in previous['sha256']:
            assert digest == previous['sha256'][relative], 'frozen ML4 source changed'
        pins[relative] = digest
        if digest not in archives:
            target = PKG / 'data/continuation-12/source-archives' / (digest + '.py.gz')
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('xb') as stream:
                    stream.write(gzip.compress(raw, mtime=0))
            archives[digest] = ref(target)
        assert gzip.decompress((PKG / archives[digest]['path']).read_bytes()) == raw
    manifest = dict(schema_version=1, frozen_utc=recorded, sha256=pins, archives=archives,
                    imports_before_freeze=False, scientific_preparation_before_freeze=False,
                    archive_policy='All scientific sources and trusted inherited dependencies authenticated before import; no fetched code execution.')
    pin_path = ROUND / 'R2/IMPLEMENTATION-PINS-v1.json'
    save(pin_path, manifest)
    input_paths = dict(
        original_pins='data/words/PINS.json',
        latest_words='data/continuation-11/latest-sources/ACQUISITION.json',
        latest_word_comparison='data/continuation-11/latest-sources/WORD-COMPARISON.json',
        current_comparison_acquisition='data/continuation-12/allocation-source/ACQUISITION.json',
        current_comparison_bindings='data/continuation-12/allocation-source/BINDINGS.json',
        source_checkpoint='data/continuation-12/pivot-checkpoint/RECEIPT.json',
        source_checkpoint_review='data/continuation-12/pivot-checkpoint/REVIEW.json',
        adapter_static_review='data/continuation-12/ADAPTER-STATIC-REVIEW.json',
        scalar_and_frame_proof='results/CONTINUATION-12/planning/RANK-TWO-CARRIER-PROPOSAL.md',
        static_review='results/CONTINUATION-12/planning/RANK2-REVIEW.json',
        inherited_frame_proof='results/CONTINUATION-09/planning/JOINT-CARRIER-PROOF.md',
        independent_window_proof='results/CONTINUATION-10/planning/GATHERED-WINDOW-PROOF.md',
        plan='PLAN.md')
    protocol = dict(
        schema_version=1, state='FROZEN', experiment='R2-MATCHED-FRAME-CARRIER',
        milestone='CONTINUATION-12/R2', registered_utc=recorded,
        scope='Complementary finite audit of a rank-two source-basis shear with a charged residual read on the PR3042 base/extra words. This is the one changed-premise pivot allowed this round. No novelty, formal pattern, or kappa claim.',
        changed_premise='Earlier J1/J2 packets required proportional coefficient rows. Here determinant is nonzero and the surviving residual source read is charged. The positive fixture also expands F1 disjoint-intervener exposure. When both source exits admit ordinary climbs, moving undo toY2 and retiming both original second-row reads toY2 weakly dominates this matched-frame factor by merging final source climbs. That alternative is broader than the frozen F1 exposure/context domain; exact equality exits can forbid it. No irreducible shared-restoration advantage is assumed.',
        seeds=[63029, 126037], n_permutations=0, shards_per_provider=64,
        source_words=dict(pr=3042, providers=['base', 'extra'],
            binding='Exact inert word files, acquisition, original and inherited PINS verified by latest3042_adapter; source attribution retained in each RESULT.',
            fresh_native_admission=False),
        comparison=dict(pr=3054, also_pr=3051, source_reported_only=True,
            complex_endpoint=str(Fraction('0.001729737950064278551242')),
            derivation='Source-reported outer endpoint plus inherited 10^-46 and 10^-70 slacks; diagnostic child tariff only, not fresh admission.'),
        domain=dict(
            source_domain='A after prelude and B split at every warp. Form consecutive target-contact pairs with two distinct source registers, group by the same unordered source pair, and combine distinct targets without common-ratio grouping. Four distinct non-C registers, exactly one nonzero dyadic edge for each target/source pair, and nonzero determinant. Complete within this explicitly consecutive-contact domain only.',
            factor='For rows(a,b),(c,d), choose either source carrier and either cancelled row. q=b/a must be dyadic; e=d-q*c is nonzero. Execute j+=q*k; u+=a*j; v+=c*j; v+=e*k; j-=q*k. The two v reads have exactly the same subspace Y2.',
            placements='Stable gather-left and gather-right inside the original four-edge window. Certify every selected/unselected adjacent scalar commutation. Preserve all unselected order and frames and every barrier. Intermediate gathered frame feasibility is not assumed; final whole-window feasibility is mandatory.',
            corners='X subset Y1 subset Y2 subset Z. Twenty labels from the five realized middle vertices (A1,A2),(K,A2),(U1,J),(U1,U2),(A1,U2), and X in {L,Y1}, Z in {Y2,D}. Exact proof is only for this matched-Y2 subclass, not five independent gate frames. Retain duplicate labels.',
            invoice='Complete fourteen-term block tariff plus all fixed context contacts and first outside successors. Include surviving k contact and both v reads. Exact exit equalities are checked as subspaces. Recompute full changed-window forward and dual matrices and canonical complete word/cleanup deltas for retained candidates.',
            length_change='Four gates become five; shift every later B warp position by exactly one. Helper endpoints, widths, order, stock, and all other sections stay fixed. Additional finite scalar work still requires fresh native admission.',
            address='[section,p0,p1,p2,p3,in,placement,carrier,anchor,corner]',
            maximum_labels_per_provider=2000000,
            maximum_structural_packets_per_provider=12500,
            cap_disposition='Domain or storage cap means incomplete, never NULL. Bound before materializing the excessive candidate collection; no outcome-driven truncation.'),
        inputs={key: ref(PKG / path) for key, path in input_paths.items()},
        initial_implementation_pins=ref(pin_path),
        controls=[
            'Exact signed dyadic rank-two identities for both carriers and anchors, with nondyadic quotient, zero determinant, wrong residual and omitted undo negatives.',
            'Interleaved synthetic positive: old4H1 versus new2H1+H2, equal mass4, all sources dirty and restored.',
            'Independent tiny subspace oracle enumerates the matched-Y2 class only; compare20corner minimum, including nonnested meet/join geometry and equality exits.',
            'Missing surviving-k contact, missing successor, unequal subspaces at same rank, noncommuting crossing, hidden warp/prelude, stale literal gate/preimage controls.',
            'Both unchanged latest3042 providers pass canonical profile and all632 independent-input forward/dual columns.',
            'Every retained candidate passes exact whole-window identity, direct invoice versus optimized invoice, canonical full-profile/cleanup delta parity, and independent632-column admission; wrong scalar, omitted paid child and omitted cleanup must reject.'
        ],
        phases=dict(controls=2, baseline=4, census=4,
            prices='256 queued tasks:64 canonical plan-ordinal shards per provider and seed. Every label appears exactly once per execution seed; two executions are not independent samples.',
            retention='First at most8 common favorable provider-independent addresses in canonical numeric order, both providers and seeds; preserve unretained favorable cases explicitly.'),
        retained_pair_limit=8,
        statistic='Outward exact rational enclosure of full-window moment delta for H(r)=(r/73)^(1-b), H(0)=0 at the pinned endpoint. Strictly negative upper bound is favorable; an interval spanning zero is unresolved.',
        null_model='No stochastic null; exact finite-domain guarded census. PLAN section6 formal-pattern criteria are not claimed.',
        pass_bar='At least one common provider-independent address has a strictly negative full-window moment and retained full-word/632-column controls pass for both providers and both seeds. PASS identifies a census target only.',
        null_bar='Complete nonempty label domain; every sign resolved or exact infeasibility recorded; no favorable row on either provider; all controls/baselines pass; both seed decisions agree. Only this fixed source/domain/exposure/matched-frame family is closed.',
        other_dispositions='Empty domain, unresolved sign, or unpaired favorable cases are EXPLORATORY. Error/control/binding failure isERROR; task/budget cutoff isTIMEOUT. Incomplete census is never NULL.',
        overlap=dict(active_claim='Discussion2612comment18983666 broadly includes multi-consumer covector reuse with residual direct reads. Rank two does not prove nonoverlap. This is a complementary matched-frame finite audit and missing cost/feasibility lemma, not a distinct-method claim.',
            prior_art='Standard source-basis shear, PR3044 shared restore covectors, earlier read merge/split searches, and fixed-scalar/frame optima retained. Changed scalar production lies outside fixed-scalar optimum assumptions, not outside all existing research.'),
        confirmation='Different traversal seeds must agree on exact census, exclusions, prices, retained words, and verdict. No statistical replication claim.',
        stop_rules='One bounded changed-premise pivot only. Stop at completed paired outcome; no post-result domain expansion. All PLAN6 five pattern criteria and prior lane stops remain binding; two consecutive scoped scientific NULLs stop a lane. Failed controls or caps stop dependent work with preserved evidence.',
        science_launch_cutoff_utc='2026-10-17T00:00:00+00:00',
        round_checkpoint_utc='2026-10-17T00:15:00+00:00',
        resources=dict(cpu_budget_seconds_family=12000, round_cpu_budget_seconds=120000,
            expected_workers=61, workers='min(120,floor(RAM_GiB/4))', allocated_cores=128,
            reserved_cores=8, timeout_seconds=300, rss_gib=4, working_set_gib=1.25,
            parent_load_once=True, one_pool_at_a_time=True, solver_calls=0,
            result_bytes_cap=200000000, new_result_bytes_cap=1000000,
            new_data_bytes_cap=1073741824,
            resource_accounting='Memory projection before preparation and each launch. Task worker-lifetime RSS and phase CPU/wall after joining the pool; no timing-skewed instantaneous utilization claim.'),
        recording='Immutable source snapshots before scientific imports/preparation; per-task data receipts and per-seed RESULTs with original PINS and current attribution. Every failure preserved. Registry transitions recorded.',
        pattern_claim=False, kappa_claim=False,
        ai_assistance='Substantial OpenAI Codex assistance in implementation, mathematical checks and analysis.')
    preg = ROUND / 'R2/PREREGISTRATION.json'
    save(preg, protocol)
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = json.loads(registry_path.read_text())
    assert registry['no_active_experiments']
    assert not any(row['id'] == protocol['experiment'] for row in registry['experiments'])
    registry['experiments'].append(dict(id=protocol['experiment'], status='planned', execution='REGISTERED',
        preregistration=str(preg.relative_to(PKG)), preregistration_sha256=sha(preg),
        implementation_pins=ref(pin_path)))
    registry['status'] = 'REGISTERED_PIVOT_READY'
    registry_path.write_text(json.dumps(registry, sort_keys=True, indent=2) + '\n')
    print(json.dumps(dict(status='FROZEN_BEFORE_SCIENCE', preregistration_sha256=sha(preg),
        implementation_pins_sha256=sha(pin_path), source_files=len(pins), registered_utc=recorded)))


if __name__ == '__main__':
    main()
