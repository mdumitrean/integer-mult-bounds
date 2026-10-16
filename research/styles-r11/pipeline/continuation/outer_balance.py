"""Independent closed-form check of the retained modern outer balance.

This module imports no primary outer checker and no fetched source. The
formulas below follow the retained PR1673/PR1786 composition and the exact
PR2161/PR2180 fixed-grid identity (dataisfire). Source evidence and the full
PINS attribution must accompany the coordinator's immutable result.

Only the registered V1 worker may call certify; this module runs nothing on
import, starts no pool and performs no file/network operation.
"""
from fractions import Fraction as Q


def require(condition, why):
    if not condition:
        raise ValueError(why)


def encode(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    return value


def certify(endpoint, source_claim, primary=None):
    """Independent exact identities and all nine saving margins.

    ``primary`` optionally binds the separately evaluated outer_transfer result.
    It is compared only after all closed-form values have been derived here.
    This routine supplements, and does not replace, all fifty functional gates.
    """
    C, r = Q(endpoint), Q(1, 10**104)
    quantum, backoff = Q(1, 10**70), Q(1, 10**46)
    d, bit = Q(1025, 1024) * r, Q('0.001733427039589844234749')
    require((C * 10**24).denominator == 1 and 2*r < C < bit < Q(1, 500),
            'registered complex grid and unchanged bit-supplier upper endpoint')
    q, a, b = C-2*r, C-Q(3, 2)*r, C-r
    epsilon, beta = 1-d, 1-3*d
    stop, theta, halo, core, matrix = r/10**6, Q(2), Q(48), Q(128), Q(45, 16)
    c = Q(3, 32)
    xi = (1-d)*(1+C-2*r)-c+r

    # Grid proof without Decimal or a copied primary floor implementation.
    # C*10^70 is integral and the exact positive loss lies in (0,10^-70).
    # Therefore floor((C-loss)*10^70)=C*10^70-1, uniquely.
    loss = 2*r+d*q
    require(0 < loss < quantum and (C/quantum).denominator == 1, 'strict sub-grid loss')
    K = C-quantum-backoff
    overhead = quantum+backoff
    main = C-loss
    require(main == epsilon*q and K+backoff < main < K+backoff+quantum,
            'unique exact floor-grid interval')

    # These expressions are expanded independently, rather than obtained by
    # subtracting K from a primary savings dictionary.
    gaps = {
        'main_transform': overhead-2*r-d*q,
        'global_coordinate_router': overhead-Q(3, 2)*r,
        'fused_gaussian': overhead-2*r+d*(1-3*q),
        'group_bit_router': overhead-Q(3, 2)*r+d*(1-3*a),
        'group_scans': 1-C+overhead-2*d,
        'boundary_algebraic_matrix': overhead-r-d*q,
        'sparse_union_movement': overhead-r-d*q+Q(13, 32),
        'polynomial_products': 1-C+overhead-d,
        'microbox_face_corrections': 77-C+overhead+4*d,
    }
    require(all(gap > 0 for gap in gaps.values()), 'all nine independent cost gaps are strict')
    excess = {
        'global_coordinate_router': r/2+d*q,
        'fused_gaussian': d*(1-2*q),
        'group_bit_router': r/2+d*(1-3*a+q),
        'group_scans': 1-2*d-C+loss,
        'boundary_algebraic_matrix': r,
        'sparse_union_movement': r+Q(13, 32),
        'polynomial_products': 1-d-C+loss,
        'microbox_face_corrections': 77+4*d-C+loss,
    }
    require(all(value > 0 for value in excess.values()), 'main transform uniquely binds nine costs')
    require(all(gaps[name]-gaps['main_transform'] == value for name, value in excess.items()),
            'independent expanded gap/excess identities')
    require(c+xi-epsilon == main+r and xi+Q(1, 2)-epsilon == main+r+Q(13, 32),
            'boundary and union exact balances')

    # Endpoint/interpolation identities: sigma<tau, so the internal maximum
    # branch is exactly tau. Every comparison is rational, including stop loss.
    tau, sigma = 1-a, 1-b
    internal, leaf = tau, sigma+stop*b
    lam = 1-C+Q(7, 4)*r
    balances = dict(complex_to_effective=b-a, effective_to_q=a-q, complex_to_q=b-q,
                    leaf_to_effective=r/2-stop*b, leaf_to_q=r-stop*b,
                    lambda_to_tau=r/4, lambda_to_sigma=3*r/4,
                    lambda_to_internal=r/4, lambda_prime_to_lambda=r/4)
    require(sigma < tau and internal == tau+(1-stop)*max(sigma-tau, Q(0)), 'internal branch identity')
    require(lam == 1-(q+a)/2 and 1-leaf-a == balances['leaf_to_effective'] and
            1-leaf-q == balances['leaf_to_q'], 'leaf and lambda expanded identities')
    require(all(value > 0 for value in balances.values()), 'strict interpolation balances')
    old, oldC = Q(source_claim['kappa']), Q(source_claim['complex_lower'])
    require(old == oldC-quantum-backoff and K > old and K-old == C-oldC,
            'strict rational headline gain at unchanged deductions')
    if primary is not None:
        require(primary['status'] == 'PASS_CONDITIONAL_OUTER_ARITHMETIC', 'primary checker completed')
        ledger = primary['ledger']
        require(Q(ledger['kappa']) == K, 'two independent headline computations agree')
        for name, gap in gaps.items():
            require(Q(ledger['savings'][name])-K == gap and
                    Q(ledger['strict_checks'][name+'_above_kappa']) == gap,
                    'independent cost gap agrees: ' + name)
        params = dict(C=C, r=r, delta=d, epsilon=epsilon, beta=beta, b=b, q=q, a=a,
                      stop=stop, xi=xi, theta=theta, halo=halo, core=core, matrix=matrix)
        require(all(Q(ledger['parameters'][name]) == value for name, value in params.items()),
                'both checkers use the exact same registered point')
    return encode(dict(status='PASS_INDEPENDENT_CLOSED_FORM_OUTER_BALANCE',
                       complex_lower=C, kappa=K, strict_gain=K-old, source_kappa=old,
                       subgrid_loss=loss, grid_quantum=quantum, fixed_backoff=backoff,
                       grid_identity='floor((1-delta)*(C-2r)*10^70)/10^70-10^-46 = C-10^-70-10^-46',
                       nine_saving_gaps=gaps, eight_strict_excesses_above_main=excess,
                       interpolation_balances=balances, bit_supplier_margin=bit-C,
                       primary_crosscheck=primary is not None,
                       scope='Independent exact algebraic derivation and primary-output crosscheck; requires separate native/supplier evidence and full functional outer gates. Inherited theorem hypotheses remain.'))
