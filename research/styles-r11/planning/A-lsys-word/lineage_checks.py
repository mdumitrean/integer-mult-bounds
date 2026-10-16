#!/usr/bin/env python3
"""Lane A follow-ups: climb-vocabulary stability across lineage words, named-lag periodicities, gate-level lineage diff."""
import sys, collections, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract_strings as X, measures as M
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
I = str(_ROOT / "research/t74-joint-twelve-retired7/inputs") + "/"
names = {"2802b": "WORD-base.json.gz", "2802x": "WORD-extra.json.gz", "2751b": "WORD2751-base.json.gz", "2462b": "POSITIVE2462-base.json.gz"}
W = {k: X.load(I + v) for k, v in names.items()}
E = {k: X.extract(w) for k, w in W.items()}
def jstr(ex): return {r: tuple(d for s, d in ex["jumps"].get(r, [])) for r in range(ex["n"])}
J = {k: jstr(ex) for k, ex in E.items()}
vocab = {k: set(s for s in js.values() if s) for k, js in J.items()}
print("climb vocabulary sizes:", {k: len(v) for k, v in vocab.items()})
print("2802b vocab also in 2751b:", len(vocab["2802b"] & vocab["2751b"]), " in 2462b:", len(vocab["2802b"] & vocab["2462b"]), " in all three:", len(vocab["2802b"] & vocab["2751b"] & vocab["2462b"]))
for a, b in (("2802b", "2802x"), ("2802b", "2751b"), ("2751b", "2462b"), ("2802b", "2462b")):
    same = sum(1 for r in range(704) if J[a][r] == J[b][r]); diff = [r for r in range(704) if J[a][r] != J[b][r]]
    print(f"registers with identical jump string {a} vs {b}: {same}/704; differing registers (first 24): {diff[:24]}")
# named lags on the mid alphabet, sections A and B
for k in ("2802b", "2751b", "2462b"):
    ex = E[k]
    for sec in ("A", "B"):
        idx = [i for i, s in enumerate(ex["sections"]) if s == sec]
        toks = X.coarse([ex["tokens"][i] for i in idx], "mid")
        base = sum((c / len(toks)) ** 2 for c in collections.Counter(toks).values())
        lm = M.lag_match(toks, [1, 2, 3, 4, 6, 8, 9, 12, 16, 18, 22, 24, 48, 73, 88, 112, 176, 224])
        print(f"{k} {sec} lag-match base={base:.3f} " + " ".join(f"L{L}:{v:.3f}" for L, v in lm.items()))
# gate-level lineage diff 2751b -> 2802b per section (positions where the gate differs, registers involved)
for a, b in (("2751b", "2802b"), ("2462b", "2751b")):
    wa, wb = W[a], W[b]
    for sec in ("A", "cut", "B", "precondition", "cleanup", "compensation", "restore"):
        ga, gb = wa[sec], wb[sec]
        if len(ga) == len(gb):
            d = [i for i in range(len(ga)) if ga[i] != gb[i]]
            fr = [i for i in d if ga[i][:-1] == gb[i][:-1]]   # frame-only differences
            print(f"{a}->{b} {sec}: len {len(ga)} == {len(gb)}, differing gates {len(d)}, of which frame-only {len(fr)}; first positions {d[:12]}")
        else:
            ca = collections.Counter(json.dumps(g) for g in ga); cb = collections.Counter(json.dumps(g) for g in gb)
            print(f"{a}->{b} {sec}: len {len(ga)} -> {len(gb)}; gates only in {a}: {sum((ca - cb).values())}, only in {b}: {sum((cb - ca).values())}")
    print(f"{a}->{b} warps {len(wa['warps'])} -> {len(wb['warps'])}; removed {len(wa.get('removed', []))} -> {len(wb.get('removed', []))}; start_extra {len(wa['start_extra'])} -> {len(wb['start_extra'])}; helper_final {len(wa['helper_final'])} -> {len(wb['helper_final'])}")
# climb-string vocabulary listing for 2802b (all 56) with counts and roles
ex = E["2802b"]; cnt = collections.Counter(); roles = collections.defaultdict(collections.Counter)
for r, s in J["2802b"].items():
    if s: cnt[s] += 1; roles[s][ex["role"](r)] += 1
print("2802b climb vocabulary (jump string: count {roles}):")
for s, c in cnt.most_common(): print("  ", "".join(map(str, s)), c, dict(roles[s]))
