#!/usr/bin/env python3
"""Lane A (r11 styles): extract candidate strings from a BORROW-WORD and measure structure vs nulls.

usage: python -I extract_strings.py WORD.json.gz [more words...] [--reps 20] [--out OUT.json]

Strings extracted (all exact functions of the word; nothing heuristic except the alphabet choice):
  G_full : one token per gate of A|cut|B|precondition|cleanup|compensation|restore,
           token = (section, op, coefficient class, role(target), role(source), frame rank, climb(target), climb(source))
  G_mid  : (section, op, coefficient class, frame rank)
  G_rank : (section, frame rank)
  G_op   : (section, op, coefficient class)
  CLIMB  : per register, the frame-dimension sequence along its event chain (start, A events, cut, B events, end);
           JUMPS = the positive deltas (these are exactly the paid children: histogram == report.local_profile)
Roles: P port (r<V), T target row (V<=r<2V), C centre, H helper (r>=2V), L lender register before its B warp,
       F the same register after the warp (hosting a follower), X removed/aliased helper register.
Climb accounting reproduces the PR2679 auditor (vendor/audit_local_pr2679.py, step 4): climbs on add/scale gate frames
in A, B and restore, the centre scatter descents at the cut, warps = frame replacement (no pay) applied before B gate
rec[0] (prelude warps in A likewise), the end climb to FULL (ports, helpers) / helper_final (cold ends) / perp(port)
(targets); removed (aliased) registers have no chain.
Nulls: N1 section-preserving token shuffle; N2 random linear extension of the per-register order (dataflow-preserving).
"""
import sys, gzip, json, random, time, collections, math, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import measures as M

V = 112; FULL = (256, 128, 64, 32, 16, 8, 4, 2, 1)

def basis(vs):
    """reduced echelon basis of a set of F2^9 bitmask vectors, as a sorted-descending tuple (canonical)."""
    rows = []
    for v in vs:
        for r in rows:
            if v & (1 << (r.bit_length() - 1)): v ^= r
        if v:
            # reduce existing rows by v
            hb = 1 << (v.bit_length() - 1)
            rows = [r ^ v if r & hb else r for r in rows]
            rows.append(v)
    return tuple(sorted(rows, reverse=True))

def perp(x): return basis([z for z in range(1, 512) if not bin(x & z).count("1") % 2])

def coef_class(e):
    if e[0] == "add": num, den = e[3], e[4]
    elif e[0] == "scale": num, den = e[2], e[3]
    else: return "w"
    if not isinstance(num, int) or not isinstance(den, int): return "other"
    s = "+" if num * den > 0 else "-"
    a = abs(num) if abs(den) == 1 else (f"{abs(num)}/{abs(den)}" if abs(num) != 1 else f"1/{abs(den)}")
    return s + str(a)

def load(path):
    w = json.load(gzip.open(path) if str(path).endswith(".gz") else open(path))
    assert w.get("kind") == "BORROW-WORD" or "A" in w
    return w

