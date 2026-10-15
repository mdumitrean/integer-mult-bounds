"""carrier: value-equality carrier substitution for the copy-window pivots (r4 A-reroute).
At a B (or tail) read  t += c*q  at position i, compute every register's value just before i as an exact linear function
of the program's initial state (precondition + derived compensation + A + cut + B[:i]).  If sum_x lam_x * value_x(i) ==
value_q(i) for registers x != q, t, the read may be replaced by reads  t += c*lam_x*x  at the same position: the main
map (A+cut+B) and the whole call map are unchanged (so is the derived compensation), but the B meets of q are replaced
by meets of the carriers.  Singles (copies) and pairs are enumerated per read; then every combination that replaces ALL of
q's B reads is priced as well (that frees q's A-end frame from the port cap).
usage: carrier.py WORD q..."""
import sys, os, json, time, itertools, collections, resource
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from awin import *
wname = sys.argv[1]; qs = list(map(int, sys.argv[2:]))
P = H.Pricer(WORDS[wname], b=os.environ['IMB_B'], check_literal=True); w = P.base
caps0, comp0 = cone_caps(w); map0 = apply_rows(prog(w, comp0))
pre_main = list(w['precondition']) + comp0 + list(w['A']) + list(w['cut'])
B = w['B']; tailidx = [i for i, U in w['early_cleanup']]; tail = [w['cleanup'][i] for i in tailidx]
NREG = 2 * 112 + w['report']['R']
def snapshot_rows(positions):
    """rows before each B position in `positions` (sorted)."""
    rows = apply_rows(pre_main); out = {}; pos = sorted(positions); j = 0
    for i, g in enumerate(B):
        while j < len(pos) and pos[j] == i: out[i] = {k: dict(v) for k, v in rows.items()}; j += 1
        apply_rows([g], rows)
    return out
def val(rows, x): return rows.get(x, {x: Q(1)})
def solve2(v, a, b):
    keys = sorted(set(v) | set(a) | set(b))
    rows = [[a.get(k, Q(0)), b.get(k, Q(0)), v.get(k, Q(0))] for k in keys]
    # exact elimination for two unknowns
    r = 0; piv = []
    for c in range(2):
        p = next((i for i in range(r, len(rows)) if rows[i][c] != 0), None)
        if p is None: return None
        rows[r], rows[p] = rows[p], rows[r]; x = rows[r][c]; rows[r] = [z / x for z in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][c] != 0:
                f = rows[i][c]; rows[i] = [z - f * y for z, y in zip(rows[i], rows[r])]
        r += 1
    if any(rows[i][2] != 0 for i in range(r, len(rows))): return None
    l1, l2 = rows[0][2], rows[1][2]
    if l1 == 0 or l2 == 0 or not sx.dyadic(l1) or not sx.dyadic(l2): return None
    return l1, l2
def build_sub(subs):
    """subs: {B index i: [(x, lam), ...]} replacing read B[i] = t += c*q by t += c*lam*x."""
    ins = []
    for i, lst in subs.items():
        g = B[i]; t, c = g[1], coef(g)
        for x, lam in lst: ins.append([i, gate(t, x, c * lam)])
    return H.compile_edits(w, dict(delete=sorted(subs), insert=ins, tail=[], prepend=[]))
results = {}
for q in qs:
    t0 = time.time()
    reads = [i for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
    snaps = snapshot_rows(reads)
    per = {}
    for i in reads:
        rows = snaps[i]; v = val(rows, q); t = B[i][1]
        supp = set(v)
        cands = [x for x in range(NREG) if x not in (q, t) and set(val(rows, x)) & supp]
        singles = [(x, Q(1)) for x in cands if val(rows, x) == v] + [(x, Q(-1)) for x in cands if {k: -c for k, c in val(rows, x).items()} == v]
        pairs = []
        for a, b in itertools.combinations(cands, 2):
            va, vb = val(rows, a), val(rows, b)
            if not (supp <= set(va) | set(vb)): continue
            s = solve2(v, va, vb)
            if s: pairs.append(((a, s[0]), (b, s[1])))
        per[i] = dict(target=t, coef=str(coef(B[i])), q_value_support=len(supp), candidates=len(cands), singles=[[x, str(l)] for x, l in singles], pairs=[[[a, str(la)], [b, str(lb)]] for (a, la), (b, lb) in pairs])
        print(q, 'read B%d' % i, '->', t, 'support', len(supp), 'cands', len(cands), 'singles', len(singles), 'pairs', len(pairs), flush=True)
    # price: each single substitution alone, and full replacements (all reads) from the substitution options
    opts = {i: [[(x, Q(l))] for x, l in per[i]['singles']] + [[(a, Q(la)), (b, Q(lb))] for (a, la), (b, lb) in per[i]['pairs']] for i in reads}
    priced = []
    def run(subs, kind):
        w1 = build_sub(subs); m1 = apply_rows(prog(w1, cone_caps(w1)[1]))
        exact = all(map0.get(k, {k: Q(1)}) == m1.get(k, {k: Q(1)}) for k in set(map0) | set(m1))
        comp_same = cone_caps(w1)[1] == comp0
        pr = price(w1, P.costs, P.base_cost) if exact else dict(status='inexact')
        priced.append(dict(kind=kind, subs={str(i): [[x, str(l)] for x, l in lst] for i, lst in subs.items()}, exact=exact, comp_unchanged=comp_same, price=pr))
        print('  ', q, kind, {i: [(x, str(l)) for x, l in lst] for i, lst in subs.items()}, 'exact', exact, 'comp_same', comp_same, '->', pr.get('status'), pr.get('delta'), pr.get('profile'), flush=True)
    for i in reads:
        for o in opts[i][:12]: run({i: o}, 'one-read')
    if all(opts[i] for i in reads):
        combos = list(itertools.product(*[opts[i][:4] for i in reads]))[:24]
        for cmb in combos: run(dict(zip(reads, cmb)), 'all-reads')
    results[q] = dict(reads=per, priced=priced, seconds=round(time.time() - t0, 1))
    print(f'q={q}: priced {len(priced)} negative {sum(1 for r in priced if (r["price"].get("delta") or 0) < 0)} {time.time()-t0:.0f}s rss {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**3:.2f}GiB', flush=True)
json.dump(results, open(os.path.join(HERE, '..', 'out', f'CARRIER-{wname}-{"-".join(map(str, qs))}.json'), 'w'), indent=1, default=str)
