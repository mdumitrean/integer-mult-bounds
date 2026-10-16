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


# The preceding functions are the starting Lane A implementation. The additions
# below fix the inferential direction explicitly and add the registered census.
STRUCTURAL_PERIODS = (9, 8, 22, 112, 73, 480, 666, 1332)
LOWER_IS_STRONGER = frozenset(("lz76", "lz78", "repair", "H1", "H2", "H3", "H4", "H5", "H6",
                             "h1", "h2", "h3", "h4", "h5", "h6"))


def suffix_array(tokens):
    """Prefix-doubling suffix array; no suffix-sized materialized tuple keys."""
    n = len(tokens)
    if not n:
        return [], []
    ids = {}
    rank = []
    for token in tokens:
        if token not in ids:
            ids[token] = len(ids)
        rank.append(ids[token])
    original = rank[:]
    sa = list(range(n))
    width = 1
    while True:
        sa.sort(key=lambda i: (rank[i], rank[i + width] if i + width < n else -1))
        new = [0] * n
        for k in range(1, n):
            a, b = sa[k - 1], sa[k]
            new[b] = new[a] + ((rank[a], rank[a + width] if a + width < n else -1)
                               != (rank[b], rank[b + width] if b + width < n else -1))
        rank = new
        if rank[sa[-1]] == n - 1:
            break
        width *= 2
    # Kasai LCP: lcp[k] is LCP(sa[k-1], sa[k]), lcp[0] = 0.
    inv = [0] * n
    for k, offset in enumerate(sa):
        inv[offset] = k
    lcp = [0] * n
    length = 0
    for i in range(n):
        k = inv[i]
        if not k:
            length = 0
            continue
        j = sa[k - 1]
        while i + length < n and j + length < n and original[i + length] == original[j + length]:
            length += 1
        lcp[k] = length
        length = max(0, length - 1)
    return sa, lcp


def maximal_repeats(tokens, min_length=4, min_count=3, top=None, positions=True):
    """Census maximal repeats via LCP intervals of the suffix array.

    Occurrences may overlap. A maximal repeat has at least two distinct left
    contexts and two right contexts, treating the string boundaries as distinct
    sentinels. LCP internal nodes enforce right maximality; the explicit preceding
    symbol test enforces left maximality. No arbitrary length cap is applied.
    """
    sa, lcp = suffix_array(tokens)
    stack = [(0, 0)]
    repeats = []
    for i in range(1, len(sa) + 1):
        depth = lcp[i] if i < len(sa) else 0
        start = i - 1
        while stack[-1][1] > depth:
            start, length = stack.pop()
            count = i - start
            if length < min_length or count < min_count:
                continue
            offsets = sa[start:i]
            contexts = {("token", tokens[p - 1]) if p else ("begin",) for p in offsets}
            if len(contexts) < 2:
                continue
            row = dict(length=length, count=count, occurrence_mass=length * count,
                       motif=tuple(tokens[offsets[0]:offsets[0] + length]))
            if positions:
                row["positions"] = sorted(offsets)
            repeats.append(row)
        if stack[-1][1] < depth:
            stack.append((start, depth))
    repeats.sort(key=lambda row: (-row["occurrence_mass"], -row["length"], repr(row["motif"])))
    return repeats if top is None else repeats[:top]


def categorical_periodogram(tokens, periods=STRUCTURAL_PERIODS):
    """Label-invariant one-hot centered Fourier energy at each exact 1/period.

    Energy is divided by n * sum_a p_a(1-p_a). Labels have no numeric ordering;
    the normalization has iid expectation about one away from finite boundaries.
    This is a descriptive statistic, calibrated by the registered matched null.
    """
    import cmath
    n = len(tokens)
    if not n:
        return {p: None for p in periods}
    count = collections.Counter(tokens)
    variance = sum((c / n) * (1 - c / n) for c in count.values())
    if not variance:
        return {p: 0.0 if p <= n else None for p in periods}
    answer = {}
    for period in periods:
        if period > n:
            answer[period] = None
            continue
        by_symbol = collections.defaultdict(complex)
        # Reuse the integer-period phases; no accumulation of recurrent error.
        phase = [cmath.exp(-2j * math.pi * k / period) for k in range(period)]
        total = 0j
        for i, token in enumerate(tokens):
            z = phase[i % period]
            by_symbol[token] += z
            total += z
        energy = sum(abs(by_symbol[token] - c / n * total) ** 2 for token, c in count.items())
        answer[period] = energy / (n * variance)
    return answer