def extract(w):
    R = w["report"]["R"]; n = 2 * V + R; P = w["ports"]
    start = {}
    for r in range(n):
        if r < V: start[r] = basis([P[r]])
        elif r >= 2 * V: start[r] = basis(w.get("start_extra", {}).get(str(r), []))
        else: start[r] = ()
    cur = dict(start)
    centres = set(w["centers"]); removed = set(w.get("removed", []))
    warp_regs = {rec[1] for rec in w["warps"]}
    warped = set()
    def role(r):
        if r in removed: return "X"
        if r in centres: return "C"
        if r < V: return "P"
        if r < 2 * V: return "T"
        if r in warp_regs: return "F" if r in warped else "L"
        return "H"
    lev = {int(t): basis(E) for t, E in w.get("target_levels", {}).items()}
    paid = collections.Counter()
    climb_seq = collections.defaultdict(list)      # register -> [(section, dim)]
    jumps = collections.defaultdict(list)          # register -> [(section, delta)]
    for r in range(n): climb_seq[r].append(("s", len(start[r])))
    tokens = []       # (gate string tokens, full alphabet)
    gate_regs = []    # registers touched by each token (for the dataflow null)
    sections = []     # section id per token
    def climb(r, F, sec):
        F = basis(F); o = cur[r]
        assert basis(list(o) + list(F)) == F, ("frame violation", sec, r, o, F)
        d = len(F) - len(o)
        if d:
            paid[d] += 1; cur[r] = F; jumps[r].append((sec, d))
        climb_seq[r].append((sec, len(F)))
        return d
    byposition = collections.defaultdict(list)
    for rec in w["warps"]: byposition[rec[0]].append(rec)
    def emit(sec, e, dt, ds, regs):
        if e[0] == "warp":
            tok = (sec, "warp", "w", role(e[1]), "-", len(basis(e[-1])) if e[-1] else 0, 0, 0)
        else:
            frame = e[-1] or ()
            rt = role(e[1]); rs = role(e[2]) if e[0] == "add" else "-"
            tok = (sec, e[0], coef_class(e), rt, rs, len(basis(frame)), dt, ds)
        tokens.append(tok); gate_regs.append(tuple(regs)); sections.append(sec)
    for sec in ("A", "cut", "B", "precondition", "cleanup", "compensation", "restore"):
        if sec == "B":
            # centre scatter descents (paid) and target levels, as in gk_word.profile
            for r, f in zip(w["centers"], w["center_frames"]):
                assert cur[r] == basis(f), ("centre frame", r)
                served = sorted({lev.get(e[1] - V, ()) for e in w["cut"] if e[2] == r}, key=lambda E: -len(E))
                o = basis(f)
                for Lv in served:
                    if Lv != o:
                        paid[len(o) - len(Lv)] += 1; jumps[r].append(("cut", len(o) - len(Lv))); o = Lv
                        climb_seq[r].append(("cut", len(o)))
            for t in range(V):
                assert cur[V + t] == lev.get(t, ()), ("target level", t)
        for i, e in enumerate(w[sec]):
            if sec == "B":
                for rec in byposition.get(i, []):
                    pos, lender, G, U, E = rec
                    assert cur[lender] == basis(U), ("warp frame mismatch", rec)
                    cur[lender] = basis(E); warped.add(lender)
                    climb_seq[lender].append(("w", len(basis(E))))
                    tokens.append(("B", "WARP", "w", "L>F", "-", len(basis(E)), 0, 0)); gate_regs.append((lender,)); sections.append("B")
            if e[0] == "warp":
                if sec == "A":
                    r_, op_, fr_, to_ = e[1], e[2], e[3], e[4]
                    assert cur[r_] == basis(fr_), ("prelude warp frame mismatch", e)
                    cur[r_] = basis(to_); climb_seq[r_].append(("A", len(basis(to_))))
                emit(sec, e, 0, 0, (e[1],))
                continue
            regs = [e[1]] + ([e[2]] if e[0] == "add" else [])
            if sec in ("A", "B", "restore"):          # restore gates are climbed (paid) after B, as in the auditor
                dt = climb(e[1], e[-1], sec); ds = climb(e[2], e[-1], sec) if e[0] == "add" else 0
            else:
                dt = ds = 0
            emit(sec, e, dt, ds, regs)
    hf = {int(k): basis(v) for k, v in w.get("helper_final", {}).items()}
    for r in range(n):
        if r in removed: continue                      # aliased helpers: no chain, no end climb
        F = hf.get(r, FULL) if r >= 2 * V else (FULL if r < V else perp(P[r - V]))   # cold ends from helper_final
        climb(r, F, "e")
    return dict(n=n, paid=dict(paid), tokens=tokens, gate_regs=gate_regs, sections=sections,
                climb_seq=dict(climb_seq), jumps=dict(jumps), start=start, role=role)

def coarse(tokens, kind):
    if kind == "full": return tokens
    if kind == "mid": return [(t[0], t[1], t[2], t[5]) for t in tokens]
    if kind == "rank": return [(t[0], t[5]) for t in tokens]
    if kind == "op": return [(t[0], t[1], t[2]) for t in tokens]
    raise ValueError(kind)

