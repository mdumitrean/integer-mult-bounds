"""Follow the binding hi-chain forward from a gate: at each gate, take the operand whose next framed event has the
smallest hi (that is what caps it); stop at a warp U, a boundary pin, or the end frame."""
import sys, json
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
nxt = {}
for r, L in b.byreg.items():
    for i, x in enumerate(L):
        nxt[(r, x[0])] = L[i + 1] if i + 1 < len(L) else None
def cls(q):
    return 'src' if q < v else 'tgt' if q < 2 * v else ('ctr' if q in w['centers'] else 'hlp')
for t0 in map(int, sys.argv[3].split(',')):
    t = t0; chain = []
    for _ in range(40):
        sec, e = ev[t]; d = len(b.hi[t]); rs = regs(e)
        cand = []
        for q in rs:
            x = nxt.get((q, t))
            if x is None: cand.append((len(Wd.end[q]), q, 'END', None)); continue
            if x[1] == 'warp': cand.append((len(x[2]), q, 'WARP-U', x[0])); continue
            cand.append((len(b.hi[x[0]]), q, 'gate', x[0]))
        cand.sort()
        chain.append((t, sec, e[0], [(q, cls(q)) for q in rs], d, cand[0][:3]))
        if cand[0][0] > d or cand[0][2] != 'gate':
            break
        t = cand[0][3]
    print('from', t0, 'hi', len(b.hi[t0]))
    for c in chain[:14]: print('  ', c)
    if len(chain) > 14: print('   ...', chain[-1])
