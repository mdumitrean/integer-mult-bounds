"""Candidate PLAN/SPEC delta for a narrowed-inventory owner map (no native words yet: program/artifact hashes pending).
usage: plan_candidate.py OWNERDIR [REG=478]"""
import collections, copy, hashlib, json, sys
from pathlib import Path
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import ctx as X
O = Path(sys.argv[1]); REG = int(sys.argv[2]) if len(sys.argv) > 2 else 478; HS = REG - 224
plan = X.rd(X.PLAN72); chk = json.load(open(O / 'CHECK.json')); spec = X.rd(X.PLAN72.parent / 'SPEC.json')
new = copy.deepcopy(plan); widths = json.load(open(O / 'PROVIDER-WIDTHS.json'))
for p in ('gauge44', 'extra'):
    reg = new['provider_registry'][p]; assert reg['widths'][HS] == 9 and widths[p][HS] == 8
    reg['widths'] = widths[p]; reg['actual_paid_profile'] = {str(k): v for k, v in chk['assumed_paid'][p].items()}
for row in new['per_call_widths']:
    prov = next(c['provider'] for c in plan['provider_calls'] if (c['stage'], c['replica']) == (row['stage'], row['replica']))
    row['widths'] = widths[prov]
new['profile'] = {str(k): v for k, v in chk['profile'].items()}
fsha = hashlib.sha256((O / 'OWNERS.json.gz').read_bytes()).hexdigest()
new['assignment_sha256'] = fsha; new['assignment_content_sha256'] = chk['owners_content_sha256']; new['replica_lift']['owners_file_sha256'] = fsha
new['source_owners_sha256'] = plan['assignment_content_sha256']; new['status'] = f'CANDIDATE_NARROWED_HELPER_{REG}_WITHIN_CALL_RELABEL'
new['solver_status'] = 'greedy concentration of narrowed slots; no role leaves its bin (within-call helper-id swaps only)'
new['pending_from_new_native_words'] = ['provider_registry.*.actual_paid_profile (assumed H1 -1 per call)', 'provider_registry.*.artifact_sha256',
    'provider_registry.*.artifact_semantic_sha256', 'provider_registry.*.orientation_program_sha256', 'provider_calls[*].local_program_sha256']
X.dump(O / 'PLAN-CANDIDATE.json', new)
idle = {str(k): v for k, v in chk['idle'].items()}
delta = dict(expected=dict(idle_remainder_profile=idle, idle_remainders=sum(idle.values()), global_profile={str(k): v for k, v in chk['profile'].items()},
                           actual_73column_sigmas=chk['charts'], hosted_residuals=chk['roles'], cross_replica_helper_roles=296300,
                           rank_mass=chk['rank_mass'], provider_counts=chk['dispatch'], assembly_controls_rejected=114, mutations_rejected=15,
                           complex_lower='recompute (assembly)', conservative_complex_lower='recompute', kappa='recompute'),
             unchanged_from=dict(actual_73column_sigmas=spec['expected']['actual_73column_sigmas'], idle_remainder_profile=spec['expected']['idle_remainder_profile'],
                                 global_profile=spec['expected']['global_profile']),
             providers={p: dict(inventory=chk['inventories'][p], expected_profile={str(k): v for k, v in chk['assumed_paid'][p].items()},
                                entering=spec['providers'][p]['entering'] + 1, entrance=spec['providers'][p]['entrance'] + 1,
                                note='entering/entrance assume the narrowed helper enters with a rank-1 start frame; width_digest, program_hashes, artifacts, complete_contract, wrappers, native_negative_controls, phase_edges, semantic_phase_sha256, expected_local come from the new native admission (discover + freeze_spec.py)')
                        for p in ('gauge44', 'extra')})
json.dump(delta, open(O / 'SPEC-DELTA.json', 'w'), indent=1); print('wrote PLAN-CANDIDATE.json and SPEC-DELTA.json', fsha[:12])