def measure(tokens):
    out = {"n": len(tokens), "alphabet": len(set(tokens)), "lz76": M.lz76(tokens), "lz78": M.lz78(tokens)}
    gs, nr, fl = M.repair_size(tokens); out["repair"] = gs; out["repair_rules"] = nr; out["repair_final"] = fl
    h1 = M.block_entropy(tokens, 1); h2 = M.block_entropy(tokens, 2); h3 = M.block_entropy(tokens, 3)
    out["H1"] = h1; out["h2"] = h2 - h1; out["h3"] = h3 - h2
    return out

def blocks_of(tokens, sections):
    blocks = []; cur = None
    for t, s in zip(tokens, sections):
        if s != cur: blocks.append([]); cur = s
        blocks[-1].append(t)
    return blocks

def null_runs(ex, kind, reps, rng, which):
    toks = coarse(ex["tokens"], kind); secs = ex["sections"]
    res = []
    if which == "N1":
        blocks = blocks_of(toks, secs)
        for _ in range(reps): res.append(measure(M.shuffle_blocks(blocks, rng)))
    elif which == "N2":
        # random linear extension inside each section (gates keep their registers; per-register order preserved)
        idx_by_sec = collections.defaultdict(list)
        for i, s in enumerate(secs): idx_by_sec[s].append(i)
        order_secs = []
        for s in secs:
            if not order_secs or order_secs[-1] != s: order_secs.append(s)
        for _ in range(reps):
            seq = []
            for s in order_secs:
                idx = idx_by_sec[s]
                perm = M.random_linear_extension(idx, lambda j: ex["gate_regs"][idx[j]], rng)
                seq.extend(toks[idx[j]] for j in perm)
            res.append(measure(seq))
    return res

def motif_census(ex, section, k, topn=8):
    """register-renamed k-grams of gates in one section (registers numbered by first appearance in the k-gram)."""
    idx = [i for i, s in enumerate(ex["sections"]) if s == section]
    toks = ex["tokens"]; regs = ex["gate_regs"]
    grams = collections.Counter()
    for a in range(len(idx) - k + 1):
        ren = {}; g = []
        for j in idx[a:a + k]:
            t = toks[j]; rr = []
            for r in regs[j]:
                if r not in ren: ren[r] = len(ren)
                rr.append(ren[r])
            g.append((t[1], t[2], t[5], tuple(rr)))
        grams[tuple(g)] += 1
    total = sum(grams.values()); distinct = len(grams)
    rep = sum(c for c in grams.values() if c >= 2)
    return dict(k=k, total=total, distinct=distinct, repeated_mass=rep, top=[(c, g) for g, c in grams.most_common(topn)])

def climb_stats(ex):
    js = ex["jumps"]; n = ex["n"]
    strings = {r: tuple(d for s, d in js.get(r, [])) for r in range(n)}
    nonempty = {r: s for r, s in strings.items() if s}
    cnt = collections.Counter(nonempty.values())
    by_role = collections.defaultdict(collections.Counter)
    for r, s in nonempty.items(): by_role[ex["role"](r)][s] += 1
    return dict(registers=n, with_jumps=len(nonempty), distinct_jump_strings=len(cnt),
                top=cnt.most_common(12), by_role={k: (sum(v.values()), len(v), v.most_common(4)) for k, v in by_role.items()},
                mean_jumps=sum(len(s) for s in nonempty.values()) / max(1, len(nonempty)),
                mean_jump=sum(sum(s) for s in nonempty.values()) / max(1, sum(len(s) for s in nonempty.values())))

def climb_null(ex, reps, rng):
    """null for the jump strings: permute jump sizes across registers keeping each register's number of jumps
    (and section labels in place). Statistic: number of distinct jump strings, and entropy of the string distribution."""
    js = ex["jumps"]; n = ex["n"]
    lens = [len(js.get(r, [])) for r in range(n)]
    pool = [d for r in range(n) for s, d in js.get(r, [])]
    def stat(strings):
        cnt = collections.Counter(s for s in strings if s)
        tot = sum(cnt.values())
        H = -sum(c / tot * math.log2(c / tot) for c in cnt.values())
        return len(cnt), H
    real = stat([tuple(d for s, d in js.get(r, [])) for r in range(n)])
    nulls = []
    for _ in range(reps):
        p = list(pool); rng.shuffle(p); k = 0; strings = []
        for L in lens: strings.append(tuple(p[k:k + L])); k += L
        nulls.append(stat(strings))
    # within-register order null
    nulls2 = []
    for _ in range(reps):
        strings = []
        for r in range(n):
            s = [d for _, d in js.get(r, [])]; rng.shuffle(s); strings.append(tuple(s))
        nulls2.append(stat(strings))
    return dict(real=real, across=nulls, within=nulls2)

