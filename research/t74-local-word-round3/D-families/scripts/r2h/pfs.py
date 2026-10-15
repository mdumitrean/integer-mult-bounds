"""pfs: prepend-free exact solver for q-read compensations with an exact joint frame-feasibility screen.
Family PFS(q, D, k): delete the B reads D of pivot q; the deleted q-column d = sum c_r S_{t_r}(r+1) is compensated by
  (a) <= k inserted q-reads y += b*q in B or the early tail, one per atom (register y, S-constant interval J), and
  (b) FREE cleanup prepends k += c*q on every FULL-end coordinate k (sources < 112 and helpers without helper_final; q has a
      FULL end), absorbing all FULL-end coordinates of d - sum b S_y.
Exactness: sum b_i S'_{y_i} = d' on non-FULL-end coordinates (exact Fractions, dyadic b).  Frames: every inserted read must
sit in a single-feasible slot and every time-ordered pair (i < j) must satisfy L_{y_i} <= U_{y_j} (exact pairwise L/U
criterion for reads sharing q's chain, verified against full graph builds).  Output: candidate edits (base coordinates).
usage: pfs.py WORD q D(comma B idx | all) k OUT.json [--maxsets N]"""
import sys, os, json, itertools, bisect, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from lucore import lu
import sx
WN = sys.argv[1]; q = int(sys.argv[2]); K = int(sys.argv[4]); OUT = sys.argv[5]
MAXSETS = int(sys.argv[sys.argv.index('--maxsets') + 1]) if '--maxsets' in sys.argv else 64
P = H.Pricer(WORDS[WN], check_literal=True); w = P.base; B = w['B']; nB = len(B)
Breads = [i for i, g in enumerate(B) if g[0] == 'add' and g[2] == q]
D = Breads if sys.argv[3] == 'all' else [int(x) for x in sys.argv[3].split(',')]
assert set(D) <= set(Breads)
ed0 = dict(delete=sorted(D), insert=[], tail=[], prepend=[])
w1 = H.compile_edits(w, ed0); nB1 = len(w1['B']); tail1 = [w1['cleanup'][i] for i, U in w1['early_cleanup']]
seq1 = list(w1['B']) + tail1; L1 = len(seq1); NREG = sx.nregs(w)
base_of = [i for i in range(nB) if i not in set(D)]      # compiled B index -> base B index
full_end = lambda r: (r < 112 or r >= 224) and str(r) not in w['helper_final']
assert full_end(q)
# d on the base sequence
seq0 = sx.build_seq(w)[2]; S0 = sx.Suffix(seq0, NREG)
d = {}
for r in D: d = sx.addv(d, S0.at(seq0[r][1], r + 1), sx.coef(seq0[r]))
dp = {k: v for k, v in d.items() if not full_end(k)}
print('pivot', q, 'D', D, 'd', {k: str(v) for k, v in sorted(d.items())}, "d'", sorted(dp), flush=True)
# suffix effects on the compiled sequence (identical to base for x != q)
S1 = sx.Suffix(seq1, NREG)
res = lu(inline(w1, True), P.caps); nodes, chains, lower, upper = res['nodes'], res['chains'], res['lower'], res['upper']
assert not res['bad'], 'deleted word infeasible'
def tkey(k):
    sec, idx = nodes[k][2], nodes[k][3]
    if sec == 'start': return -3
    if sec == 'A': return -2
    if sec == 'cut': return -1
    if sec == 'B': return idx
    if sec == 'tail': return nB1 + idx
    return 10 ** 9
qch = chains[q]; qt = [tkey(k) for k in qch]
sp = lambda X: F.span(tuple(X))
def leq(a, b): return sp(a) <= sp(b)
def meet(a, b):
    sb = sp(b); return F.basis(tuple(x for x in sp(a) if x in sb))
def slot_info(y, p):
    """insert y += q before compiled seq position p (p <= nB1: B; else tail index p - nB1). returns (Ly, Uy, Lq, Uq)."""
    ch = chains[y]; ts = [tkey(k) for k in ch]
    j = bisect.bisect_left(ts, p)        # first vertex of y with time >= p  (vertex at time p is AFTER the insert)
    a, b = ch[j - 1], ch[j]
    if nodes[a][2] in ('tail', 'end') and p <= nB1: return None
    jq = bisect.bisect_left(qt, p); qa, qb = qch[jq - 1], qch[jq]
    Ly = lower[a]; Uy = upper[b]
    if p <= nB1 and nodes[b][2] in ('tail', 'end'):
        if y in P.caps: Uy = meet(Uy, P.caps[y])
    Uqq = upper[qb]
    if p <= nB1 and nodes[qb][2] in ('tail', 'end') and q in P.caps: Uqq = meet(Uqq, P.caps[q])
    return Ly, Uy, lower[qa], Uqq
events = collections.defaultdict(list)
for i, g in enumerate(seq1):
    for r in (g[1:3] if g[0] == 'add' else g[1:2]): events[r].append(i)
# atoms with feasible slots
atoms = []
t0 = time.time()
for y in range(NREG):
    if y == q: continue
    for lo, hi, v in S1.intervals(y):
        vp = {k: c for k, c in v.items() if not full_end(k)}
        if not vp: continue
        if not (set(vp) & set(dp)) and True: pass
        ev = sorted(set(e for r in (y, q) for e in events.get(r, []) if lo <= e < hi))
        reps = sorted(set([lo] + [e + 1 for e in ev]))
        slots = []
        for p in reps:
            if p > L1: continue
            si = slot_info(y, p)
            if si is None: continue
            Ly, Uy, Lq, Uq = si
            Lnew = F.basis(tuple(Ly) + tuple(Lq))
            if leq(Lnew, Uy) and leq(Lnew, Uq): slots.append((p, Ly, Uy))
        if slots: atoms.append(dict(y=y, lo=lo, hi=hi, v=v, vp=vp, slots=slots))
