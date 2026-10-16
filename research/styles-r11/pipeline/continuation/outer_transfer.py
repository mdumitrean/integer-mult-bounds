"""Independent rational evaluation of the retained modern outer composition.

This file implements mathematical equations read as inert source data from
PR2853's outer/check_ledger.py, SHA256
9e12909c73d3b3a31a45d801ae76c034510d6306400412e474df79bc4f1dc67e.
No fetched Python is imported, copied as executable code, or executed.
Attribution: retained PR1673 composition, PR1786 fine padding, and the
PR2161/2180 fixed-grid derivation by dataisfire, with the full PINS lineage.

This arithmetic is a conditional transfer, not an all-size theorem proof.
The coordinator must register V1 and launch it through pipeline/pool.py.
"""
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from fractions import Fraction as Q
import hashlib
import json
import random


def require(value, reason):
    if not value:
        raise ValueError(reason)


def decimal(value, digits=90):
    value = Q(value)
    with localcontext() as ctx:
        ctx.prec = digits
        return str(Decimal(value.numerator) / Decimal(value.denominator))


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(v) for v in value]
    return value


@dataclass(frozen=True)
class Point:
    C: Q
    r: Q = Q(1, 10**104)
    bit: Q = Q('0.001733427039589844234749')
    backoff: Q = Q(1, 10**46)
    grid: int = 10**70
    theta: Q = Q(2)
    halo: int = 48
    core: int = 128
    matrix: Q = Q(45, 16)

    @property
    def delta(self):
        return Q(1025, 1024) * self.r


def evaluate(point, mutation=None):
    """All functional inequalities, evaluated from exact rational parameters.

    Historical improvement comparisons are handled separately by transitivity
    against the pinned predecessor release. They are not silently rerun here.
    """
    C, r = point.C, point.r
    d = point.delta
    epsilon, beta = 1-d, 1-3*d
    b, q, a = C-r, C-2*r, C-Q(3, 2)*r
    layout = r
    matrix, halo, core = point.matrix, point.halo, point.core
    if mutation == 'endpoint_equality':
        q = b
    elif mutation == 'zero_layout_slack':
        layout = Q(0)
    elif mutation == 'matrix_below_strassen':
        matrix = Q(14, 5)
    elif mutation == 'halo_too_short':
        halo = 40
    elif mutation == 'core_too_small':
        core = 48
    elif mutation == 'group_equals_dimension':
        beta = epsilon
    elif mutation == 'epsilon_equals_one':
        epsilon = Q(1)
    elif mutation == 'epsilon_not_above_r0_slack':
        epsilon = 1-r
    elif mutation == 'beta_below_gaussian_window':
        beta = 1-700*d
    elif mutation == 'beta_above_membership_window':
        beta = 1-2*d

    stop = r / 10**6
    c = (3-matrix)/2
    saving = epsilon*q
    xi = epsilon*(1+q)-c+layout
    K = Q((saving*point.grid).__floor__(), point.grid)-point.backoff
    tau, sigma = 1-a, 1-b
    internal = tau+(1-stop)*max(sigma-tau, Q(0))
    leaf = sigma+stop*(1-sigma)
    lam = 1-(q+a)/2
    key = beta+1-epsilon

    savings = dict(main_transform=saving,
        global_coordinate_router=a,
        fused_gaussian=1-epsilon+q*beta,
        group_bit_router=1-epsilon+a*beta,
        group_scans=1-epsilon+beta,
        boundary_algebraic_matrix=c+xi-epsilon,
        sparse_union_movement=xi+Q(1, 2)-epsilon,
        polynomial_products=epsilon,
        microbox_face_corrections=1-epsilon-beta-halo+core-2)
    checks = dict(
        actual_bit_above_effective=point.bit-a,
        complex_above_effective=b-a,
        q_positive=q,
        complex_endpoint=b-q,
        q_below_effective=a-q,
        stop_positive=stop,
        stop_below_one=1-stop,
        leaf_saving_above_effective=(1-stop)*b-a,
        q_below_internal=1-internal-q,
        q_below_leaf=1-leaf-q,
        lambda_above_tau=lam-tau,
        lambda_above_sigma=lam-sigma,
        lambda_above_internal=lam-internal,
        lambda_prime_above_lambda=1-q-lam,
        lambda_prime_above_leaf=1-q-leaf,
        epsilon_positive=epsilon,
        epsilon_below_one=1-epsilon,
        cap_above_band=xi-Q(1, 2),
        cap_below_cell=epsilon-xi,
        group_positive=beta,
        group_below_dimension=epsilon-beta,
        support_router_span=1-beta,
        group_gauge_power_slack=1-2*xi+point.theta-r-beta,
        actual_logarithmic_group_guard=1-2*xi+point.theta-beta,
        global_gamma_power_slack=1-epsilon-r,
        actual_logarithmic_gamma_guard=1-epsilon,
        alpha_logarithm_absorption=r,
        group_key_fits_record=1-key,
        membership_arithmetic_fits_record=1-beta-2*(1-epsilon),
        microbox_halo_volume=core-halo-beta,
        positive_layout_slack=layout,
        short_record_fallback=epsilon-a,
        complex_below_one_over_32=Q(1, 32)-b,
        strassen_integer_power_gap=Q(2**matrix.numerator-7**matrix.denominator),
        theta_positive_polynomial_power=point.theta,
        cap_below_phase_cell_power=point.theta-xi,
        halo_covers_generic_inverse_radius=Q(halo-43),
        union_tag_work_per_visit_fits_record=1-beta,
        union_header_fits_record=1-beta,
        source_axis_superpolynomial=1-epsilon,
        gaussian_above_main=savings['fused_gaussian']-saving)
    old_savings = dict(old_per_axis_scan=1-epsilon,
        full_key_sort=savings['sparse_union_movement']-key,
        old_g_factor_union_row=1-epsilon-beta-Q(1, 2)+xi)
    old_guards = dict(full_cell_gauge=1-point.theta-r-beta,
        old_theta_chirp_guard=1-2*xi+epsilon-r-beta,
        old_linear_guard=1-xi-r-beta,
        old_union_tag_2beta=1-2*beta)
    if mutation in old_savings:
        savings[mutation] = old_savings[mutation]
    if mutation in old_guards:
        checks[mutation] = old_guards[mutation]
    checks.update({name+'_above_kappa': val-K for name, val in savings.items()})
    require(savings['boundary_algebraic_matrix'] == saving+layout,
            'boundary/main balance identity')
    require(savings['sparse_union_movement'] == saving+layout+(matrix-2)/2,
            'union/main balance identity')
    return dict(kappa=K, parameters=dict(C=C, r=r, delta=d, epsilon=epsilon, beta=beta,
                b=b, q=q, a=a, stop=stop, xi=xi, theta=point.theta,
                halo=halo, core=core, matrix=matrix), savings=savings, strict_checks=checks)


