"""Bounded reproduction of PR987's slot search (search2.py loop, unchanged evaluation) on the k8 ancestor word,
restricted to copy gates whose slot X is in a target set.  usage: slot_repro.py CODE_DIR WORD OUT_JSON X1 X2 ..."""
import sys, json, itertools, time
code, word, out = sys.argv[1], sys.argv[2], sys.argv[3]; targets = set(map(int, sys.argv[4:]))
sys.path.insert(0, code)
from slot import *          # noqa: E402,F401  (PR987's own module)
b = 0.001665; m = 73
f = lambda r: r * ((m / r) ** b - 1)
fee = lambda P: sum(f(int(k)) * v for k, v in P.items())
w = L(word); base = fee(profile(w)); B = w['B']
copies = [i for i, g in enumerate(B) if g[0] == 'add' and g[1] >= 224 and g[2] >= 224 and g[3] == 1 and g[4] == 1]
sel = []
for ci in copies:
    E, X, reads, pre = slot_info(w, ci)
    if X in targets: sel.append(ci)
res = []
t_all = time.time()
for ci in sel:
    E, X, reads, pre = slot_info(w, ci)
    rec = dict(ci=ci, E=E, X=X, reads=len(reads))
    if not reads or len(reads) > 5 or any(j > ci and B[j][1] in (X, E) for j in range(len(B))):
        rec['skipped'] = True; res.append(rec); continue
    orig = {i: s for (i, t, s, c) in reads}
    H = {i: holders(w, ci, i, {E, X}) for (i, t, s, c) in reads}
    ks = [i for (i, t, s, c) in reads]
    assigns = [dict(zip(ks, ss)) for ss in itertools.product((E, X), repeat=len(ks))] if len(ks) <= 4 else [orig]
    singles = [(i, h, j) for i in ks for (h, j) in H[i]]
    donopts = [[]] + [[s] for s in singles] + [[s1, s2] for s1, s2 in itertools.combinations(singles, 2) if s1[0] != s2[0] and s1[1] != s2[1]]
    best = None; n = 0; t0 = time.time()
    for dons in donopts:
        for a in assigns:
            if not dons and a == orig: continue
            try:
                w2 = build(w, ci, a, dons)
                if w2 is None: continue
                w3, info = optimise(w2)
                if w3 is None: continue
                P = profile(w3); r = (fee(P) - base) / b
            except Exception:
                continue
            n += 1
            if best is None or r < best[0]: best = (r, {str(k): v for k, v in a.items()}, dons, P)
    rec.update(evals=n, seconds=round(time.time() - t0, 1), best=None if best is None else dict(delta=best[0], assign=best[1], dons=best[2], profile=best[3]))
    res.append(rec); print(json.dumps(rec)[:300], flush=True)
    json.dump(dict(word=word, targets=sorted(targets), selected=sel, results=res, seconds=round(time.time() - t_all, 1)), open(out, 'w'), indent=1, default=str)