print('atoms with feasible slots', len(atoms), f'{time.time()-t0:.1f}s', flush=True)
# exact sparse solve: sum b_i vp_i = dp, <= K atoms, support pruning
mask = lambda vec: sum(1 << k for k in vec)
Dm = mask(dp)
for a in atoms: a['m'] = mask(a['vp'])
inv = collections.defaultdict(list)
for i, a in enumerate(atoms):
    m = a['m']
    while m:
        b = (m & -m).bit_length() - 1; inv[b].append(i); m &= m - 1
def solve(idx):
    keys = sorted(set(dp).union(*[atoms[i]['vp'].keys() for i in idx])); kk = len(idx)
    rows = [[atoms[i]['vp'].get(c, Q(0)) for i in idx] + [dp.get(c, Q(0))] for c in keys]
    r = 0
    for cidx in range(kk):
        pv = next((i for i in range(r, len(rows)) if rows[i][cidx] != 0), None)
        if pv is None: return None
        rows[r], rows[pv] = rows[pv], rows[r]; x = rows[r][cidx]; rows[r] = [z / x for z in rows[r]]
        for i in range(len(rows)):
            if i != r and rows[i][cidx] != 0:
                f = rows[i][cidx]; rows[i] = [z - f * y for z, y in zip(rows[i], rows[r])]
        r += 1
    if any(rows[i][kk] != 0 for i in range(r, len(rows))): return None
    sol = [rows[i][kk] for i in range(kk)]
    if any(b == 0 or not sx.dyadic(b) for b in sol): return None
    return sol
sols = []; seen = set()
def dfs(chosen, cover, outside_cnt):
    # cover: OR of masks; need cover >= Dm and every outside bit at least twice
    if chosen:
        out_ok = all(c >= 2 for c in outside_cnt.values())
        if (cover & Dm) == Dm and out_ok:
            key = tuple(sorted(chosen))
            if key not in seen:
                seen.add(key); s = solve(list(key))
                if s: sols.append((key, s))
    if len(chosen) >= K: return
    # branch on lowest unmet requirement: an uncovered d' bit, or an outside bit seen once
    need = [b for b in range(NREG) if (Dm >> b) & 1 and not (cover >> b) & 1]
    once = [b for b, c in outside_cnt.items() if c == 1]
    if need: b = need[0]
    elif once: b = once[0]
    else: return
    for i in inv.get(b, []):
        if chosen and i <= max(chosen) and False: continue
        if i in chosen: continue
        oc = dict(outside_cnt)
        m = atoms[i]['m'] & ~Dm
        while m:
            bb = (m & -m).bit_length() - 1; oc[bb] = oc.get(bb, 0) + 1; m &= m - 1
        dfs(chosen + [i], cover | atoms[i]['m'], oc)
t0 = time.time(); dfs([], 0, {}); print('exact atom solutions', len(sols), f'{time.time()-t0:.1f}s', flush=True)
# slot assignment with pairwise screen
def to_base(p):
    if p <= nB1: return ('B', base_of[p] if p < nB1 else nB)
    return ('T', p - nB1)
cands = []
nsets = collections.Counter()
for key, sol in sols:
    opts = [atoms[i]['slots'] for i in key]; got = 0
    for combo in itertools.product(*opts):
        order = sorted(range(len(key)), key=lambda j: combo[j][0])
        ok = True
        for x in range(len(order)):
            for y_ in range(x + 1, len(order)):
                i1, i2 = order[x], order[y_]
                if combo[i1][0] == combo[i2][0]: continue  # same position: order resolved by list order (both directions tried below)
                if not leq(combo[i1][1], combo[i2][2]): ok = False; break
            if not ok: break
        if not ok: continue
        # build edit
        ins = []; tl = []; pre_vec = dict(d)
        for j, i in enumerate(key):
            a = atoms[i]; b = sol[j]; p = combo[j][0]; sec, bp = to_base(p)
            gt = gate(a['y'], q, b)
            if sec == 'B': ins.append([bp, gt])
            else: tl.append([bp, gt])
            pre_vec = sx.addv(pre_vec, a['v'], -b)
        assert all(full_end(k) for k in pre_vec), pre_vec
        tl.sort(key=lambda z: z[0]); tl = [[j0 + n, g] for n, (j0, g) in enumerate(tl)]
        ed = dict(delete=sorted(D), insert=sorted(ins, key=lambda z: z[0]), tail=tl, prepend=[gate(k, q, c) for k, c in sorted(pre_vec.items())])
        cid = f"PFS-{q}-D{'_'.join(map(str, D))}-" + '+'.join(f"{atoms[i]['y']}@{combo[j][0]}" for j, i in enumerate(key))
        cands.append(dict(id=cid, fam='PFS', pivot=q, D=D, atoms=[[atoms[i]['y'], atoms[i]['lo'], atoms[i]['hi'], str(sol[j])] for j, i in enumerate(key)], ed=ed))
        got += 1
        if got >= MAXSETS: break
    nsets[len(key)] += got
print('slot-feasible candidate edits', len(cands), dict(nsets), flush=True)
json.dump(cands, open(OUT, 'w'))
