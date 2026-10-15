"""borrow_price.py: exact frame pricing of BORROW-WORD edits (r8 shared harness; r9 B-retired copy pinned to #2745's package).

Frame model = the BORROW-WORD branch of #2474's audit_local.py (new/borrow/audit_local.py, run_borrow):
  * every A (after the prelude), prelude target write, B and restore gate is one vertex whose frame is shared by its registers;
  * register chains are monotone (nested), every rank jump is paid; ends climb (paid) to the end frames;
  * at the end of A the targets equal their target levels and the centres their centre frames (cut equality);
  * a warp (B-phase record [pos, lender, G, U, E], or an A-phase prelude item ['warp', r, op, fr, to]) requires the lender's
    current frame to EQUAL U (resp. fr) with no payment and resets it to E (resp. to).
Warps are modelled by splitting the lender's chain into virtual registers: the segment before a warp ends in an
'end' vertex fixed to U with an equality constraint (no paid jump), the segment after starts at E.
Centre descents (cut paths) are fixed and added as the auditor counts them.
Solving uses our #1186 toolkit (frames.optimal_frames: exact chain dual decomposition / variable elimination, certified).

API (see HARNESS.md):
  w = load(path)                          BORROW-WORD dict
  pf = frame_profile(w, b, literal=False) dict(profile, cost, certified, seconds, assign, ...) for the word's gate order
  w1 = edit_B(w, delete=[i,...], insert=[(i, gate), ...])   gate-level B edit (warp positions shifted, cleanup re-derived)
  w1 = apply_patch(w, kind, patch)        word_patch.apply_kernel / apply_handoff / apply_lowfour
  wf = write_frames(w1, pf)               word with optimal frames written back + report.local_profile
  a = audit(wf)                            the package's unchanged auditor (subprocess); dict(rc, status, receipt)
  r = price(w0, w1, b)                     full pipeline: frames(w0) cached, frames(w1), write back, audit; dict(delta, ...)
"""
import collections, copy, gzip, json, os, resource, subprocess, sys, tempfile, time
from pathlib import Path

# Relocated for research/t74-r10-hosting-leads (was a scratchpad layout); every path can be overridden by environment.
REPO = Path(__file__).resolve().parents[4]                      # repository root (research/t74-r10-hosting-leads/J-dim1/code)
TOOLKIT = Path(os.environ.get('IMB_TOOLKIT', REPO / 'research/t74-r10-hosting-leads/deps/toolkit-rev3'))   # our #1186 toolkit rev3
MAIN = REPO
PKG = Path(os.environ.get('IMB_PR2745_PKG', REPO / 'research/gmx-t74-borrow43-handoff'))   # optional: #2745's package (git fetch origin pull/2745/head)
BORROW = PKG / 'new/borrow'                                     # word_patch.py is also in this directory (byte-identical copy)
AUDITOR = Path(os.environ.get('IMB_AUDITOR', REPO / 'research/t74-joint-twelve-retired7/vendor/audit_local_pr2679.py'))   # pinned PR2679 auditor (#2802)
B_DEFAULT = '0.001717409316335491'   # r10: our candidate's endpoint, rounded down
os.environ.setdefault('IMB_ROOT', str(MAIN))
sys.path.insert(0, str(TOOLKIT))
import frames as F                                              # noqa: E402  (our #1186 toolkit, revision 3)
from frames import basis, span, leq, Infeasible                 # noqa: E402
sys.path.insert(0, str(BORROW))
import word_patch                                               # noqa: E402  (#2474's patch helpers, read before use)

V = 112; H = 9
FULL9 = tuple(basis(tuple(1 << i for i in range(H))))


def load(path):
    return json.loads(gzip.decompress(Path(path).read_bytes()))


def dump(w, path):
    Path(path).write_bytes(gzip.compress(json.dumps(w, separators=(',', ':')).encode()))


def _perp_port(p):
    return tuple(basis(tuple(x for x in range(1, 1 << H) if (x & p).bit_count() % 2 == 0)))


def contained(a, b):
    return span(tuple(a)) <= span(tuple(b))


