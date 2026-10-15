"""r10 F-lenders: augmenting paths for the retired-lender rule with every B-warp hosting movable.
f (free follower) -> L (hosted lender, own segment ends before f.first, pinless lo(L own last) <= hi(f first))
   -> h1 (L's current hostee) -> L2 (free lender with last < h1.first and lo <= hi(h1 first)), L2 != L.
usage: python3 -I augment_r10.py CODE CENSUS.json WORD.json.gz OUT.json"""
import sys, json
sys.path.insert(0, sys.argv[1])
from bounds_nopin import Bounds
d = json.load(open(sys.argv[2])); b = Bounds(sys.argv[3])
fol = {int(h): r for h, r in d['helpers'].items() if r['status'] == 'follower'}
lend = {int(L): r for L, r in d['lend'].items()}
seg = d['segments']
nopin_lo = {}
for s in seg:
    t = s['own_last']
    nopin_lo[s['lender']] = len(b.lo[t]) if t in b.lo else None
free = {L: r for L, r in lend.items() if not r['hosts']}
paths = []
for f, fr in fol.items():
    for s in seg:
        L = s['lender']; lo = nopin_lo[L]
        if lo is None or not (s['own_last'] < fr['first'] and lo <= fr['hi']): continue
        for L2, r2 in free.items():
            if L2 != L and r2['last'] < s['hosted_first'] and r2['lo'] <= s['hosted_hi']:
                paths.append(dict(f=f, f_width=fr['width'], f_first=fr['first'], f_hi=fr['hi'], L=L, op=s['op'], L_own_last=s['own_last'],
                                  L_lo_nopin=lo, L_lo_pin=s['own_lo'], h1_first=s['hosted_first'], h1_hi=s['hosted_hi'], L2=L2, L2_last=r2['last'], L2_lo=r2['lo']))
from collections import Counter
print('nopin lo hist (hosted lenders)', Counter(nopin_lo.values()))
print('paths', len(paths), 'by f', Counter(p['f'] for p in paths), 'by L2', Counter(p['L2'] for p in paths))
print('ops usable', sorted(Counter(p['op'] for p in paths).items())[:60])
json.dump(dict(nopin_lo=nopin_lo, paths=paths), open(sys.argv[4], 'w'), indent=0)
