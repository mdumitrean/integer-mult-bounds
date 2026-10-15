"""structure: pivot service structure (copy register, copy reads, direct reads) + S-constant intervals."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sx
from fractions import Fraction as Q
def build(w):
    B, tail, seq = sx.build_seq(w); N = sx.nregs(w); S = sx.Suffix(seq, N)
    return B, tail, seq, N, S
def interval(S, z, p):
    """[lo, hi] positions with S_z(p') == S_z(p)."""
    import bisect
    ch = S.change[z]; j = bisect.bisect_left(ch, p)
    lo = ch[j - 1] + 1 if j > 0 else 0; hi = ch[j] if j < len(ch) else S.L
    return lo, hi
def service(w, q, B, seq, S):
    nB = len(B)
    reads = [i for i, g in enumerate(seq) if g[0] == 'add' and g[2] == q]
    Breads = [i for i in reads if i < nB]; Treads = [i for i in reads if i >= nB]
    out = dict(q=q, Breads=Breads, Treads=Treads)
    # copy: B read whose target is undone by a tail read
    for t in Treads:
        c = seq[t][1]
        cb = [i for i in Breads if seq[i][1] == c]
        if cb:
            out['copy'] = c; out['copy_in'] = cb[0]; out['copy_out'] = t
            out['copy_reads'] = [i for i, g in enumerate(seq) if g[0] == 'add' and g[2] == c]
            out['copy_writes'] = [i for i, g in enumerate(seq) if g[1] == c]
    out['direct'] = [i for i in Breads if i != out.get('copy_in')]
    return out
if __name__ == '__main__':
    w = sx.load(sys.argv[1]); B, tail, seq, N, S = build(w)
    for q in map(int, sys.argv[2].split(',')):
        sv = service(w, q, B, seq, S); print(q, sv)
        for i in sv['Breads'] + sv.get('copy_reads', []):
            g = seq[i]; print('   ', i, g[:5], 'S-int of target', interval(S, g[1], i + 1), 'writes of src', [j for j, h in enumerate(seq) if h[1] == g[2]][:8])