def centre_descents(w):
    """the auditor's cut-path payments (fixed by centre frames, target levels and cut gates)"""
    lev = {int(t): tuple(basis(tuple(U))) for t, U in w.get('target_levels', {}).items()}
    paid = collections.Counter()
    for q, U in zip(w['centers'], w['center_frames']):
        U = tuple(basis(tuple(U)))
        served = {lev.get(e[1] - V, ()) for e in w['cut'] if e[2] == q}
        for T in sorted(served, key=lambda x: -len(x)):
            assert contained(T, U), 'center path not nested'
            if T != U: paid[len(U) - len(T)] += 1
            U = T
    return paid


def build_problem(w):
    """BORROW-WORD -> standard inline word for the toolkit Graph with virtual registers split at warps.
    Returns (w2, meta). meta['A_idx'][i] = index in w['A'] of w2['A'][i]; B and restore keep their indices."""
    R = w['report']['R']; N = 2 * V + R
    removed = set(w['removed'])
    start = [(p,) for p in w['ports']] + [()] * (V + R)
    for q, U in w.get('start_extra', {}).items(): start[int(q)] = tuple(basis(tuple(U)))
    end = [FULL9] * V + [_perp_port(p) for p in w['ports']] + [FULL9] * R
    for q, U in w.get('helper_final', {}).items(): end[int(q)] = tuple(basis(tuple(U)))
    starts = list(start); finals = [None] * N            # finals filled when a segment closes
    alias = list(range(N)); eq_end = set(); nxt_virtual = [N]
    def close_and_split(r, fr, to):
        # close the current segment of r at frame fr (equality), open a fresh virtual register starting at `to`
        cur = alias[r]; finals[cur] = tuple(basis(tuple(fr)))
        eq_end.add(cur)
        new = nxt_virtual[0]; nxt_virtual[0] += 1
        starts.append(tuple(basis(tuple(to)))); finals.append(None); alias[r] = new
    def ren(e):
        g = list(e)
        if g[0] == 'add': g[1] = alias[g[1]]; g[2] = alias[g[2]]
        else: g[1] = alias[g[1]]
        return g
    npre = w.get('prelude_events', 0); A_out = []; A_idx = []
    for i, e in enumerate(w['A']):
        if e[0] == 'warp':
            assert i < npre, 'warp after prelude'
            _, r, op, fr, to = e; close_and_split(r, fr, to)
        else:
            A_out.append(ren(e)); A_idx.append(i)
    centers_at_cut = [alias[q] for q in w['centers']]
    byp = collections.defaultdict(list)
    for op, rec in enumerate(w['warps'], 1): byp[rec[0]].append(op)
    B_out = []
    for p in range(len(w['B']) + 1):
        for op in byp.get(p, []):
            pos, lender, cols, U, E = w['warps'][op - 1]; close_and_split(lender, U, E)
        if p < len(w['B']): B_out.append(ren(w['B'][p]))
    T_out = [ren(e) for e in w['restore']]
    Nv = nxt_virtual[0]
    for r in range(N):
        a = alias[r]
        if finals[a] is None: finals[a] = end[r]
    for r in removed:                                   # removed helpers: no gates, no paid jump
        starts[r] = (); finals[r] = ()
        assert alias[r] == r
    assert all(f is not None for f in finals)
    w2 = dict(A=A_out, B=B_out, _tail=T_out, ports=w['ports'], centers=centers_at_cut, center_frames=w['center_frames'],
              target_levels=w.get('target_levels', {}), report=dict(R=Nv - 2 * V),
              _start_frames=[list(s) for s in starts], _final_frames=[list(f) for f in finals])
    meta = dict(N=N, Nv=Nv, eq_end=eq_end, A_idx=A_idx, virtual=Nv - N, removed=len(removed))
    return w2, meta


