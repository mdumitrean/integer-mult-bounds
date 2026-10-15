"""For each E-hosting candidate hostee h: list h's writes (h += c*q at k1..) and whether each source q is unmodified from
that write until (a) h's final read and (b) the end of B, i.e. whether an exact undo 'host -= c*q' is available."""
import sys, json, gzip
from collections import Counter
w = json.load(gzip.open(sys.argv[1])); R = json.load(open(sys.argv[2]))['rows']; v = w['report']['v']; B = w['B']
def regs(e): return e[1:3] if e[0] == 'add' else e[1:2]
writes_to = {}
for i, e in enumerate(B):
    writes_to.setdefault(e[1], []).append(i)
in_restore = Counter(e[1] for e in w['restore'])
stat = Counter(); rows = []
for r in R:
    h = r['h']; P = [i for i, e in enumerate(B) if h in regs(e)]
    wr = [i for i in P if B[i][1] == h]                       # gates writing h
    last = P[-1]
    ok_final = ok_end = True; info = []
    for i in wr:
        e = B[i]; q = e[2] if e[0] == 'add' else None
        if q is None: ok_final = ok_end = False; info.append(('scale', i)); continue
        mods = [j for j in writes_to.get(q, []) if j > i]
        a = not any(j < last for j in mods); bb = not mods and not in_restore[q]
        ok_final &= a; ok_end &= bb; info.append((i, q, 'S' if q < v else 'H', len(mods), a, bb))
    k = ('undo@final' if ok_final else '') + ('+undo@end' if ok_end else '')
    stat[k or 'none'] += 1; rows.append(dict(h=h, writes=info, last=last))
print(dict(stat))
for r in rows[:6]: print(r)
