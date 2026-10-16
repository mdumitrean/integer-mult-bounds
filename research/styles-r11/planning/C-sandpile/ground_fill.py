#!/usr/bin/env python3
"""Lane C grounding: the #2802 owner fill as a capacity/threshold system.

Reads the package inputs (FILL, PLAN, ORDER, DISPATCH, PROVIDERS, GLOBAL-TEMPLATE), rebuilds the
1,332 (replica, child) windows exactly as independent_owners.py does (the windows() logic is
ported from that file: Tekalign, Apache-2.0), and computes
  * per-capacity bin occupancy histograms, idle-remainder distribution, roles-per-bin, all-or-nothing index;
  * the moment root kappa of the real profile (666 x local + idle);
  * two NULL fills that respect every hosting rule (time window, one role per helper per call, one role per
    family per call, bin capacity): (N1) uniformly random eligible bin; (N2) random "fill-up" greedy
    (prefer a partially used eligible bin); each with 2 seeds; their idle distribution and kappa.
Pure standard library + mpmath for the root. No solver. Runs in about a minute.
usage: ground_fill.py INPUT_DIR OUT_JSON
"""
import gzip, json, sys, random, collections, time
from pathlib import Path
from mpmath import mp, mpf

mp.dps = 40
IN = Path(sys.argv[1]) if len(sys.argv) > 1 else None; OUT = Path(sys.argv[2]) if len(sys.argv) > 2 else None
LIVE2 = 66304; DIM = 73; MASS = 4816512; CALLS = 666

def load(name):
    p = IN / name
    if name.endswith('.gz'):
        with gzip.open(p, 'rt') as fh: return json.load(fh)
    return json.load(open(p))

def need(ok, why):
    if not ok: raise RuntimeError(why)

def windows(template, order):
    """(replica, child) -> (cap, start, stop); eligible call times are start < t <= stop."""
    ranks = {c['child']: c['rank'] for c in template['idle_children']}
    pairs = {e['stage']: e['pair'] for e in template['recipe'] if e['kind'] == 'local'}
    blocks = {}; stage = None
    for event in template['execution_schedule']:
        if event['kind'] in ('bank_padding_cover_sweep', 'translate_every_live_family'):
            continue
        if event['kind'] == 'local_cover_sweep':
            stage = event['stage']; blocks[stage] = []
        need(stage is not None, 'event before first call')
        blocks[stage].append(event)
    progression = [0] * 74; last = {}; result = {}
    for t, (stage, replica) in enumerate(order):
        need(0 <= replica < 74 and stage == progression[replica], 'order chronology')
        progression[replica] += 1
        for j, event in enumerate(blocks[stage]):
            kind = event['kind']
            if kind == 'local_cover_sweep':
                last[replica, pairs[stage]] = t
            elif kind == 'bridge':
                last[replica, event['src']] = last[replica, event['dst']] = t
            elif kind == 'idle_cover_sweep':
                start = last.get((replica, event['pair']), -1)
                for child in event['child_indices']:
                    if child in ranks:
                        result[replica, child] = (ranks[child], start, t)
    need(progression == [9] * 74, 'complete replica progression')
    return result

def kappa_root(profile):
    """root of sum_r c_r (r/73)^(1-k) = 66304 (bisection, 40 digits)."""
    items = [(mpf(r) / DIM, c) for r, c in profile.items()]
    def M(k): return sum(c * x ** (1 - k) for x, c in items)
    lo, hi = mpf(0), mpf('0.01')
    need(M(lo) < LIVE2 < M(hi), 'root bracket')
    for _ in range(120):
        mid = (lo + hi) / 2
        if M(mid) < LIVE2: lo = mid
        else: hi = mid
    return (lo + hi) / 2

