"""pairs.py: characterise how every entering helper's initial value is pre-cancelled in a word.
For each entering helper e (start_extra): gates that read e while e is still pure (before e's first write), in program
order precondition, A, cut, B; the partners they write, their types; plus e's first write. usage: pairs.py WORD OUT.json"""
import gzip, json, sys
from collections import Counter, defaultdict
w = json.loads(gzip.decompress(open(sys.argv[1], 'rb').read()))
V = 112; R = w['report']['R']; ent = {int(k): v for k, v in w['start_extra'].items()}; cold = {int(k) for k in w['helper_final']}
def regs(g): return (g[1], g[2]) if g[0] == 'add' else (g[1],)
seq = [('P', i, g) for i, g in enumerate(w['precondition'])] + [('A', i, g) for i, g in enumerate(w['A'])] + \
      [('C', i, g) for i, g in enumerate(w['cut'])] + [('B', i, g) for i, g in enumerate(w['B'])]
first_write = {}; pure_reads = defaultdict(list)
for sec, i, g in seq:
    t = g[1]
    if g[0] == 'add':
        s = g[2]
        if s in ent and s not in first_write: pure_reads[s].append((sec, i, t, g[3], g[4] if len(g) > 5 else 1))
    first_write.setdefault(t, (sec, i))
def kind(r):
    if r < V: return 'data'
    if r < 2 * V: return 'target'
    if r in ent: return 'entering'
    if r in cold: return 'cold'
    return 'ordinary'
out = {}; summary = Counter(); partner_kinds = Counter()
for e in sorted(ent):
    pr = pure_reads.get(e, [])
    out[e] = dict(start_extra=ent[e], first_write=first_write.get(e), pure_reads=pr,
                  partners=sorted({t for _, _, t, _, _ in pr}), partner_kinds=sorted({kind(t) for _, _, t, _, _ in pr}),
                  pure_read_sections=sorted({s for s, _, _, _, _ in pr}))
    summary[(len(pr) > 0, tuple(out[e]['pure_read_sections']))] += 1
    for _, _, t, _, _ in pr: partner_kinds[kind(t)] += 1
json.dump(dict(per_helper={str(k): v for k, v in out.items()},
               summary={f'{k[0]}|{",".join(k[1])}': v for k, v in summary.items()},
               partner_kinds=dict(partner_kinds), n_entering=len(ent), n_cold=len(cold)), open(sys.argv[2], 'w'), indent=1)
print('entering', len(ent), 'cold', len(cold)); print('has pure reads | sections:', dict(summary)); print('partner kinds over pure reads:', dict(partner_kinds))
for e in (526, 527, 538, 539, 550, 551, 563, 506, 518):
    if e in out: print(e, out[e]['start_extra'], 'first write', out[e]['first_write'], 'pure reads', out[e]['pure_reads'][:4])
