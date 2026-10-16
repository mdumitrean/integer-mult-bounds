"""Lane D grounding: cost of LZ76 complexity and a plain Re-Pair pass on the #2802 gate token string, against one
section-preserving shuffle (the null model of CONTROLS.md).  Alphabet = (section, op, coefficient class, rank).  Run with -I."""
import gzip, json, time, random, collections
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
w = json.load(gzip.open(str(_ROOT / "research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz")))
def tok(sec, e):
    if e[0] == "add": c = (e[3], e[4]); f = e[5]
    elif e[0] == "scale": c = (e[2], e[3]); f = e[4]
    else: return (sec, "warp", None, None)
    return (sec, e[0], c, len(f) if isinstance(f, list) else 0)
import sys
secs = ("A", "cut", "B") if "--forward-only" in sys.argv else ("precondition", "compensation", "A", "cut", "B", "restore", "cleanup")
string = [tok(s, e) for s in secs for e in w[s]]
alpha = sorted(set(string)); idx = {a: i for i, a in enumerate(alpha)}
seq = [idx[t] for t in string]
print("tokens", len(seq), "alphabet", len(alpha))
def lz76(s):
    i, c, n = 0, 0, len(s)
    while i < n:
        l = 1
        while i + l <= n and any(s[j:j + l] == s[i:i + l] for j in range(0, i)) : l += 1
        c += 1; i += l
    return c
def lz76_fast(s):
    # standard Kaspar-Schuster LZ76 complexity (O(n^2) worst case, fast in practice)
    n = len(s); i, k, l, c, k_max = 0, 1, 1, 1, 1
    while True:
        if s[i + k - 1] == s[l + k - 1]:
            k += 1
            if l + k > n: c += 1; break
        else:
            k_max = max(k, k_max); i += 1
            if i == l:
                c += 1; l += k_max
                if l + 1 > n: break
                i, k, k_max = 0, 1, 1
            else: k = 1
    return c
def repair(s, max_rules=100000):
    s = list(s); rules = 0; nxt = max(s) + 1
    while rules < max_rules:
        pairs = collections.Counter(zip(s, s[1:]))
        if not pairs: break
        (a, b), f = pairs.most_common(1)[0]
        if f < 2: break
        out = []; i = 0
        while i < len(s):
            if i + 1 < len(s) and s[i] == a and s[i + 1] == b: out.append(nxt); i += 2
            else: out.append(s[i]); i += 1
        s = out; nxt += 1; rules += 1
    return rules, len(s)
def shuffled(seed):
    rng = random.Random(seed); out = []
    for sname in secs:
        part = [idx[tok(sname, e)] for e in w[sname]]; rng.shuffle(part); out += part
    return out
for name, s in (("real", seq), ("section-shuffle", shuffled(1))):
    t = time.time(); c = lz76_fast(s); t1 = time.time() - t
    t = time.time(); r, L = repair(s); t2 = time.time() - t
    print(f"{name}: LZ76 c={c} ({t1:.2f}s) | Re-Pair rules={r} final length={L} ({t2:.2f}s) | grammar size ~ {2*r + L}")