class BorrowGraph(F.Graph):
    """toolkit Graph (rev3 logic) plus equality at the 'end' vertices of registers in eq_end (warp entry frames)."""
    def __init__(self, w, eq_end, check_literal=True, tail_mutable=True, caps=None, cut_equality=True):
        self.w = w; R = F.R_of(w); N = 2 * V + R; self.N = N; self.check_literal = check_literal; self.tail_mutable = tail_mutable
        caps = caps or {}; self.caps = caps; self.cut_equality = cut_equality
        nodes = []; chains = [[] for _ in range(N)]; mutable = []
        start_frames = w.get("_start_frames"); final_frames = w.get("_final_frames"); tail = w.get("_tail", [])
        def node(regs, Fr, sec, index=None):
            k = len(nodes); nodes.append((tuple(regs), basis(tuple(Fr)), sec, index))
            for r in regs: chains[r].append(k)
            if sec in ("A", "B") or (sec == "tail" and tail_mutable): mutable.append(k)
        for r in range(N): node([r], start_frames[r], "start")
        for sec in ("A", "B"):
            if sec == "B":
                for r, Fr in zip(w["centers"], w["center_frames"]): node([r], Fr, "cut")
                for t in range(V): node([V + t], w.get("target_levels", {}).get(str(t), []), "cut")
            for i, e in enumerate(w[sec]): node(F.regs_of(e), e[-1] if e[-1] is not None else [], sec, i)
        for i, e in enumerate(tail): node(F.regs_of(e), e[-1], "tail", i)
        for r in range(N): node([r], final_frames[r], "end")
        self.nodes = nodes; self.chains = chains; self.mutable = mutable
        prev = {}; nxt = {}
        for r, ch in enumerate(chains):
            for p, q in zip(ch, ch[1:]):
                prev[q, r] = p; nxt[p, r] = q
                if check_literal and not leq(nodes[p][1], nodes[q][1]): raise ValueError(("frame violation on register", r, p, q))
        self.prev = prev; self.nxt = nxt
        allowed = set(mutable); lower = {}; upper = {}
        for k, (regs, F0, sec, idx) in enumerate(nodes):
            lower[k] = basis(tuple(x for r in regs for x in lower[prev[k, r]])) if k in allowed else F0
            if k in allowed:
                for r in regs:
                    j = nxt.get((k, r))
                    if j is None: continue
                    if (cut_equality and sec == "A" and nodes[j][2] == "cut") or (nodes[j][2] == "end" and r in eq_end):
                        lower[k] = basis(tuple(lower[k]) + tuple(nodes[j][1]))
            elif sec != "end":
                for r in regs:                                   # fixed vertex directly before an equality end
                    j = nxt.get((k, r))
                    if j is not None and nodes[j][2] == "end" and r in eq_end and span(F0) != span(nodes[j][1]):
                        raise Infeasible(("fixed vertex differs from its warp frame", k, sec, idx, r))
        for k in reversed(range(len(nodes))):
            regs, F0, sec, idx = nodes[k]
            if k in allowed:
                U = set(span(FULL9))
                for r in regs: U.intersection_update(span(upper[nxt[k, r]]))
                for r in regs:
                    if r in caps and nodes[nxt[k, r]][2] in ("tail", "end"): U.intersection_update(span(caps[r]))
                upper[k] = basis(tuple(U))
                if not leq(lower[k], upper[k]): raise Infeasible(("L not inside U at mutable vertex", k, sec, idx))
                if check_literal and not (leq(lower[k], F0) and leq(F0, upper[k])): raise ValueError(("literal frame outside [L,U]", k, sec, idx))
            else:
                upper[k] = F0
                if not leq(lower[k], F0): raise Infeasible(("fixed vertex below its forced lower frame", k, sec, idx))
                for r in regs:
                    if (k, r) in nxt and not leq(F0, upper[nxt[k, r]]): raise Infeasible(("fixed vertex above its successor cap", k, sec, idx))
        self.lower = lower; self.upper = upper
        if not check_literal:
            nodes = [((regs, lower[k], sec, idx) if (k in allowed and lower[k] == upper[k]) else (regs, F0, sec, idx)) for k, (regs, F0, sec, idx) in enumerate(nodes)]
            self.nodes = nodes
        self.var = [k for k in mutable if lower[k] != upper[k]]; self.varset = set(self.var)
        self.dom = {k: self._domain(k) for k in self.var}
        self.didx = {k: {Fr: i for i, Fr in enumerate(d)} for k, d in self.dom.items()}
        adj = collections.defaultdict(set)
        for (k, r), j in prev.items():
            if k in self.varset and j in self.varset: adj[k].add(j); adj[j].add(k)
        self.adj = adj
        comps = []; remaining = set(self.var)
        while remaining:
            root = min(remaining); stack = [root]; remaining.remove(root); comp = []
            while stack:
                k = stack.pop(); comp.append(k)
                for j in adj[k] & remaining: remaining.remove(j); stack.append(j)
            comps.append(sorted(comp))
        self.components = sorted(comps, key=lambda z: (-len(z), min(z)))


