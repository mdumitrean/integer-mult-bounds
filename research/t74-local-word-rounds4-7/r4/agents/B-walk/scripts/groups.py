"""List (A,H,q) shared-fusion groups (>=2 port targets) on a word and the exact gates that block a shared donation."""
import collections, json, sys
from fractions import Fraction as Q
sys.path.insert(0, __import__('os').path.dirname(__file__)); import common
import fusion as G
w = common.load(sys.argv[1] if len(sys.argv) > 1 else 'base')
I = G.index(w); B = I['B']; reads = G.data_reads(w, I)
by = collections.defaultdict(list)
for t, rs in reads.items():
    for (iA, A, a) in rs:
        for (iH, H, h) in rs:
            if A == H or iA == iH or A == t or H == t: continue
            if G.any_in(I['RD'][t] + I['SC'][t], min(iA, iH), max(iA, iH) + 1): continue
            q = a / h
            if G.dyadic(q): by[(A, H, q)].append((t, iA, iH))
out = []
for (A, H, q), lst in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][1])):
    if len({t for t, _, _ in lst}) < 2: continue
    lst = sorted(lst, key=lambda x: x[2]); selH = [iH for _, _, iH in lst]; selA = [iA for _, iA, _ in lst]
    lo, hi = min(selH + selA), max(selH + selA)
    otherH = sorted(x for x in I['RD'][H] + I['SC'][H] if x not in selH and min(selH) <= x <= max(selH))
    wA = sorted(x for x in I['W'][A] if lo <= x <= hi)
    out.append(dict(A=A, H=H, q=str(q), targets=[dict(t=t, iA=iA, iH=iH) for t, iA, iH in lst],
                    H_blockers=[dict(i=x, gate=B[x][:5]) for x in otherH], A_writes=[dict(i=x, gate=B[x][:5]) for x in wA]))
print(json.dumps(out, indent=1))
