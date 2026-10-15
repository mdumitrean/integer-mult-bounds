# X-bitleaf (r7): can the bit primitive realise the outer recurrence's compact leaf?

**Verdict: (c) obstruction.** There is no separate "leaf step" that another primitive could take over. The compact
leaf term is the complex network's own recursion count, and the bit network's calls compute exact permutations, which
cannot produce the butterfly layer. kappa above the complex endpoint C needs a stronger complex network (supplier),
not a different outer. W-ceiling's bound bit - C = 5.37e-5 is not reachable by outer restructuring.

Paths below are relative to scratchpad/r3/main (canonical main 0fdd7d82) unless noted.

## 1. Prior work (overlap search)
`scripts/find_overlap.py 'bit leaf' 'phase leaf' 'compact leaf' 'leaf primitive' 'bit-only' 'bit leaves' 'leaf_saving'
'phase_leaf' 'complex leaf'` (665 open PRs, 1,191 discussions, local READMEs; out/OVERLAP.txt): no prior attempt or
no-go on bit leaves. Related only: "bit-only outer ceilings" in PR #673 and the "bit-only corollary" in
research/format-limits*/README.md are hypothetical ceilings, not constructions.

## 2. What the two primitives compute (original manuscript, upstream/build/sections/00-introduction.tex)
- Transforms need savings in both movement and arithmetic, supplied by two separate tape procedures (lines 56-58).
- Bit procedure: interchanges two contiguous address fields, cost O(V u^tau); "its final effect is an exact
  permutation" for arbitrary auxiliary values (59-64). Its network's endpoint operator is an address shear
  (H,D) -> (H+D,D), completed to an interchange by linear-cost updates (114-117).
- Numerical (complex) procedure: applies H_0(u,v) = ((u+v)/2,(u-v)/2) on selected coordinate bits of arrays of complex
  fixed-point polynomial records, cost O(V d^lambda') (66-75); its endpoint operator is the simultaneous H_0 layer after
  diagonal phases and a dyadic scale (117-119).
- The two networks have separate branching ratios: s_b/W_b < m^tau and s_c/W_c < m^sigma, with sigma "a rational upper
  bound for the logarithmic exponent of the complex recurrence" (03-motifs.tex:682-700). Today's suppliers: bit word
  research/e8-bit-p111-tuned (c = 0.001733...), complex = the T74 566+554 supplier (C ~ 0.00167975).

## 3. What the compact leaf is (05-layers.tex:632-683, the simultaneous-layer recursion)
- A call applying C^(tensor e) on e selected chunks makes s child calls on e/m chunks of the COMPLEX network
  (branching a = s/W <= m^sigma), plus an internal-node overhead O((eK)^tau + 1) paid with the bit procedure,
  giving exponent tau(1+c/beta) < lambda (lines 645-656).
- "Stop recursion when e < d^beta and apply the e C kernels individually" (640-641): leaves are naive kernel
  applications, cost O(u) each. Their total is O(a^j u) <= O(e^sigma d^{beta(1-sigma)}) (659-667), because the NUMBER
  of leaves is a^j <= m^{j sigma}, the complex network's branching. Hence the layer exponent
  lambda' > max{lambda, sigma + beta(1-sigma)} (677-683).
- The current ledger is the same structure (W's copy of #2220, outer/check_ledger.py:124-154): tau = 1-a, sigma = 1-b,
  internal = tau (since sigma < tau), leaf = sigma + stop(1-sigma), lambda' = 1-q with q_below_leaf and
  lambda_prime_above_leaf, and the binding margin main_transform = eps*q (130, 218) is the manuscript's
  simultaneous-butterfly-rounds margin g_3 = eps(1-lambda') (08-assembly.tex:835-856). So
  kappa < eps*q < (1-stop)*b, and the bit side enters only through a < bit (144) at internal-node overhead.

## 4. Why a bit leaf is impossible
1. The leaf term has no primitive of its own to replace: its size is a^j, the complex network's child-call count.
   Lowering it means lowering s_c/W_c, i.e. a better complex network (the supplier problem of rounds r3-r7).
2. Replacing the complex child calls by bit-network calls cannot preserve the computed map. Every bit-network call
   ends in an address interchange, an exact permutation of records (00-introduction.tex:62-64, 114-117), so any
   composition of such calls is a monomial operator up to the auxiliary restoration. H_0 and C^(tensor e) are not
   monomial: each output mixes two inputs with weights +-1/2 (66-69). No product of permutations equals them.
3. Conversion overhead does not rescue it. Doing the arithmetic outside the complex network is the naive leaf
   (cost O(e) per record, 640-641) at every level, i.e. sigma = 1 and complex saving 0, so lambda' -> 1 and kappa -> 0.
   Raising the stop parameter beta only increases sigma + beta(1-sigma).

## 5. Consequence
kappa <= (1-stop)*b < C is structural for this algorithm family (Gaussian resampling, synthetic polynomial transforms,
simultaneous butterfly layers): every transform level's butterflies run through the complex network's recursion.
The bit headroom (c - C = 5.37e-5) is usable only by a stronger complex network. The remaining routes are the ones
r6/r7 mapped (factory/packet redesign, new parent) or an algorithm whose butterfly layers do not go through
C^(tensor e) at all, which would be a new multiplication algorithm, outside this framework.

No code was run apart from the overlap search; nothing committed or posted. Prepared with substantial AI assistance
(Anthropic Claude, via Claude Code).
