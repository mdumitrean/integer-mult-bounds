"""pfslib: prepend-free exact solver (see pfs.py doc) as a library, with optional exact PRE-EDIT (non-q gate moves).
A pre-edit is a B-only edit E1 (delete/insert relative to the base word) preserving the map; the solver then deletes q's
reads D (base indices, not touched by E1), compensates on the pre-edited word, and composes everything into ONE edit
relative to the base word."""
import sys, os, json, itertools, bisect, collections, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from lucore import lu
import sx
def compiled_B_with_prov(w, ed):
    """compiled B list of base word w under B-only edit ed, with provenance ('b', i) or ('n', gate)."""
    B = w['B']; dele = set(ed.get('delete', [])); at = collections.defaultdict(list)
    for p, g in ed.get('insert', []): at[p].append(g)
    out = []
    for i in range(len(B) + 1):
        for g in at.get(i, []): out.append(('n', list(g)))
        if i < len(B) and i not in dele: out.append(('b', i))
    return out
def prov_to_edit(nB, items, tail=(), prepend=()):
    """final B sequence as provenance items -> edit relative to base (base gates must stay in increasing order)."""
    present = [x[1] for x in items if x[0] == 'b']
    assert present == sorted(present)
    dele = sorted(set(range(nB)) - set(present)); ins = []; pending = []
    for x in items:
        if x[0] == 'n': pending.append(x[1])
        else:
            for g in pending: ins.append([x[1], g])
            pending = []
    for g in pending: ins.append([nB, g])
    return dict(delete=dele, insert=ins, tail=[list(t) for t in tail], prepend=[list(p) for p in prepend])