def measure(tokens, statistics=None, include_census=False):
    """Measure one token stream; expensive census/period work is opt-in.

    statistics=None returns the M0 calibration measurements (LZ76, RePair,
    H1..H6 and h1..h6). Request 'maximal_repeat_mass' or 'period_peak' to include
    their registered scalar summaries. include_census returns detailed evidence.
    """
    chosen = set(statistics) if statistics is not None else {"lz76", "repair", *[f"H{k}" for k in range(1, 7)]}
    out = dict(n=len(tokens), alphabet=len(set(tokens)))
    if "lz76" in chosen: out["lz76"] = lz76(tokens)
    if "lz78" in chosen: out["lz78"] = lz78(tokens)
    if "repair" in chosen:
        out["repair"], out["repair_rules"], out["repair_final"] = repair_size(tokens)
    if any(x.startswith(("h", "H")) and x[1:].isdigit() for x in chosen):
        previous = 0.0
        for k in range(1, 7):
            value = block_entropy(tokens, k)
            out[f"H{k}"] = value
            out[f"h{k}"] = value - previous
            previous = value
    if "maximal_repeat_mass" in chosen or include_census:
        repeats = maximal_repeats(tokens, positions=include_census)
        out["maximal_repeat_mass"] = sum(row["occurrence_mass"] for row in repeats)
        out["maximal_repeat_count"] = len(repeats)
        if include_census: out["maximal_repeats"] = repeats
    if "period_peak" in chosen or include_census:
        spectrum = categorical_periodogram(tokens)
        out["period_peak"] = max((v for v in spectrum.values() if v is not None), default=0.0)
        if include_census:
            out["periodogram"] = spectrum
            out["lag_match"] = {p: value if math.isfinite(value) else None
                                for p, value in lag_match(tokens, STRUCTURAL_PERIODS).items()}
    return out


def score(value, statistic):
    """All inferential scores increase with structure; compression uses -value."""
    return -value if statistic in LOWER_IS_STRONGER else value


def permutation_summary(real, nulls, statistic, inferential=True):
    """Phipson-Smyth p=(1+#null_score>=real_score)/(1+n), never zero.

    CR=null mean/real for lower-is-stronger measurements; enrichment=real/null
    mean otherwise. A zero-variance z is None with its sign recorded separately.
    """
    if not nulls:
        raise ValueError("At least one null value is required")
    mean = sum(nulls) / len(nulls)
    sd = (sum((x - mean) ** 2 for x in nulls) / max(1, len(nulls) - 1)) ** .5
    observed_score = score(real, statistic)
    tail_count = sum(score(x, statistic) >= observed_score for x in nulls)
    lower = statistic in LOWER_IS_STRONGER
    effect = (mean / real if real else (1.0 if not mean else None)) if lower else (
        real / mean if mean else (1.0 if not real else None))
    return dict(real=real, null_mean=mean, null_sd=sd, n=len(nulls), tail_count=tail_count,
                p=(1 + tail_count) / (1 + len(nulls)) if inferential else None,
                score_transform="negative" if lower else "identity", effect=effect,
                effect_name="CR" if lower else "enrichment",
                z=(real - mean) / sd if sd else None,
                zero_variance_direction=(0 if real == mean else (1 if real > mean else -1)) if not sd else None)


def bh_fdr(pvalues):
    """Benjamini-Hochberg adjusted p-values in input order (registered family)."""
    n = len(pvalues)
    answer = [None] * n
    previous = 1.0
    for rank, (index, p) in reversed(list(enumerate(sorted(enumerate(pvalues), key=lambda z: z[1]), 1))):
        if not 0 <= p <= 1:
            raise ValueError(p)
        previous = min(previous, p * n / rank)
        answer[index] = previous
    return answer
