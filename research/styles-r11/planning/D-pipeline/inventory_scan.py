"""Lane D grounding scan: sizes of every lineage word we hold (sections, ops, ranks, registers, warps) and the
#2802 fill/plan/dispatch/template shapes.  Read-only; run with -I.  usage: python -I inventory_scan.py"""
import gzip, json, time, sys, collections, os
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
P = str(_ROOT / "research/t74-joint-twelve-retired7/inputs")
WORDS = {
 "#2802 base": P + "/WORD-base.json.gz",
 "#2802 extra": P + "/WORD-extra.json.gz",
 "#2751 base": P + "/WORD2751-base.json.gz",
 "#2745 base": str(_ROOT / "research/styles-r11/data/words/2745-BORROW-WORD-43base.json.gz"),
 "#1672 gauge44-566": str(_ROOT / "research/styles-r11/data/words/1672-gauge44-word-566-554.json.gz"),
 "#1094 k8 seven-slot": str(_ROOT / "research/styles-r11/data/words/1094-K8S7-FULL-WORD.json.gz"),
}
def load(p):
    t = time.time(); w = json.load(gzip.open(p)); return w, time.time() - t
def sec_stats(w):
    out = {}
    for sec in ("precondition", "compensation", "A", "cut", "B", "cleanup", "restore", "initial_corrections", "warps"):
        if sec in w and isinstance(w[sec], list):
            out[sec] = len(w[sec])
    return out
def rank_hist(gates):
    h = collections.Counter()
    for e in gates:
        if isinstance(e, list) and e and e[0] in ("add", "scale"):
            f = e[-1]; h[len(f) if isinstance(f, list) else 0] += 1
    return dict(sorted(h.items()))
def op_hist(gates):
    return dict(collections.Counter(e[0] for e in gates if isinstance(e, list) and e))
def coef_classes(gates):
    c = collections.Counter()
    for e in gates:
        if not (isinstance(e, list) and e): continue
        if e[0] == "add": num, den = e[3], e[4]
        elif e[0] == "scale": num, den = e[2], e[3]
        else: continue
        c[(num, den)] += 1
    return len(c), c.most_common(6)
def regs_touched(gates):
    s = set()
    for e in gates:
        if isinstance(e, list) and e and e[0] == "add": s.update((e[1], e[2]))
        elif isinstance(e, list) and e and e[0] == "scale": s.add(e[1])
    return len(s)
for name, p in WORDS.items():
    if not os.path.exists(p): print(name, "MISSING", p); continue
    w, dt = load(p)
    print(f"\n=== {name}  ({os.path.getsize(p)} bytes gz, load {dt:.2f}s)")
    print(" keys:", sorted(w.keys()))
    rep = w.get("report", {})
    print(" report:", {k: rep[k] for k in rep if k in ("R", "h", "v", "local_profile", "width_inventory")})
    st = sec_stats(w); print(" sections:", st, "| forward gates A+cut+B:", st.get("A", 0) + st.get("cut", 0) + st.get("B", 0), "| all gates:", sum(v for k, v in st.items() if k != "warps"))
    for sec in ("A", "B", "cleanup", "compensation"):
        if sec in w and isinstance(w[sec], list) and w[sec] and isinstance(w[sec][0], list):
            n_c, top = coef_classes(w[sec])
            print(f"  {sec}: ops {op_hist(w[sec])} ranks {rank_hist(w[sec])} regs {regs_touched(w[sec])} coef-classes {n_c} top {top[:4]}")
    for k in ("centers", "ports", "helper_final", "start_extra", "removed", "early_cleanup", "target_levels", "center_frames"):
        if k in w: print(f"  {k}: len {len(w[k])}")
    if "warps" in w and w["warps"]:
        dims = collections.Counter(len(r[3]) for r in w["warps"] if isinstance(r, list) and len(r) >= 5)
        print("  warps:", len(w["warps"]), "lender-frame dims", dict(sorted(dims.items())), "example", w["warps"][0] if isinstance(w["warps"][0], list) else type(w["warps"][0]))
# ---------------- fill / plan / dispatch / template
print("\n=== #2802 global objects")
for f in ("FILL.json.gz", "PLAN.json.gz", "DISPATCH.json.gz", "GLOBAL-TEMPLATE.json.gz"):
    t = time.time(); d = json.load(gzip.open(P + "/" + f)); dt = time.time() - t
    print(f"\n--- {f}: {os.path.getsize(P + '/' + f)} bytes gz, load {dt:.2f}s, type {type(d).__name__}")
    if isinstance(d, dict):
        for k, v in d.items():
            if isinstance(v, list): print(f"  {k}: list[{len(v)}] first={str(v[0])[:160] if v else ''}")
            elif isinstance(v, dict): print(f"  {k}: dict[{len(v)}] keys={list(v)[:8]}")
            else: print(f"  {k}: {str(v)[:120]}")
    elif isinstance(d, list):
        print(f"  list[{len(d)}] first={str(d[0])[:200]}")
        if d and isinstance(d[0], list):
            print("  row lengths:", collections.Counter(len(r) for r in d).most_common(3))
            cols = list(zip(*d[:200000]))
            for i, c in enumerate(cols[:8]):
                try: print(f"  col{i}: min {min(c)} max {max(c)} distinct {len(set(c))}")
                except TypeError: print(f"  col{i}: non-numeric sample {c[:3]}")
