"""lineage.py: diff the entering structure (start_extra, helper_final, sections) along the vendored word lineage.
usage: python3 -I -B lineage.py OUT.json NAME=PATH ...  (paths are data; nothing is imported from them)"""
import gzip, json, sys, hashlib
from collections import Counter
out = sys.argv[1]; pairs = [a.split('=', 1) for a in sys.argv[2:]]
def load(p): return json.loads(gzip.decompress(open(p, 'rb').read()))
def dimbasis(vs):  # rank over GF(2) of a list of 9-bit ints
    rows = []; 
    for v in vs:
        for r in rows:
            v = min(v, v ^ r)
        if v: rows.append(v)
    return len(rows)
words = {n: load(p) for n, p in pairs}
res = {}; prev = None
for n, w in words.items():
    se = {int(k): v for k, v in w.get('start_extra', {}).items()}; hf = {int(k): v for k, v in w.get('helper_final', {}).items()}
    sec = {s: len(w[s]) for s in ('precondition', 'A', 'cut', 'B', 'cleanup') if s in w}
    canon = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()[:12]
    r = dict(sections=sec, n_start_extra=len(se), n_helper_final=len(hf), early_cleanup=len(w.get('early_cleanup', [])),
             start_extra_dims=dict(sorted(Counter(dimbasis(v) for v in se.values()).items())),
             section_hash={s: canon(w[s]) if s != 'B' else canon([g[:-1] for g in w['B']]) for s in ('precondition', 'A', 'cut', 'B')},
             A_ops_hash=canon([g[:-1] for g in w['A']]), profile=w.get('report', {}).get('local_profile'))
    if prev is not None:
        pw = words[prev]; pse = {int(k): v for k, v in pw.get('start_extra', {}).items()}; phf = {int(k): v for k, v in pw.get('helper_final', {}).items()}
        r['vs_prev'] = dict(prev=prev,
            start_extra_added=sorted(set(se) - set(pse)), start_extra_removed=sorted(set(pse) - set(se)),
            start_extra_changed=sorted(k for k in set(se) & set(pse) if se[k] != pse[k]),
            helper_final_added=sorted(set(hf) - set(phf)), helper_final_removed=sorted(set(phf) - set(hf)),
            helper_final_changed=sorted(k for k in set(hf) & set(phf) if hf[k] != phf[k]),
            A_ops_same=[g[:-1] for g in w['A']] == [g[:-1] for g in pw['A']], A_frames_same=w['A'] == pw['A'],
            cut_same=w['cut'] == pw['cut'], precondition_same=w['precondition'] == pw['precondition'],
            B_ops_same=[g[:-1] for g in w['B']] == [g[:-1] for g in pw['B']])
    res[n] = r; prev = n
json.dump(res, open(out, 'w'), indent=1, sort_keys=True)
for n, r in res.items():
    print(n, r['sections'], 'start_extra', r['n_start_extra'], r['start_extra_dims'], 'helper_final', r['n_helper_final'], 'profile', r['profile'])
    if 'vs_prev' in r:
        v = r['vs_prev']; print('   vs', v['prev'], {k: (x if not isinstance(x, list) or len(x) < 12 else f'{len(x)} items') for k, x in v.items() if k != 'prev'})
