#!/usr/bin/env python3
"""Lane C grounding, part 2: a feasibility-preserving random walk on the #2802 owner fill.

The greedy random nulls of ground_fill.py lose roles (the window system is tight), so they are not
valid fills. This null starts from the real fill and applies random single-role moves that keep every
hosting rule (time window, one role per helper per call, one role per family per call, capacity).
After K moves the fill is still a valid fill; its idle histogram and kappa show how fast the real
fill's all-or-nothing structure dissolves under rule-preserving randomisation.
usage: ground_fill_walk.py INPUT_DIR OUT_JSON [moves] [seeds]
"""
import gzip, json, sys, random, collections, time
from pathlib import Path
from mpmath import mp, mpf
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ground_fill import windows, kappa_root, LIVE2, DIM, MASS, CALLS

mp.dps = 40
IN = Path(sys.argv[1]); OUT = Path(sys.argv[2])
MOVES = int(sys.argv[3]) if len(sys.argv) > 3 else 300000
SEEDS = int(sys.argv[4]) if len(sys.argv) > 4 else 2

def load(name):
    p = IN / name
    if name.endswith('.gz'):
        with gzip.open(p, 'rt') as fh: return json.load(fh)
    return json.load(open(p))

def main():
    t0 = time.time()
    template = load('GLOBAL-TEMPLATE.json.gz'); plan = load('PLAN.json.gz'); fill = load('FILL.json.gz')
    dispatch0 = load('DISPATCH.json.gz'); order = load('ORDER.json'); providers = load('PROVIDERS.json')
    win = windows(template, order)
    dispatch = {(s, r): pid for s, r, pid in dispatch0}
    widths = [providers[dispatch[tuple(order[t])]]['widths'] for t in range(CALLS)]
    pairs = {int(k): v for k, v in plan['pairs'].items()}; sides = {int(k): v for k, v in plan['sides'].items()}
    fam = {c: 2 * pairs[c] + sides[c] for c in pairs}
    local = {int(r): n for r, n in providers['gauge44']['actual_paid_profile'].items()}
    cap_of = {(o, c): cap for (o, c), (cap, _, _) in win.items()}
    elig = collections.defaultdict(list)
    for (o, c), (cap, start, stop) in win.items():
        for t in range(start + 1, stop + 1): elig[t].append((o, c))
    rows0 = [tuple(r[:5]) for r in fill['rows']]   # (t, h, o, c, port)

    def idle_profile(rem):
        idle = collections.Counter(r for r in rem.values() if r > 0)
        prof = collections.Counter({r: CALLS * n for r, n in local.items()}); prof.update(idle)
        assert sum(r * n for r, n in prof.items()) == MASS
        return idle, prof

    results = []
    for seed in range(1, SEEDS + 1):
        rng = random.Random(seed)
        rem = {(o, c, p): cap_of[o, c] for (o, c) in win for p in range(112)}
        fams = [set() for _ in range(CALLS)]
        rows = list(rows0)
        for (t, h, o, c, port) in rows:
            rem[o, c, port] -= widths[t][h]; fams[t].add((o, fam[c], port))
        assert min(rem.values()) >= 0
        checkpoints = sorted(set([1000, 3000, 10000, 30000, 100000, MOVES]))
        accepted = 0; log = []
        for m in range(1, MOVES + 1):
            i = rng.randrange(len(rows)); t, h, o, c, port = rows[i]; w = widths[t][h]
            rem[o, c, port] += w; fams[t].discard((o, fam[c], port))
            ew = elig[t]; placed = None
            for _ in range(60):
                o2, c2 = rng.choice(ew); p2 = rng.randrange(112)
                if rem[o2, c2, p2] >= w and (o2, fam[c2], p2) not in fams[t]:
                    placed = (o2, c2, p2); break
            if placed is None: placed = (o, c, port)
            else: accepted += 1
            rem[placed] -= w; fams[t].add((placed[0], fam[placed[1]], placed[2])); rows[i] = (t, h) + placed
            if m in checkpoints:
                idle, prof = idle_profile(rem)
                k = kappa_root(prof)
                log.append(dict(moves=m, accepted=accepted, idle_bins=sum(idle.values()),
                                idle_top=dict(sorted(idle.items(), key=lambda x: -x[1])[:8]), kappa=mp.nstr(k, 20)))
                print('seed', seed, log[-1], round(time.time() - t0, 1), 's', flush=True)
        idle, prof = idle_profile(rem)
        results.append(dict(seed=seed, moves=MOVES, accepted=accepted, idle=dict(sorted(idle.items())), log=log))
    OUT.write_text(json.dumps(results, indent=1))

if __name__ == '__main__':
    main()
