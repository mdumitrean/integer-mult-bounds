#!/usr/bin/env python3
"""Lane C grounding, part 3: the lives-vs-register-slots bipartite graph of #2802's base word.

Data: the r10 J-dim1 census of the #2802 construction (CENSUS-b.json: per-helper first/last event,
entrance floor/ceiling hi, per-lender last event and exact floor lo, the 72 hosted segments).
Model (the alias rule of the lineage): a life l (a helper that enters in B with a non-empty start frame)
can live in register slot s iff  last(s) < first(l)  and  lo(s) <= hi(l)  (frames refit over the exact
lattice).  Slots: the 330 free retired registers (lo 6..8) and the 72 own-life segments of the current
lender registers (lo 4, or 5 for the refit lenders 564/565), currently occupied by the 72 hosted lives.
Computes: degree histograms (time-only supergraph and lo/hi graph), a maximum matching (Hopcroft-Karp),
and the Koenig/Hall deficiency certificate by the alternating "burning" from unmatched lives
(fire spreads life -> every neighbouring slot -> that slot's matched life).  The burnt lives S satisfy
|S| - |N(S)| = number of unmatched lives: an exact non-hostability certificate (the 74-vs-72 pigeonhole
for 670/671 should appear as the burnt set of the hi-5 lives).
usage: ground_bipartite.py CENSUS-b.json OUT_JSON
"""
import json, sys, collections
from pathlib import Path

census = json.load(open(sys.argv[1])); OUT = Path(sys.argv[2])
helpers = {int(k): v for k, v in census['helpers'].items()}
lend = {int(k): v for k, v in census['lend'].items()}
segments = census['segments']

# ---- lives: followers (private register, not hosted) + the 72 hosted lives (one per segment)
lives = {}
for h, d in helpers.items():
    if d['status'] == 'follower':
        lives[('follower', h)] = dict(first=d['first'], hi=d['hi'], width=d['width'])
seg_by_lender = {}
for s in segments:
    lives[('hosted', s['op'])] = dict(first=s['hosted_first'], hi=s['hosted_hi'], width=None, lender=s['lender'])
    seg_by_lender[s['lender']] = s
# ---- slots: free retired registers + the own-life segments of hosting registers
slots = {}
for r, d in lend.items():
    if d.get('hosts'):
        s = seg_by_lender.get(r)
        if s is None: continue
        slots[('segment', r)] = dict(last=s['own_last'], lo=s['own_lo'], occupied_by=('hosted', s['op']))
    else:
        slots[('free', r)] = dict(last=d['last'], lo=d['lo'], occupied_by=None)
# segments whose lender is not in lend (lender register has no further retirement entry)
for s in segments:
    if ('segment', s['lender']) not in slots:
        slots[('segment', s['lender'])] = dict(last=s['own_last'], lo=s['own_lo'], occupied_by=('hosted', s['op']))

def edges(frame_rule):
    adj = {}
    for l, dl in lives.items():
        adj[l] = [s for s, ds in slots.items() if ds['last'] < dl['first'] and (not frame_rule or ds['lo'] <= dl['hi'])]
    return adj

def hopcroft_karp(adj):
    # simple augmenting-path matching (graph is tiny: ~122 x ~402)
    match_l, match_s = {}, {}
    def try_aug(l, seen):
        for s in adj[l]:
            if s in seen: continue
            seen.add(s)
            if s not in match_s or try_aug(match_s[s], seen):
                match_l[l] = s; match_s[s] = l; return True
        return False
    for l in adj:
        try_aug(l, set())
    return match_l, match_s

def burn(adj, match_l, match_s):
    """Koenig alternating search from unmatched lives (Dhar-style spreading): returns burnt lives S and slots N(S)."""
    S = set(l for l in adj if l not in match_l); front = list(S); NS = set()
    while front:
        l = front.pop()
        for s in adj[l]:
            if s in NS: continue
            NS.add(s)
            l2 = match_s.get(s)
            if l2 is not None and l2 not in S:
                S.add(l2); front.append(l2)
    return S, NS

out = dict(n_lives=len(lives), n_slots=len(slots),
           lives_by_hi=dict(collections.Counter(d['hi'] for d in lives.values())),
           slots_by_lo=dict(collections.Counter(d['lo'] for d in slots.values())),
           slots_occupied=sum(1 for d in slots.values() if d['occupied_by']))
for name, rule in (('time_only', False), ('time_and_frame', True)):
    adj = edges(rule)
    deg = collections.Counter(len(v) for v in adj.values())
    deg_by_hi = collections.defaultdict(list)
    for l, v in adj.items(): deg_by_hi[lives[l]['hi']].append(len(v))
    ml, ms = hopcroft_karp(adj)
    S, NS = burn(adj, ml, ms)
    unmatched = sorted(str(l) for l in adj if l not in ml)
    res = dict(max_matching=len(ml), unmatched=len(unmatched), unmatched_sample=unmatched[:6],
               degree_hist=dict(sorted(deg.items())),
               degree_by_hi={hi: dict(min=min(v), max=max(v), mean=round(sum(v) / len(v), 1), n=len(v)) for hi, v in deg_by_hi.items()},
               hall_violator=dict(S=len(S), N_S=len(NS), deficiency=len(S) - len(NS),
                                  S_by_hi=dict(collections.Counter(lives[l]['hi'] for l in S)),
                                  N_S_by_lo=dict(collections.Counter(slots[s]['lo'] for s in NS))))
    # the sub-certificate for the hi-5 lives alone
    hi5 = [l for l in adj if lives[l]['hi'] >= 4]
    N5 = set(s for l in hi5 for s in adj[l])
    res['hi5_pigeonhole'] = dict(lives=len(hi5), neighbourhood=len(N5), N_by_lo=dict(collections.Counter(slots[s]['lo'] for s in N5)))
    # 670/671 near misses in the time-only graph: dim gap of their time-OK slots
    for h in (670, 671):
        l = ('follower', h)
        if l in adj:
            gaps = collections.Counter(slots[s]['lo'] - lives[l]['hi'] for s in edges(False)[l])
            res[f'follower_{h}_time_ok_slots_by_dim_gap'] = dict(sorted(gaps.items()))
    out[name] = res
OUT.write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