_COSTS = {}
def costs(b=B_DEFAULT):
    if b not in _COSTS: _COSTS[b] = F.Costs(b)
    return _COSTS[b]


def frame_profile(w, b=B_DEFAULT, literal=False, interval=False):
    """certified optimal frames for the word's gate order (literal=True: also validate the stored frames)."""
    t0 = time.monotonic(); w2, meta = build_problem(w)
    g = BorrowGraph(w2, meta['eq_end'], check_literal=literal, tail_mutable=True, cut_equality=True)
    r = F.optimal_frames(w2, costs(b), check_literal=literal, graph=g, interval=interval)
    cd = centre_descents(w); prof = collections.Counter(r['profile']); prof.update(cd)
    out = dict(profile=dict(sorted(prof.items())), cost=r['cost'] + costs(b).profile_cost(cd), certified=r['certified'],
               graph=g, assign=r['assign'], meta=meta, w2=w2, seconds=round(time.monotonic() - t0, 2))
    if literal:
        lp = collections.Counter(r['literal_profile']); lp.update(cd)
        out['literal_profile'] = dict(sorted(lp.items())); out['literal_cost'] = r['literal_cost'] + costs(b).profile_cost(cd)
    if interval: out['interval'] = r['interval']
    return out


def write_frames(w, pf):
    """copy of w with the optimal frames written into A/B/restore gates and report.local_profile updated"""
    w1 = copy.deepcopy(w); g = pf['graph']; A_idx = pf['meta']['A_idx']
    for k, (regs, F0, sec, idx) in enumerate(g.nodes):
        if sec not in ('A', 'B', 'tail'): continue
        Fr = pf['assign'].get(k, F0)
        if sec == 'A': w1['A'][A_idx[idx]][-1] = list(Fr)
        elif sec == 'B': w1['B'][idx][-1] = list(Fr)
        else: w1['restore'][idx][-1] = list(Fr)
    w1['report'] = dict(w1['report']); w1['report']['local_profile'] = {str(k): v for k, v in pf['profile'].items()}
    return w1


def edit_B(w, delete=(), insert=()):
    """gate-level edit of the B section. delete: B indices of w; insert: (i, gate) = place gate immediately before old B[i]
    (after the warps at position i; i = len(B) appends). Warp positions shift accordingly; frames of inserted gates are
    placeholders (solve with frame_profile); the inverse-reverse cleanup is re-derived."""
    restored = word_patch.restored_of(w); dele = set(delete); ins = collections.defaultdict(list)
    for i, g in insert: ins[i].append(list(g[:5]) + [list(FULL9)] if len(g) == 5 else list(g))
    newB = []; newpos = {}
    for i in range(len(w['B']) + 1):
        newpos[i] = len(newB)                            # warps at old position i stay before the gates inserted at i
        newB += ins.get(i, [])
        if i < len(w['B']) and i not in dele: newB.append(list(w['B'][i]))
    w1 = copy.deepcopy(w); w1['B'] = newB
    w1['warps'] = [[newpos[rec[0]]] + rec[1:] for rec in w['warps']]
    w1['cleanup'] = derive_cleanup(w1, restored)
    return w1