def cleanup_vs_forward(w, n):
    """is cleanup the reversed inverse of (a subsequence of) the forward A/B gates on buffered registers?"""
    fwd = [e for sec in ("A", "B") for e in w[sec] if e[0] != "warp"]
    def key(e, shift):
        if e[0] == "add": return ("add", e[1] % shift, e[2] % shift, e[3], e[4])
        return ("scale", e[1] % shift, e[2], e[3])
    def inv(e):
        if e[0] == "add": return ("add", e[1], e[2], -e[3], e[4])
        return ("scale", e[1], e[3], e[2])
    fset = collections.Counter(key(e, 10 ** 9) for e in fwd)
    cl = [e for e in w["cleanup"] if e[0] != "warp"]
    hits = 0; pos = []
    fpos = {}
    for i, e in enumerate(fwd): fpos.setdefault(key(e, 10 ** 9), []).append(i)
    for j, e in enumerate(cl):
        k = key(e, n)   # reduce buffer registers r+n -> r
        ki = inv(k) if k[0] == "add" else ("scale", k[1], k[3], k[2])
        ki = (ki[0], ki[1], ki[2], ki[3], ki[4]) if k[0] == "add" else ki
        # scale inverse: num/den -> den/num ; stored as (scale, t, num, den)
        if ki in fpos: hits += 1; pos.append((j, fpos[ki][-1]))
    # Spearman-ish: fraction of consecutive cleanup hits whose forward positions are decreasing
    dec = sum(1 for (a, b), (c, d) in zip(pos, pos[1:]) if d < b)
    return dict(cleanup_gates=len(cl), inverse_in_forward=hits, consecutive_hits=len(pos) - 1, decreasing_pairs=dec)