def main():
    t0 = time.time()
    template = load('GLOBAL-TEMPLATE.json.gz'); plan = load('PLAN.json.gz'); fill = load('FILL.json.gz')
    dispatch0 = load('DISPATCH.json.gz'); order = load('ORDER.json'); providers = load('PROVIDERS.json')
    win = windows(template, order)
    need(len(win) == 1332, 'window count')
    dispatch = {(s, r): pid for s, r, pid in dispatch0}
    for s, r, pid in fill['dispatch_overrides']: dispatch[s, r] = pid
    widths = [providers[dispatch[tuple(order[t])]]['widths'] for t in range(CALLS)]
    R = len(widths[0])
    pairs = {int(k): v for k, v in plan['pairs'].items()}; sides = {int(k): v for k, v in plan['sides'].items()}
    fam = {c: 2 * pairs[c] + sides[c] for c in pairs}
    local = {int(r): n for r, n in providers['gauge44']['actual_paid_profile'].items()}
    need(all({int(r): n for r, n in p['actual_paid_profile'].items()} == local for p in providers.values()), 'same local profile')
    bins = [(o, c, port) for (o, c) in win for port in range(112)]
    cap_of = {(o, c): cap for (o, c), (cap, _, _) in win.items()}

    # ---------------- real fill
    used = collections.Counter(); nroles = collections.Counter(); calls_in_bin = collections.defaultdict(set)
    for t, h, o, c, port, off in fill['rows']:
        w = widths[t][h]; used[o, c, port] += w; nroles[o, c, port] += 1; calls_in_bin[o, c, port].add(t)
    need(len(fill['rows']) == CALLS * R, 'role count')
    stats = {}
    idle = collections.Counter()
    for b in bins:
        cap = cap_of[b[:2]]; u = used.get(b, 0); need(u <= cap, 'capacity')
        if u < cap: idle[cap - u] += 1
    real_profile = collections.Counter({r: CALLS * n for r, n in local.items()}); real_profile.update(idle)
    need(sum(r * n for r, n in real_profile.items()) == MASS, 'rank mass')
    stats['idle_real'] = dict(sorted(idle.items()))
    stats['n_bins'] = len(bins); stats['n_windows'] = len(win)
    stats['cells_total'] = sum(cap_of[b[:2]] for b in bins); stats['cells_used'] = sum(used.values())
    percap = {}
    for cap in sorted(set(cap_of.values())):
        bb = [b for b in bins if cap_of[b[:2]] == cap]
        us = [used.get(b, 0) for b in bb]
        percap[cap] = dict(bins=len(bb), windows=sum(1 for w in win.values() if w[0] == cap),
                           full=sum(1 for u in us if u == cap), empty=sum(1 for u in us if u == 0),
                           partial=sum(1 for u in us if 0 < u < cap),
                           used_hist=dict(sorted(collections.Counter(us).items())),
                           roles_per_bin=dict(sorted(collections.Counter(nroles.get(b, 0) for b in bb).items())),
                           elig_len_hist=dict(sorted(collections.Counter(stop - start for (cap2, start, stop) in win.values() if cap2 == cap).items())))
    stats['per_capacity'] = percap
    # all-or-nothing index per window: fraction of ports that are full or empty
    aon = []
    for (o, c), (cap, _, _) in win.items():
        us = [used.get((o, c, p), 0) for p in range(112)]
        aon.append(sum(1 for u in us if u in (0, cap)) / 112)
    stats['window_all_or_nothing_mean'] = sum(aon) / len(aon)
    stats['windows_fully_empty'] = sum(1 for (o, c) in win if all(used.get((o, c, p), 0) == 0 for p in range(112)))
    stats['windows_fully_used'] = sum(1 for (o, c), (cap, _, _) in win.items() if all(used.get((o, c, p), 0) == cap for p in range(112)))
    # chips from how many distinct calls share a bin
    stats['bins_by_distinct_calls'] = dict(sorted(collections.Counter(len(calls_in_bin[b]) for b in bins if b in calls_in_bin).items()))
    kr = kappa_root(real_profile); stats['kappa_real'] = mp.nstr(kr, 25)
    # eligible capacity vs demand per call
    elig = collections.defaultdict(list)
    for (o, c), (cap, start, stop) in win.items():
        for t in range(start + 1, stop + 1): elig[t].append((o, c))
    demand = [sum(widths[t]) for t in range(CALLS)]
    stats['eligible_windows_per_call'] = dict(min=min(len(elig[t]) for t in range(CALLS)), max=max(len(elig[t]) for t in range(CALLS)),
                                              mean=sum(len(elig[t]) for t in range(CALLS)) / CALLS)
    stats['demand_cells_per_call'] = demand[0]
    print('real fill parsed', round(time.time() - t0, 1), 's; kappa_real', stats['kappa_real'], flush=True)

    # ---------------- null fills
    def null_fill(seed, mode):
        rng = random.Random(seed)
        rem = {b: cap_of[b[:2]] for b in bins}
        partial = collections.defaultdict(set)   # window -> bins with 0 < used < cap
        fails = 0
        for t in range(CALLS):
            fams = set(); roles = list(range(R)); rng.shuffle(roles)
            ew = elig[t]
            for h in roles:
                w = widths[t][h]; placed = None
                if mode == 'fillup':
                    # prefer a partially used bin that fits, sampled window-first among eligible windows
                    for (o, c) in rng.sample(ew, min(len(ew), 60)):
                        cands = [b for b in partial[o, c] if rem[b] >= w and (o, fam[c], b[2]) not in fams]
                        if cands: placed = rng.choice(cands); break
                if placed is None:
                    for _ in range(200):
                        o, c = rng.choice(ew); port = rng.randrange(112); b = (o, c, port)
                        if rem[b] >= w and (o, fam[c], port) not in fams:
                            placed = b; break
                if placed is None:
                    cands = [(o, c, p) for (o, c) in ew for p in range(112) if rem[o, c, p] >= w and (o, fam[c], p) not in fams]
                    if cands: placed = rng.choice(cands)
                if placed is None:
                    fails += 1; continue
                o, c, port = placed
                rem[placed] -= w; fams.add((o, fam[c], port))
                if rem[placed] > 0: partial[o, c].add(placed)
                else: partial[o, c].discard(placed)
        idle_n = collections.Counter(r for r in rem.values() if r > 0)
        prof = collections.Counter({r: CALLS * n for r, n in local.items()}); prof.update(idle_n)
        res = dict(seed=seed, mode=mode, fails=fails, idle=dict(sorted(idle_n.items())),
                   idle_bins=sum(idle_n.values()), mass=sum(r * n for r, n in prof.items()))
        if fails == 0:
            res['kappa'] = mp.nstr(kappa_root(prof), 25)
        return res
    nulls = []
    for mode in ('uniform', 'fillup'):
        for seed in (1, 2):
            t1 = time.time(); r = null_fill(seed, mode); r['seconds'] = round(time.time() - t1, 1); nulls.append(r)
            print('null', mode, seed, 'fails', r['fails'], 'idle bins', r['idle_bins'], 'kappa', r.get('kappa'), r['seconds'], 's', flush=True)
    stats['nulls'] = nulls
    stats['seconds'] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(stats, indent=1))
    print(json.dumps({k: v for k, v in stats.items() if k not in ('per_capacity',)}, indent=1))
    for cap, d in percap.items():
        print('cap', cap, {k: v for k, v in d.items() if k != 'used_hist'})
        print('   used_hist', d['used_hist'])

if __name__ == '__main__':
    main()
