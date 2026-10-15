"""Select neutral pre-moves that touch the registers of kernel-sized reads (W0 relaxation band -8,879..-3,000), round-robin
over those registers for diversity.  usage: select.py N -> out/SEL.json"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import common
W0 = common.load('base'); B = W0['B']; N = int(sys.argv[1])
r = json.load(open(os.path.join(common.R3, 'agents', 'A-extra', 'out', 'relax-extra.json')))['results']
KB = sorted(int(k) for k, v in r.items() if -8879 <= v['delta'] <= -3000)
def regs_of(e): return set(e[1:3]) if e[0] == 'add' else {e[1]}
KR = collections.Counter(x for i in KB for x in regs_of(B[i]) if x >= 224)
pms = [p for p in json.load(open(os.path.join(common.OUT, 'PREMOVES.json'))) if p['delta1'] in (0, None) and p['src'] != 'D-twocol']
def nregs(ed):
    s = set()
    for i in ed['delete']: s |= regs_of(B[i])
    for _, g in ed['insert'] + ed.get('tail', []): s |= regs_of(g)
    return s
by = collections.defaultdict(list)
for p in pms:
    hit = sorted(x for x in nregs(p['ed']) if x in KR)
    if hit: by[hit[0]].append(p)
order = sorted(by, key=lambda x: -KR[x]); sel = []; k = 0
while len(sel) < N and any(by.values()):
    x = order[k % len(order)]; k += 1
    if by[x]: sel.append(by[x].pop(0))
print('kernel-sized B reads', len(KB), 'helper registers', len(KR), 'eligible pre-moves', sum(len(v) for v in by.values()) + len(sel), 'selected', len(sel), collections.Counter(p['src'] for p in sel))
json.dump(sel, open(os.path.join(common.OUT, 'SEL.json'), 'w'))
