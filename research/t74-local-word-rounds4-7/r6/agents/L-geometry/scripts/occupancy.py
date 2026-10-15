"""Per-child bin occupancy of the current T74 owner map: compositions of whole-helper widths per (owner, child, port) bin."""
import collections, gzip, json, sys
from pathlib import Path
S = Path(__file__).resolve().parents[4]
roles = json.loads(gzip.decompress((S / 'wt-566/research/global-mixed-t74-exact-fill/OWNERS.json.gz').read_bytes()))
rank = {int(k): v['rank'] for k, v in json.load(open(S / 'r6/agents/L-geometry/out/GEOMETRY.json'))['children'].items()}
bins = collections.defaultdict(list)
for z in roles: bins[z['owner_replica'], z['child'], z['port']].append(z['width'])
T, V = 74, 112
per_child = {}
for ch in sorted(rank):
    comp = collections.Counter()
    for o in range(T):
        for p in range(V): comp[tuple(sorted(bins.get((o, ch, p), [])))] += 1
    per_child[ch] = {('+'.join(map(str, k)) or 'empty'): v for k, v in comp.most_common()}
    print(ch, rank[ch], per_child[ch])
json.dump(per_child, open(S / 'r6/agents/L-geometry/out/OCCUPANCY.json', 'w'), indent=1)
