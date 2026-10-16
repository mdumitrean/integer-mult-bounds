"""Close the retrospective round from saved receipts; no scientific execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

PKG = Path(__file__).resolve().parents[2]
ROUND = PKG / 'results/CONTINUATION-07'


def read(path):
    return json.loads(path.read_bytes())


def ref(path):
    return {'path': str(path.relative_to(PKG)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def immutable_json(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError('Refusing to replace final document: ' + str(path))
    else:
        with path.open('xb') as stream:
            stream.write(raw)


def main():
    registry_path = ROUND / 'EXPERIMENTS.json'
    registry = read(registry_path)
    for row in registry['experiments']:
        if row['execution'] != 'COMPLETED' or row['status'] != 'EXPLORATORY':
            raise ValueError('Unfinished or unexpectedly promoted family')
    runs = {}
    for family, version in [('ML1-HISTORICAL-CONTROLS', 'v1'),
                            ('ML2-RELEASE-COMPARISON', 'v1'),
                            ('ML2-RELEASE-COMPARISON', 'v2'),
                            ('ML3-OUT-OF-COHORT', 'v1')]:
        path = ROUND / family / version / 'RUN.json'
        runs[(family, version)] = (path, read(path))
    first = runs[('ML1-HISTORICAL-CONTROLS', 'v1')][1]
    second = runs[('ML2-RELEASE-COMPARISON', 'v2')][1]
    third = runs[('ML3-OUT-OF-COHORT', 'v1')][1]
    third_result = read(ROUND / 'ML3-OUT-OF-COHORT/v1/seed-37003/RESULT.json')
    seeds = [37003, 74017]
    predictions = {
        'schema_version': 1,
        'round': 'CONTINUATION-07',
        'status': 'NO_PROMOTED_PATTERN_NO_PROSPECTIVE_PREDICTIONS',
        'formal_pattern_claims': [],
        'prospective_predictions': [],
        'new_kappa_improvement': False,
        'scope': ('Retrospective selected-success comparison; separate PR3015 outcome was '
                  'known before registration. No causal or independent-admission claim.'),
        'plan_section_6': {
            'all_five_pattern_criteria_satisfied': False,
            'two_seed_scoped_decisions_agree': True,
            'descriptive_shuffles_per_seed': 199,
            'q_values_assigned': False,
            'existing_lane_stop_rules_remain_in_force': True,
            'insufficient_data_is_not_scientific_null': True,
        },
        'diagnostic_outcomes': [
            {'experiment': 'ML1-HISTORICAL-CONTROLS', 'attempt': 'v1',
             'outcome': 'REGISTERED_FRAME_FEASIBILITY_BAR_NOT_MET',
             'gain_classifier_identifiable': False,
             'positive_kappa_training_examples': 0,
             'by_seed': {str(seed): {
                 'diagnostic_bar_met': first['statistics'][str(seed)]['diagnostic_bar_met'],
                 'null_summary': first['statistics'][str(seed)]['null_summary'],
             } for seed in seeds},
             'limitation': 'Exact-stratum whole-pair permutation null is degenerate; no general null claim.'},
            {'experiment': 'ML2-RELEASE-COMPARISON', 'attempt': 'v2',
             'outcome': 'WORSE_THAN_BASELINE_WITH_UNIDENTIFIABLE_MECHANISM_HOLDOUT',
             'regression_release_ids': [2948, 2957, 2966],
             'distinct_immediate_sources': 2,
             'distinct_declared_mechanisms': 1,
             'source_group_baseline_log10_mse': 0.009740217144594584,
             'source_group_ridge_log10_mse': 0.10538226875923525,
             'source_group_baseline_minus_ridge_mse': -0.09564205161464066,
             'mechanism_group_status': 'UNIDENTIFIABLE_GROUPING',
             'by_seed_null_summary': {str(seed): second['statistics'][str(seed)]['null_summary'] for seed in seeds},
             'correction': ref(ROUND / 'ML2/COVERAGE-CORRECTION-v2.json'),
             'v1_preserved': True,
             'limitation': 'Three selected related successes after conservative unchanged-allocation gate; no success classifier.'},
            {'experiment': 'ML3-OUT-OF-COHORT', 'attempt': 'v1',
             'release_id': 3015, 'matched_parent_pr': 2979,
             'outcome': 'UNBLINDED_FACTOR_TWO_DIAGNOSTIC_FAILED',
             'training_release_ids': [2948, 2957, 2966],
             'outcome_known_before_registration': True,
             'blinded_prospective_validation': False,
             'model_updated_with_heldout': False,
             'source_reported_gain_only': True,
             'fresh_native_outer_admission': False,
             'by_seed': {str(seed): third['statistics'][str(seed)]['prediction']['comparison'] for seed in seeds},
             'preregistration': ref(ROUND / 'ML3/PREREGISTRATION.json'),
             'cohort': ref(ROUND / 'planning/HOLDOUT-3015-COHORT-v2.json')},
        ],
        'runs': [ref(path) for path, run in runs.values()],
        'source_attribution': third_result['source_attribution'],
        'release_source_attribution': ref(ROUND / 'planning/RELEASE-COHORT.json'),
        'additional_release_source_attribution': ref(ROUND / 'planning/HOLDOUT-3015-COHORT-v2.json'),
        'ai_assistance': 'Substantial OpenAI Codex assistance in implementation and analysis.',
    }
    immutable_json(ROUND / 'PREDICTIONS.json', predictions)
    closed = 'COMPLETE_RETROSPECTIVE_ANALYSIS_NO_PROMOTED_PATTERN'
    if registry['status'] != closed:
        registry['status'] = closed
        registry['closed_utc'] = datetime.now(timezone.utc).isoformat()
        registry['goal_status'] = 'ACTIVE_NOT_ACHIEVED'
        registry['no_active_experiments'] = True
        registry['new_kappa_improvement'] = False
        registry['formal_pattern_claims'] = 0
        registry['compute'] = {
            'cpu_seconds': sum(run['total_cpu_seconds'] for path, run in runs.values()),
            'summed_scientific_wall_seconds': sum(run['total_wall_seconds'] for path, run in runs.values()),
            'pool_tasks': sum(sum(run['completed_by_phase'].values()) for path, run in runs.values()),
            'permutation_tasks': sum(run['completed_by_phase'].get('permutations', 0) for path, run in runs.values()),
            'configured_workers': 61,
            'source_acquisition_and_administrative_audit_separate': True,
        }
        for row in registry['experiments']:
            if row['id'] == 'ML2-RELEASE-COMPARISON':
                row['scope'] = ('Twelve completed parent-matched source releases; paired descriptive '
                                'analysis, with conservative v2 unchanged-allocation regression coverage.')
        registry['deliverables'] = {name: ref(ROUND / name)
                                    for name in ['RESULTS.md', 'HANDBACK.md', 'PREDICTIONS.json']}
        registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + '\n')
    else:
        for name, expected in registry['deliverables'].items():
            if ref(ROUND / name) != expected:
                raise ValueError('Final document changed after closure: ' + name)
    print(json.dumps({'status': closed, 'compute': registry['compute']}))


if __name__ == '__main__':
    main()