CONTROLS = ('endpoint_equality', 'zero_layout_slack', 'old_per_axis_scan',
    'full_cell_gauge', 'full_key_sort', 'old_g_factor_union_row',
    'old_theta_chirp_guard', 'old_linear_guard', 'old_union_tag_2beta',
    'matrix_below_strassen', 'halo_too_short', 'core_too_small',
    'group_equals_dimension', 'epsilon_equals_one', 'epsilon_not_above_r0_slack',
    'beta_below_gaussian_window', 'beta_above_membership_window')

HISTORICAL_COMPARISONS = ('online_final', 'previous_local_final', 'pr1786',
    'pr1828', 'pr1839', 'pr1875', 'pr1876', 'pr1897', 'pr1758', 'pr1699',
    'pr1712', 'previous_package', 'pkg_k2')


def certify(endpoint, source_claim, release_receipt, seed):
    """Check the complete functional ledger and source-bound monotone reuse."""
    C = Q(endpoint)
    require((C*10**24).denominator == 1 and 0 < C < Q(1, 500),
            'registered positive 24-place grid endpoint')
    point = Point(C)
    row = evaluate(point)
    checks = row['strict_checks']
    require(len(checks) == 50 and all(v > 0 for v in checks.values()),
            'all fifty functional outer inequalities must be strict')
    K, saving = row['kappa'], row['savings']['main_transform']
    require(min(row['savings'].values()) == saving, 'main transform binds')
    require((C*point.grid).denominator == 1 and 0 < C-saving < Q(1, point.grid),
            'strict sub-grid saving loss')
    require(K == C-Q(1, point.grid)-point.backoff, 'exact fixed-grid headline')
    require(row['strict_checks']['gaussian_above_main'] == point.delta*(1-2*row['parameters']['q']),
            'independent Gaussian excess identity')
    old = Q(source_claim['kappa'])
    oldC = Q(source_claim['complex_lower'])
    require(old == oldC-Q(1, 10**70)-Q(1, 10**46) and K > old,
            'strict headline improvement over pinned latest source')
    require(release_receipt['status'] == 'PASS_RELEASE'
            and release_receipt['kappa_decimal'] == source_claim['kappa_decimal'],
            'source release numerical binding')
    require('63 strict inequalities' in release_receipt['proof'],
            'source evidence explicitly covers all retained comparisons')

    order = list(CONTROLS)
    random.Random(seed).shuffle(order)
    rejected = {}
    for name in order:
        mutant = evaluate(point, name)
        failures = {k: v for k, v in mutant['strict_checks'].items() if v <= 0}
        require(failures, 'non-rejecting arithmetic control: '+name)
        rejected[name] = failures
    umbrella = Q(10)-(2*point.theta+2+Q(1, 2))
    bad_umbrella = Q(10)-(2*Q(15, 4)+2+Q(1, 2))
    require(umbrella > 0 and bad_umbrella <= 0, 'fine-padding umbrella control')
    require(C < point.bit, 'complex endpoint stays below retained bit supplier')
    return encode(dict(status='PASS_CONDITIONAL_OUTER_ARITHMETIC', seed=seed,
        ledger=row, kappa_decimal=decimal(K), improvement=K-old,
        improvement_decimal=decimal(K-old), predecessor_kappa=old,
        functional_check_count=50,
        historical_comparison_transfer=dict(count=13, names=HISTORICAL_COMPARISONS,
            rule='K_new > K_source; every K_source - old_constant > 0 in the pinned PASS_RELEASE. Hence each new historical margin is strictly positive.',
            receipt_reused=True, prior_constants_recomputed=False),
        rejecting_controls=rejected, umbrella=dict(margin=umbrella, control_margin=bad_umbrella),
        fixed_grid_identity='K=C-10^-70-10^-46',
        native_moment_at_b='Separate exact upper moment at C plus strict monotonicity implies moment(b)<1 for b=C-10^-104.',
        inherited_obligations=['Retained bit H1-H5 admission', 'Retained exact union schedule and gauge-free identity/theorem',
            'Fine source-prime padding and all-size machine/compiler interfaces',
            'Source-bound native physical supplier and fresh changed owner checks'],
        scope='Fresh exact functional arithmetic and rejecting controls. Thirteen historical comparisons and unchanged outer mechanisms reuse source-bound prior evidence. This is not a fresh replay of that evidence.'))