class PFS:
    def __init__(self, P, q, pre=None):
        """P: Pricer on the base word; q: pivot; pre: B-only exact pre-edit (dict) or None."""
        self.P = P; self.q = q; self.w = P.base; self.pre = pre or dict(delete=[], insert=[])
        self.nB = len(self.w['B']); self.NREG = sx.nregs(self.w)
        fe0 = lambda r: (r < 112 or r >= 224) and str(r) not in self.w['helper_final']
        self.prepend_ok = fe0(q)       # cleanup prepends must read a FULL-end q; otherwise no free coordinates
        self.full_end = fe0 if self.prepend_ok else (lambda r: False)
        self.prov0 = compiled_B_with_prov(self.w, self.pre)
        self.Breads0 = [k for k, x in enumerate(self.prov0) if x[0] == 'b' and self.w['B'][x[1]][0] == 'add' and self.w['B'][x[1]][2] == q]
    def run(self, Dbase, K, maxsets=64):
        """Dbase: base B indices of q-reads to delete (must be present in the pre-edited word)."""
        w = self.w; q = self.q; P = self.P
        prov = [x for x in self.prov0 if not (x[0] == 'b' and x[1] in set(Dbase))]
        B1 = [list(w['B'][x[1]]) if x[0] == 'b' else list(x[1]) for x in prov]
        w1 = H.compile_edits(w, prov_to_edit(self.nB, prov)); assert len(w1['B']) == len(B1)
        nB1 = len(B1); tail1 = [w1['cleanup'][i] for i, U in w1['early_cleanup']]; seq1 = list(w1['B']) + tail1; L1 = len(seq1)
        # d: q-column of (pre-edited word) minus (deleted word)  [exact, via forward columns]
        seq_pre = [list(w['B'][x[1]]) if x[0] == 'b' else list(x[1]) for x in self.prov0] + tail1
        d = sx.addv(sx.col(seq_pre, q), sx.col(seq1, q), -1)
        fe = self.full_end
        dp = {k: v for k, v in d.items() if not fe(k)}
        S1 = sx.Suffix(seq1, self.NREG)
        res = lu(inline(w1, True), P.caps)
        if res['bad']: return dict(status='deleted-word-infeasible', d=d, cands=[])
        nodes, chains, lower, upper = res['nodes'], res['chains'], res['lower'], res['upper']
        def tkey(k):
            sec, idx = nodes[k][2], nodes[k][3]
            return {'start': -3, 'A': -2, 'cut': -1}[sec] if sec in ('start', 'A', 'cut') else (idx if sec == 'B' else (nB1 + idx if sec == 'tail' else 10 ** 9))
        qch = chains[q]; qt = [tkey(k) for k in qch]
        sp = lambda X: F.span(tuple(X)); leq = lambda a, b: sp(a) <= sp(b)
        def meet(a, b):
            sb = sp(b); return F.basis(tuple(x for x in sp(a) if x in sb))
        def slot_info(y, p):
            ch = chains[y]; ts = [tkey(k) for k in ch]; j = bisect.bisect_left(ts, p)
            a, b = ch[j - 1], ch[j]
            if nodes[a][2] in ('tail', 'end') and p <= nB1: return None
            jq = bisect.bisect_left(qt, p); qa, qb = qch[jq - 1], qch[jq]
            Ly = lower[a]; Uy = upper[b]
            if p <= nB1 and nodes[b][2] in ('tail', 'end') and y in P.caps: Uy = meet(Uy, P.caps[y])
            Uqq = upper[qb]
            if p <= nB1 and nodes[qb][2] in ('tail', 'end') and q in P.caps: Uqq = meet(Uqq, P.caps[q])
            return Ly, Uy, lower[qa], Uqq
        events = collections.defaultdict(list)
        for i, g in enumerate(seq1):
            for r in (g[1:3] if g[0] == 'add' else g[1:2]): events[r].append(i)
        atoms = []
        for y in range(self.NREG):
            if y == q: continue
            for lo, hi, v in S1.intervals(y):
                vp = {k: c for k, c in v.items() if not fe(k)}
                if not vp: continue
                ev = sorted(set(e for r in (y, q) for e in events.get(r, []) if lo <= e < hi))
                slots = []
                for p in sorted(set([lo] + [e + 1 for e in ev])):
                    if p > L1: continue
                    si = slot_info(y, p)
                    if si is None: continue
                    Ly, Uy, Lq, Uq = si; Lnew = F.basis(tuple(Ly) + tuple(Lq))
                    if leq(Lnew, Uy) and leq(Lnew, Uq): slots.append((p, Ly, Uy))
                if slots: atoms.append(dict(y=y, lo=lo, hi=hi, v=v, vp=vp, slots=slots))
        mask = lambda vec: sum(1 << k for k in vec); Dm = mask(dp)
        for a in atoms: a['m'] = mask(a['vp'])
        inv = collections.defaultdict(list)
        for i, a in enumerate(atoms):
            m = a['m']
            while m:
                b = (m & -m).bit_length() - 1; inv[b].append(i); m &= m - 1
        def solve(idx):
            keys = sorted(set(dp).union(*[atoms[i]['vp'].keys() for i in idx])); kk = len(idx)
            rows = [[atoms[i]['vp'].get(c, Q(0)) for i in idx] + [dp.get(c, Q(0))] for c in keys]; r = 0
            for cidx in range(kk):
                pv = next((i for i in range(r, len(rows)) if rows[i][cidx] != 0), None)
                if pv is None: return None
                rows[r], rows[pv] = rows[pv], rows[r]; x = rows[r][cidx]; rows[r] = [z / x for z in rows[r]]
                for i in range(len(rows)):
                    if i != r and rows[i][cidx] != 0:
                        f = rows[i][cidx]; rows[i] = [z - f * yv for z, yv in zip(rows[i], rows[r])]
                r += 1
            if any(rows[i][kk] != 0 for i in range(r, len(rows))): return None
            sol = [rows[i][kk] for i in range(kk)]
            if any(b == 0 or not sx.dyadic(b) for b in sol): return None
            return sol
        sols = []; seen = set()
        def dfs(chosen, cover, oc):
            if chosen and (cover & Dm) == Dm and all(c >= 2 for c in oc.values()):
                key = tuple(sorted(chosen))
                if key not in seen:
                    seen.add(key); s = solve(list(key))
                    if s: sols.append((key, s))
            if len(chosen) >= K: return
            need = [b for b in sorted(dp) if not (cover >> b) & 1]; once = sorted(b for b, c in oc.items() if c == 1)
            b = need[0] if need else (once[0] if once else None)
            if b is None: return
            for i in inv.get(b, []):
                if i in chosen: continue
                o2 = dict(oc); m = atoms[i]['m'] & ~Dm
                while m:
                    bb = (m & -m).bit_length() - 1; o2[bb] = o2.get(bb, 0) + 1; m &= m - 1
                dfs(chosen + [i], cover | atoms[i]['m'], o2)
        if dp: dfs([], 0, {})
        else: sols.append(((), []))
        cands = []; seen_ed = set()
        for key, sol in sols:
            opts = [atoms[i]['slots'] for i in key]; got = 0
            for combo, order in ((c, o) for c in itertools.product(*opts) for o in itertools.permutations(range(len(key)))):
                if any(combo[order[x]][0] > combo[order[x + 1]][0] for x in range(len(order) - 1)): continue
                if any(combo[order[x]][0] == combo[order[x + 1]][0] and order[x] > order[x + 1] and False for x in range(len(order) - 1)): continue
                if any(not leq(combo[order[x]][1], combo[order[yy]][2]) for x in range(len(order)) for yy in range(x + 1, len(order))): continue
                # compose: B inserts at compiled positions -> provenance list; tail inserts relative to tail
                items = list(prov); bins = collections.defaultdict(list); tl = []; pre_vec = dict(d)
                for j in order:
                    i = key[j]; a = atoms[i]; b = sol[j]; p = combo[j][0]; gt = gate(a['y'], q, b)
                    if p <= nB1: bins[p].append(gt)
                    else: tl.append([p - nB1, gt])
                    pre_vec = sx.addv(pre_vec, a['v'], -b)
                assert all(fe(k) for k in pre_vec), pre_vec
                out = []
                for k in range(nB1 + 1):
                    for g in bins.get(k, []): out.append(('n', g))
                    if k < nB1: out.append(items[k])
                tl.sort(key=lambda z: z[0]); tl = [[j0 + n, g] for n, (j0, g) in enumerate(tl)]
                ed = prov_to_edit(self.nB, out, tail=tl, prepend=[gate(k, q, c) for k, c in sorted(pre_vec.items())])
                kk = json.dumps(ed, sort_keys=True)
                if kk in seen_ed: continue
                seen_ed.add(kk)
                cands.append(dict(atoms=[[atoms[i]['y'], atoms[i]['lo'], atoms[i]['hi'], str(sol[j])] for j, i in enumerate(key)],
                                  slots=[combo[j][0] for j in range(len(key))], nprepend=len(ed['prepend']), ed=ed))
                got += 1
                if got >= maxsets: break
        return dict(status='ok', d=d, natoms=len(atoms), nsols=len(sols), cands=cands)
