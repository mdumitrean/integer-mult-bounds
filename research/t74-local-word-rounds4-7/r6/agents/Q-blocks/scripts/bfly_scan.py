"""bfly_scan.py (agent Q-blocks, r6): find B-section butterflies (a += c1 b; b += c2 a) whose two outputs are only delivered
into ports afterwards (no other read or write of a or b later in B or in the early-cleanup tail).  usage: bfly_scan.py WORD OUT"""
import gzip, json, sys
from fractions import Fraction as Fr
W = json.load(gzip.open(sys.argv[1])); B = W['B']; V = 112
tail = [W['cleanup'][i] for i, U in W['early_cleanup']]
low = set(map(int, W['helper_final'])); ent = set(map(int, W['start_extra']))
isport = lambda r: V <= r < 2 * V
def regs(g): return {g[1], g[2]} if g[0] == 'add' else {g[1]}
out = []
for i in range(len(B) - 1):
    g1, g2 = B[i], B[i + 1]
    if g1[0] != 'add' or g2[0] != 'add': continue
    a, b = g1[1], g1[2]
    if not (g2[1] == b and g2[2] == a): continue
    if isport(a) or isport(b): continue
    later = [(j, B[j]) for j in range(i + 2, len(B)) if regs(B[j]) & {a, b}]
    reads = [(j, g) for j, g in later if g[0] == 'add' and g[2] in (a, b) and g[1] not in (a, b)]
    writes = [(j, g) for j, g in later if g[1] in (a, b)]
    tail_touch = [g for g in tail if regs(g) & {a, b}]
    deliv = [(j, g) for j, g in reads if isport(g[1])]
    ok = not writes and not tail_touch and len(deliv) == len(reads) and len(deliv) >= 1
    out.append(dict(pos=i, a=a, b=b, g1=g1[:5], g2=g2[:5], deliveries=[(j, g[:5]) for j, g in deliv], other_reads=[(j, g[:5]) for j, g in reads if not isport(g[1])],
                    later_writes=[(j, g[:5]) for j, g in writes], tail_touch=len(tail_touch), low=[x for x in (a, b) if x in low], entering=[x for x in (a, b) if x in ent], ok=ok))
json.dump(out, open(sys.argv[2], 'w'), indent=0)
okk = [o for o in out if o['ok']]
print('butterflies', len(out), 'pattern ok (outputs only delivered to ports, untouched after, not in tail):', len(okk))
print('  low-helper involvement among ok:', sum(1 for o in okk if o['low']), '| entering:', sum(1 for o in okk if o['entering']))
for o in okk[:12]: print('  B%d %s %s -> %s' % (o['pos'], o['g1'], o['g2'], o['deliveries']))
