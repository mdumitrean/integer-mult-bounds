"""r10 F-lenders: augmenting-path edits on a BORROW-WORD.  Each spec 'op:L2:f' (op = 1-based B-warp index in the INPUT word):
(1) move the hostee of warp op off its lender L onto the retired free lender L2 (un-alias to a placeholder helper X with start
frame E, then the package's refit + alias_build.alias X <- L2), (2) alias the free follower f onto the now-retired L
(alias_build.alias f <- L).  Refits are eval1.apply_stack's minimal-change lower/raise.  Prints the local profile.
usage: python3 -I build_move.py CODE WORD_IN WORD_OUT SPEC [SPEC ...]"""
import sys, json, gzip, copy, os, tempfile
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, basis, regs
from refit import Refit
import alias_build as mk
W0 = json.load(gzip.open(sys.argv[2])); OUT = sys.argv[3]
specs = [tuple(map(int, s.split(':'))) for s in sys.argv[4:]]
def used_ids(w):
    s = set()
    for sec in ('precondition', 'compensation', 'A', 'cut', 'B', 'restore', 'cleanup'):
        for e in w[sec]:
            if e[0] == 'warp': s.add(e[1])
            else: s.update(regs(e))
    for c in w.get('initial_corrections', []): s.update((c['source'], c['target']))
    return s
def unalias(w, k, X):
    w = copy.deepcopy(w); pos, L, G, U, E = w['warps'][k]
    for sec, start in (('B', pos), ('restore', 0)):
        for i in range(start, len(w[sec])):
            e = w[sec][i]
            if e[0] == 'add':
                if e[1] == L: e[1] = X
                if e[2] == L: e[2] = X
            elif e[1] == L: e[1] = X
    del w['warps'][k]
    w['removed'] = [r for r in w['removed'] if r != X]
    w['start_extra'][str(X)] = list(E)
    t = copy.deepcopy(w); t['A'] = w['A'][w.get('prelude_events', 0):]
    w['cleanup'] = mk.word_patch.derive_cleanup(t, mk.word_patch.restored_of(w))
    return w, L
def dump(w, p): open(p, 'wb').write(gzip.compress(json.dumps(w, separators=(',', ':')).encode(), mtime=0))
w = copy.deepcopy(W0); tmp = tempfile.mkdtemp(prefix='fmove-', dir=os.path.dirname(OUT))
free_ids = sorted(set(W0['removed']) - used_ids(W0))
assert len(free_ids) >= len(specs), ('no placeholder ids', free_ids)
# resolve ops against the input word, then unalias in descending op order so indices stay valid
recs = [(k - 1, L2, f, W0['warps'][k - 1][1]) for k, L2, f in specs]
stack = []; slot = {}
for (k, L2, f, L), X in sorted(zip(recs, free_ids), key=lambda z: -z[0][0]):
    w, Lw = unalias(w, k, X); assert Lw == L
    stack.append((X, L2)); stack.append((f, L)); slot[X] = k
lp0, wi0 = mk.profile(w); w['report'] = dict(w['report'], local_profile=lp0, width_inventory=wi0)
stack = sorted([x for x in stack if x[0] in slot], key=lambda z: slot[z[0]]) + [x for x in stack if x[0] not in slot]
p1 = os.path.join(tmp, 'unaliased.json.gz'); dump(w, p1)
b = Bounds(p1); R = Refit(b)
log = []
for h, L in stack:
    gh = [x for x in b.byreg[h] if x[1] == 'gate'][0][0]
    gl = [x for x in b.byreg[L] if x[1] == 'gate'][-1][0]
    U = R.F(gl); F1 = R.F(gh)
    if len(U) > len(F1):
        X_ = b.lo[gl]
        r1 = R.lower(gl, X_) if len(X_) < len(U) else []
        assert not isinstance(r1, str), ('lower-fail', h, L, r1)
        U = R.F(gl); r2 = []
        if len(U) > len(F1):
            r2 = R.raise_(gh, b.hi[gh]); assert not isinstance(r2, str), ('raise-fail', h, L, r2)
            F1 = R.F(gh)
        assert len(U) <= len(F1), ('still-blocked', h, L)
        log.append((h, L, len(r1), len(r2)))
    else:
        log.append((h, L, 0, 0))
w = copy.deepcopy(b.Wd.w); recs_out = []
for h, L in stack:
    first = min(p for p, e in enumerate(w['B']) if e[0] != 'warp' and h in mk.registers(e))
    U = mk.frame_at_B(w, L, first); F1 = basis(w['B'][first][-1])
    if len(F1) == len(U): E = list(F1)
    else:
        S = basis(w['start_extra'][str(h)])
        E = list(S) if len(S) == len(U) else list(F1)[len(F1) - len(U):]
    nw = len(w['warps']); w, rec = mk.alias(w, h, L, E); recs_out.append(rec)
    if h in slot:   # moved hostee: put its warp back at the original op index so operator words keep their meaning
        k = slot[h]; rec_w = w['warps'].pop(); assert rec_w[1] == L and len(w['warps']) == nw; w['warps'].insert(k, rec_w)
        t = copy.deepcopy(w); t['A'] = w['A'][w.get('prelude_events', 0):]
        w['cleanup'] = mk.word_patch.derive_cleanup(t, mk.word_patch.restored_of(w))
lp, wi = mk.profile(w); w['report'] = dict(w['report'], local_profile=lp, width_inventory=wi)
dump(w, OUT)
print(json.dumps(dict(specs=specs, placeholders=free_ids[:len(specs)], unaliased_profile=lp0, refit_log=log, profile=lp, widths=wi,
                      aliases=[dict(h=r['h'], L=r['L'], pos=r['pos'], dimU=len(r['U'])) for r in recs_out])))