def structure_checks(w, n):
    out = {}
    cut = w["cut"]
    per_centre = collections.Counter(e[2] for e in cut)
    out["cut_fanout_per_centre"] = dict(per_centre)
    out["cut_targets"] = len({e[1] for e in cut})
    comp = w["compensation"]
    pairs = [(e[2], e[1]) for e in comp]
    out["comp_sorted_by_source_then_target"] = pairs == sorted(pairs)
    out["comp_sorted_by_target_then_source"] = [(b, a) for a, b in pairs] == sorted((b, a) for a, b in pairs)
    # runs of equal source
    runs = 1 + sum(1 for a, b in zip(pairs, pairs[1:]) if a[0] != b[0])
    out["comp_source_runs"] = runs; out["comp_distinct_sources"] = len({p[0] for p in pairs}); out["comp_distinct_targets"] = len({p[1] for p in pairs})
    pre = w["precondition"]
    out["precondition_pattern"] = collections.Counter((e[0], coef_class(e)) for e in pre).most_common()
    out["cleanup_vs_forward"] = cleanup_vs_forward(w, n)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("words", nargs="+"); ap.add_argument("--reps", type=int, default=20); ap.add_argument("--out", default=None)
    ap.add_argument("--kinds", default="full,mid,rank,op"); ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = random.Random(a.seed); report = {}
    for path in a.words:
        t0 = time.time(); w = load(path); ex = extract(w)
        name = Path(path).name; rep = {"path": path}
        prof = {int(k): v for k, v in w["report"]["local_profile"].items()}
        rep["paid"] = ex["paid"]; rep["report_profile"] = prof; rep["profile_match"] = (ex["paid"] == prof)
        print(f"== {name}: n_regs={ex['n']} tokens={len(ex['tokens'])} paid={ex['paid']} match_report={rep['profile_match']}", flush=True)
        rep["climb"] = climb_stats(ex); print("  climb:", {k: v for k, v in rep["climb"].items() if k != "by_role"}, flush=True)
        print("  climb by role:", rep["climb"]["by_role"], flush=True)
        rep["climb_null"] = climb_null(ex, a.reps, rng)
        cn = rep["climb_null"]
        print("  climb null (distinct strings, entropy): real", cn["real"], "across-reg null mean", tuple(sum(x[i] for x in cn["across"]) / len(cn["across"]) for i in range(2)),
              "within-reg null mean", tuple(sum(x[i] for x in cn["within"]) / len(cn["within"]) for i in range(2)), flush=True)
        rep["structure"] = structure_checks(w, ex["n"]); print("  structure:", rep["structure"], flush=True)
        rep["measures"] = {}
        for kind in a.kinds.split(","):
            toks = coarse(ex["tokens"], kind)
            real = measure(toks)
            n1 = null_runs(ex, kind, a.reps, rng, "N1"); n2 = null_runs(ex, kind, a.reps, rng, "N2")
            row = {"real": real}
            for lab, nl in (("N1", n1), ("N2", n2)):
                row[lab] = {}
                for stat in ("lz76", "lz78", "repair", "H1", "h2", "h3"):
                    m, sd, z = M.zstats(real[stat], [x[stat] for x in nl]); row[lab][stat] = (m, sd, z)
            rep["measures"][kind] = row
            print(f"  [{kind}] n={real['n']} |alpha|={real['alphabet']} lz76={real['lz76']} repair={real['repair']} H1={real['H1']:.3f} h2={real['h2']:.3f} h3={real['h3']:.3f}")
            for lab in ("N1", "N2"):
                print("     ", lab, " ".join(f"{s}:{row[lab][s][0]:.1f}±{row[lab][s][1]:.1f}(z={row[lab][s][2]:+.1f})" for s in ("lz76", "repair", "h2", "h3")), flush=True)
        # per-section measures (full alphabet) with N1 only
        rep["per_section"] = {}
        for sec in ("A", "B", "cleanup", "compensation"):
            idx = [i for i, s in enumerate(ex["sections"]) if s == sec]
            toks = [ex["tokens"][i] for i in idx]
            real = measure(toks); nl = [measure(rng.sample(toks, len(toks))) for _ in range(a.reps)]
            rep["per_section"][sec] = {"real": real, "N1": {s: M.zstats(real[s], [x[s] for x in nl]) for s in ("lz76", "repair", "h2")}}
            print(f"  section {sec}: n={real['n']} |alpha|={real['alphabet']} lz76={real['lz76']} (null {rep['per_section'][sec]['N1']['lz76'][0]:.0f}, z={rep['per_section'][sec]['N1']['lz76'][2]:+.1f}) repair={real['repair']} (null {rep['per_section'][sec]['N1']['repair'][0]:.0f}, z={rep['per_section'][sec]['N1']['repair'][2]:+.1f})", flush=True)
        # motif census (register-renamed) in A and B
        rep["motifs"] = {}
        for sec in ("A", "B"):
            for k in (2, 3, 4, 6):
                mc = motif_census(ex, sec, k); rep["motifs"][f"{sec}_{k}"] = mc
                print(f"  motifs {sec} k={k}: distinct={mc['distinct']}/{mc['total']} repeated_mass={mc['repeated_mass']} top={mc['top'][:3]}", flush=True)
        # periodicity probe on the mid alphabet in B
        idxB = [i for i, s in enumerate(ex["sections"]) if s == "B"]
        toksB = coarse([ex["tokens"][i] for i in idxB], "mid")
        lags = list(range(1, 130))
        lm = M.lag_match(toksB, lags); base = sum((c / len(toksB)) ** 2 for c in collections.Counter(toksB).values())
        peaks = sorted(lags, key=lambda L: -lm[L])[:10]
        rep["lag_B_mid"] = {"base": base, "top_lags": [(L, round(lm[L], 3)) for L in peaks]}
        print("  B lag-match (mid alphabet): shuffle base", round(base, 3), "top lags", rep["lag_B_mid"]["top_lags"], flush=True)
        rep["seconds"] = round(time.time() - t0, 1); print("  seconds", rep["seconds"], flush=True)
        report[name] = rep
    if a.out:
        json.dump(report, open(a.out, "w"), indent=1, default=str)

if __name__ == "__main__":
    main()
