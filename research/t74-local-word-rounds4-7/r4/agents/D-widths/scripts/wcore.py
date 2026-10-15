"""wcore: price a helper-interface change (start_extra / helper_final) on a fixed local word with exact optimal frames.
The program is unchanged; only start or end frames of helpers change.  Cone caps are recomputed (they depend on
helper_final).  usage: imported; set IMB_ROOT and put the toolkit on sys.path first."""
import copy, gzip, json, time
import frames as F
from word import inline
from model import cone_caps
B = "0.001679754956125544"
def load(p): return json.load(gzip.open(p))
def solve(w, costs, timeout=None):
    caps, comp = cone_caps(w)
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
    return r, g, len(comp)
def reduce_vec(x, basis):   # basis: dict pivotbit -> vector (echelon)
    for bit in sorted(basis, reverse=True):
        if x >> bit & 1: x ^= basis[bit]
    return x
def echelon(vectors):
    basis = {}
    for v in vectors:
        v = reduce_vec(v, basis)
        if v:
            bit = v.bit_length() - 1
            for k in list(basis):
                if basis[k] >> bit & 1: basis[k] ^= v
            basis[bit] = v
    return basis
def hyperplanes(vectors):
    """all (d-1)-dim subspaces of span(vectors), as basis lists"""
    b = list(echelon(vectors).values()); d = len(b); out = []
    for f in range(1, 1 << d):
        j = (f & -f).bit_length() - 1
        out.append(sorted(b[i] ^ (b[j] if f >> i & 1 else 0) for i in range(d) if i != j))
    return out
def extensions(vectors):
    """all (d+1)-dim superspaces of span(vectors) in GF(2)^9, as basis lists"""
    basis = echelon(vectors); seen = set(); out = []
    for x in range(1, 512):
        r = reduce_vec(x, basis)
        if r and r not in seen:
            # canonical representative of the coset line: r and r reduced are unique per extension
            seen.add(r); out.append(sorted(list(basis.values()) + [r]))
    # distinct superspaces: dedupe by echelon form
    uniq = {}
    for o in out: uniq[tuple(sorted(echelon(o).values()))] = o
    return list(uniq.values())
