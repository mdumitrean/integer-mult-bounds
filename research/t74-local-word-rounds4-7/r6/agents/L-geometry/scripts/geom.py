"""Dump the T74 hosting geometry: idle children (rank, pair, side), windows, per-family axis budgets (r6 L-geometry).
Reuses r6 C-hosting's ctx.load() (PR1319's unchanged independent_core.make_context on the retained T74 replay inputs)."""
import collections, json, sys
from pathlib import Path
S = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(S / 'r6/agents/C-hosting/scripts'))
import ctx as CX
L = CX.load(); c = L['ctx']; A = L['A']
rank, pair, side, win = c['rank'], c['child_pair'], c['side'], c['windows']
T = A.T; V = A.V; M = A.M
out = dict(T=T, V=V, M=M, children={})
for ch in sorted(rank):
    out['children'][ch] = dict(rank=rank[ch], pair=pair[ch], side=side[ch])
fam = collections.defaultdict(list)
for ch in rank: fam[(pair[ch], side[ch])].append(ch)
out['families'] = {f'{p},{s}': dict(children=sorted(v), ranks=[rank[x] for x in sorted(v)], total=sum(rank[x] for x in v)) for (p, s), v in sorted(fam.items())}
# windows per owner 0 (positions in the expanded event list) and how many calls each window covers
calls_by_pos = sorted(c['callpos'].items(), key=lambda kv: kv[1])
def ncalls(lo, hi): return sum(1 for _, pos in calls_by_pos if lo < pos < hi)
out['windows_owner0'] = {ch: dict(lo=win[0, ch][0], hi=win[0, ch][1], calls=ncalls(*win[0, ch])) for ch in sorted(rank)}
# per port: the pending axes of every child; check how many of the 73 axes each family uses
ph = c['phases']['recipes']
used = collections.Counter()
axes_used_per_family = collections.defaultdict(set)
for port in range(V):
    for ch in rank:
        ax = list(map(int, ph[port]['idle_children'][ch]['orthogonal_axes']))
        axes_used_per_family[(port, pair[ch], side[ch])].update(ax)
sizes = collections.Counter(len(v) for v in axes_used_per_family.values())
out['axes_used_per_port_family_hist'] = dict(sizes)
# how many distinct axes are used by children per port (all families)
per_port = collections.Counter()
for port in range(V):
    s = set()
    for ch in rank: s.update(map(int, ph[port]['idle_children'][ch]['orthogonal_axes']))
    per_port[len(s)] += 1
out['distinct_axes_per_port_hist'] = dict(per_port)
out['basis_len'] = len(c['bases'][0])
out['parent_keys'] = None
json.dump(out, open(S / 'r6/agents/L-geometry/out/GEOMETRY.json', 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('T', 'V', 'M', 'families', 'axes_used_per_port_family_hist', 'distinct_axes_per_port_hist', 'basis_len')}, indent=1))
print('windows owner0:', json.dumps(out['windows_owner0']))