def derive_cleanup(w, restored=None):
    """inverse-reverse cleanup at FULL as the package derives it: the A-phase prelude is excluded (apply_lowfour)"""
    if restored is None: restored = word_patch.restored_of(w)
    t = copy.deepcopy(w); t['A'] = w['A'][w.get('prelude_events', 0):]
    return word_patch.derive_cleanup(t, restored)


def apply_patch(w, kind, patch):
    return {'kernel': word_patch.apply_kernel, 'handoff': word_patch.apply_handoff, 'lowfour': word_patch.apply_lowfour}[kind](w, patch)


def audit(w, timeout=120):
    """the package's unchanged auditor (BORROW-WORD branch) in a subprocess with a timeout and a 6 GiB RSS cap"""
    with tempfile.TemporaryDirectory() as d:
        wp = Path(d) / 'w.json.gz'; rp = Path(d) / 'r.json'; dump(w, wp)
        def lim():
            try: resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))
            except Exception: pass
        try:
            p = subprocess.run([sys.executable, '-B', str(AUDITOR), '--word', str(wp), '--output', str(rp)], capture_output=True,
                               text=True, timeout=timeout, preexec_fn=lim)
        except subprocess.TimeoutExpired:
            return dict(rc=-1, status='TIMEOUT')
        rec = json.loads(rp.read_text()) if rp.exists() else None
        tail = (p.stdout + p.stderr).strip().splitlines()[-1:] if p.returncode else []
        return dict(rc=p.returncode, status=(rec or {}).get('status', 'FAIL'), error=tail, receipt=rec)


def native(w, timeout=900):
    """the package's native borrow chain (new/run_native_borrow.py: transport -> emit -> local replay -> wrappers -> phases +
    warp-recipe recheck) on a written-back word, in a temporary work dir, with a timeout and a 6 GiB address-space cap"""
    with tempfile.TemporaryDirectory() as d:
        wp = Path(d) / 'w.json.gz'; dump(w, wp)
        def lim():
            try: resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))
            except Exception: pass
        t0 = time.monotonic()
        try:
            p = subprocess.run([sys.executable, '-B', str(PKG / 'new/run_native_borrow.py'), str(wp), str(Path(d) / 'work')],
                               capture_output=True, text=True, timeout=timeout, preexec_fn=lim)
        except subprocess.TimeoutExpired:
            return dict(rc=-1, status='TIMEOUT', seconds=timeout)
        steps = [l for l in p.stdout.splitlines() if l.startswith('PASS ')]
        return dict(rc=p.returncode, status='PASS_NATIVE_BORROW' if p.returncode == 0 else 'FAIL', steps=steps,
                    error=(p.stdout + p.stderr).strip().splitlines()[-3:] if p.returncode else [], seconds=round(time.monotonic() - t0, 1))


_BASE = {}
def price(w0, w1, b=B_DEFAULT, do_audit=True, key=None):
    """exact frames of w0 (cached by key) and w1, delta = cost(w1) - cost(w0) at b, write-back + auditor on w1"""
    t0 = time.monotonic()
    k0 = key or id(w0)
    if (k0, b) not in _BASE: _BASE[k0, b] = frame_profile(w0, b)
    p0 = _BASE[k0, b]
    try: p1 = frame_profile(w1, b)
    except Infeasible as ex: return dict(status='infeasible', why=str(ex)[:200], seconds=round(time.monotonic() - t0, 2))
    out = dict(status='ok' if p1['certified'] else 'uncertified', delta=p1['cost'] - p0['cost'], profile=p1['profile'],
               base_profile=p0['profile'], cost=p1['cost'])
    if do_audit:
        a = audit(write_frames(w1, p1)); out['audit'] = a['status']; out['audit_error'] = a.get('error')
    out['seconds'] = round(time.monotonic() - t0, 2)
    return out


if __name__ == '__main__':
    w = load(sys.argv[1]); pf = frame_profile(w, literal=True)
    print(json.dumps(dict(profile=pf['profile'], literal_profile=pf['literal_profile'], cost=pf['cost'], literal_cost=pf['literal_cost'],
                          certified=pf['certified'], virtual=pf['meta']['virtual'], seconds=pf['seconds'])))
