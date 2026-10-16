"""Cheap string-structure measures for Lane A (L-system encoding of the local word).

All functions take a list of hashable tokens. No third-party dependencies.
  lz76(tokens)          Lempel-Ziv 1976 phrase count (Kaspar-Schuster exhaustive-history parse), C-speed via str.find
  lz78(tokens)          LZ78 phrase count
  repair_size(tokens)   batched greedy Re-Pair grammar size (sum of rule rhs lengths + final sequence length)
  block_entropy(tokens,k) H_k = entropy of k-grams (bits);  cond_entropy = H_k - H_{k-1}
  ngram_repeat_census(tokens, kmax)  number of distinct k-grams occurring >= 2 times, and total repeated mass
  lag_match(tokens, lags)  P(x_i == x_{i+L}) for each lag L (periodicity probe)
"""
import math, collections, random

def _to_str(tokens):
    ids = {}
    out = []
    for t in tokens:
        if t not in ids: ids[t] = len(ids)
        out.append(ids[t])
    # map ids into a private-use-area-free range of code points (avoid surrogates 0xD800-0xDFFF)
    def cp(i):
        c = 0x100 + i
        return c + 0x900 if c >= 0xD800 else c
    return "".join(chr(cp(i)) for i in out), len(ids)

def lz76(tokens):
    """Kaspar & Schuster (1987) LZ76 complexity c(n): number of phrases in the exhaustive history."""
    s, _ = _to_str(tokens)
    n = len(s)
    if n == 0: return 0
    i = 0; c = 0
    while i < n:
        # longest prefix of s[i:] that occurs in s[:i+l-1] (reproducible from the past, allowing overlap)
        l = 1
        while i + l <= n and s.find(s[i:i + l], 0, i + l - 1) != -1:
            l += 1
        c += 1
        i += l
    return c

def lz78(tokens):
    d = set(); w = (); c = 0
    for t in tokens:
        w2 = w + (t,)
        if w2 in d: w = w2
        else: d.add(w2); c += 1; w = ()
    return c + (1 if w else 0)

def repair_size(tokens, min_count=2):
    """Batched greedy Re-Pair: each pass replaces every pair occurring >= min_count times (most frequent first,
    non-overlapping, left to right) by a new nonterminal; stops when no pair repeats.
    Returns (grammar_size, n_rules, final_len) with grammar_size = 2*n_rules + final_len."""
    seq = list(tokens)
    next_id = 0; rules = 0
    while True:
        cnt = collections.Counter(zip(seq, seq[1:]))
        cand = [(p, c) for p, c in cnt.items() if c >= min_count]
        if not cand: break
        cand.sort(key=lambda pc: (-pc[1], str(pc[0])))
        chosen = {}
        used = set()
        for p, c in cand:
            if p[0] in used or p[1] in used: continue   # keep this pass's pairs disjoint in symbols (non-overlap safety)
            chosen[p] = ("NT", next_id); next_id += 1; used.add(p[0]); used.add(p[1])
        if not chosen: break
        out = []; i = 0; n = len(seq); replaced = 0
        while i < n:
            if i + 1 < n and (seq[i], seq[i + 1]) in chosen:
                out.append(chosen[(seq[i], seq[i + 1])]); i += 2; replaced += 1
            else:
                out.append(seq[i]); i += 1
        # only count rules that were actually used at least twice; others are expanded back (cheap approximation: keep all used)
        usedc = collections.Counter(x for x in out if isinstance(x, tuple) and x[0] == "NT")
        inv = {v: k for k, v in chosen.items()}
        single = {nt for nt in chosen.values() if usedc[nt] < 2}
        if single:
            out2 = []
            for x in out:
                if x in single: out2.extend(inv[x])
                else: out2.append(x)
            out = out2
        new_rules = len(chosen) - len(single)
        rules += new_rules
        if new_rules == 0: break
        seq = out
    return 2 * rules + len(seq), rules, len(seq)

def block_entropy(tokens, k):
    n = len(tokens) - k + 1
    if n <= 0: return 0.0
    cnt = collections.Counter(tuple(tokens[i:i + k]) for i in range(n))
    return -sum(c / n * math.log2(c / n) for c in cnt.values())

def ngram_repeat_census(tokens, kmax=8):
    res = {}
    for k in range(2, kmax + 1):
        cnt = collections.Counter(tuple(tokens[i:i + k]) for i in range(len(tokens) - k + 1))
        rep = {g: c for g, c in cnt.items() if c >= 2}
        res[k] = (len(rep), sum(rep.values()), max(rep.values()) if rep else 0)
    return res

def lag_match(tokens, lags):
    n = len(tokens); out = {}
    for L in lags:
        m = n - L
        if m <= 0: out[L] = float("nan"); continue
        out[L] = sum(1 for i in range(m) if tokens[i] == tokens[i + L]) / m
    return out

def shuffle_blocks(blocks, rng):
    """section-preserving shuffle: permute tokens inside each block, keep block order."""
    out = []
    for b in blocks:
        b = list(b); rng.shuffle(b); out.extend(b)
    return out

def random_linear_extension(items, chains_of, rng):
    """items: list of indices 0..n-1 in a valid order; chains_of(i) -> iterable of chain keys (registers) item i belongs to.
    Returns a uniformly-ish random topological order of the partial order 'same chain => original order'
    (random-priority Kahn)."""
    n = len(items)
    last = {}; pred = [[] for _ in range(n)]; succ = [[] for _ in range(n)]
    for i in range(n):
        for r in chains_of(i):
            if r in last:
                pred[i].append(last[r]); succ[last[r]].append(i)
            last[r] = i
    indeg = [len(p) for p in pred]
    import heapq
    prio = [rng.random() for _ in range(n)]
    heap = [(prio[i], i) for i in range(n) if indeg[i] == 0]; heapq.heapify(heap)
    out = []
    while heap:
        _, i = heapq.heappop(heap); out.append(i)
        for j in succ[i]:
            indeg[j] -= 1
            if indeg[j] == 0: heapq.heappush(heap, (prio[j], j))
    assert len(out) == n
    return out

def zstats(real, nulls):
    m = sum(nulls) / len(nulls)
    sd = (sum((x - m) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** 0.5
    z = (real - m) / sd if sd > 0 else float("inf") if real != m else 0.0
    return m, sd, z
