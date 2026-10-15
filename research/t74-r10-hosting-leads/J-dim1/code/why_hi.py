"""For each (1,1) follower: its first gate, the other register, and the chain that caps hi at 1."""
import sys, json
from collections import Counter
sys.path.insert(0, sys.argv[1])
from bounds import Bounds, regs
b = Bounds(sys.argv[2]); Wd = b.Wd; w = Wd.w; v = Wd.v; ev = b.ev
C = json.load(open(sys.argv[3]))
fol = {int(h): r for h, r in C['helpers'].items() if r['status'] == 'follower'}
def cls(q):
    if q < v: return 'src'
    if q < 2 * v: return 'tgt'
    if q in w['centers']: return 'ctr'
    return 'hlp'
rows = []; kinds = Counter()
for h, f in sorted(fol.items()):
    if f['hi'] != 1: continue
    t = f['first']; sec, e = ev[t]
    others = [q for q in regs(e) if q != h]
    q = others[0] if others else None
    # next events of q after t and their hi dims
    nxt = [(x[0], x[1], len(b.hi[x[0]]) if x[1] == 'gate' else None) for x in b.byreg.get(q, []) if x[0] > t][:6] if q is not None else []
    # h's own next gates
    hn = [(x[0], len(b.hi[x[0]]) if x[1] == 'gate' else None, len(b.lo[x[0]]) if x[1] == 'gate' else None) for x in b.byreg.get(h, []) if x[0] > t][:4]
    k = (sec, e[0], 'h-is-target' if e[1] == h else 'h-is-source', cls(q) if q is not None else None)
    kinds[k] += 1
    rows.append(dict(h=h, t=t, gate=e[:4] if e[0] == 'add' else e[:3], other=q, other_cls=cls(q) if q is not None else None,
                     hi=len(b.hi[t]), lo=len(b.lo[t]), other_next=nxt, h_next=hn, width=f['width']))
print('kinds', dict(kinds))
for r in rows[:8]: print(json.dumps(r))
json.dump(rows, open(sys.argv[4], 'w'))
