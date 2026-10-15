"""aplan.py: dedupe A-window alternatives by the resulting A section and write a prioritised pricing plan with quotas.
Key of an alternative replacing A[i:i+k] by alt: strip the common prefix/suffix with the original window; two alternatives
with the same (start, replaced length, new middle) give the same word.  Order: all strict reductions; same-length
non-permutation rewrites k=2, k=3 (all), k=4 (large-deletion windows, then nonzero-frame up to a quota); permutations
(large-deletion windows first, quotas); 2->3 rewrites on large-deletion windows (quota).  usage: aplan.py out.jsonl"""
import json, gzip, os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, HERE); import apeep
A = json.load(gzip.open(os.path.join(SCR, 'r3/inputs/gauge44-word-566-554.json.gz')))['A']
orig = [tuple(str(x) for x in apeep.gt(g)) for g in A]
def norm(t): return tuple(str(x) for x in t)
seen = set(); groups = {}
for k in (2, 3, 4):
    for l in open(os.path.join(HERE, '..', 'out', f'ALT-k{k}.jsonl')):
        r = json.loads(l); i = r['i']; alt = [norm(t) for t in r['alt']]; win = orig[i:i + k]; L = len(alt)
        p = 0
        while p < min(L, k) and alt[p] == win[p]: p += 1
        s = 0
        while s < min(L, k) - p and alt[L - 1 - s] == win[k - 1 - s]: s += 1
        key = (i + p, k - p - s, tuple(alt[p:L - s]))
        if key in seen: continue
        seen.add(key)
        g = 'reduce' if L < k else ('same' if (L == k and not r['perm']) else ('perm' if r['perm'] else 'longer'))
        pr = 'big' if r['big'] else ('nz' if r['nz'] else 'zero')
        groups.setdefault((g, k, pr), []).append(r)
random.seed(7)
for v in groups.values(): v.sort(key=lambda r: r['i'])
def take(g, k, pr, n=None):
    v = groups.get((g, k, pr), [])
    return v if n is None or len(v) <= n else sorted(random.sample(v, n), key=lambda r: r['i'])
plan = []
for k in (2, 3, 4):
    for pr in ('big', 'nz', 'zero'): plan += take('reduce', k, pr)
for k in (2, 3):
    for pr in ('big', 'nz', 'zero'): plan += take('same', k, pr)
plan += take('same', 4, 'big') + take('same', 4, 'nz', 1200)
plan += take('perm', 2, 'big') + take('perm', 3, 'big', 900) + take('perm', 4, 'big', 600)
plan += take('longer', 2, 'big', 900) + take('perm', 2, 'nz', 400) + take('same', 4, 'nz', 2000)[:0]
with open(sys.argv[1], 'w') as f:
    for r in plan: f.write(json.dumps(r) + '\n')
print('unique alternatives:', len(seen), {f'{g}/{k}/{pr}': len(v) for (g, k, pr), v in sorted(groups.items())})
print('plan:', len(plan))
