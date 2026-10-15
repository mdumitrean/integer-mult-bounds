"""levels.py: for each centre c, D_c = C_c ∩ (∩ perp(p_t) over targets t it serves) ∩ (∩ C_c' for the other centres serving
those targets): the largest common target level that would shrink c's descent without forcing a split descent elsewhere.
usage: levels.py WORD.json.gz"""
import json, gzip, sys, collections, itertools
V = 112
w = json.load(gzip.open(sys.argv[1])); ports = w['ports']
def span(vs):
    pts = {0}
    for v in vs: pts |= {p ^ v for p in pts}
    return frozenset(pts)
def dim(S): return len(S).bit_length() - 1
perp = lambda p: frozenset(x for x in range(512) if (x & p).bit_count() % 2 == 0)
C = {c: span(tuple(f)) for c, f in zip(w['centers'], w['center_frames'])}
serves = collections.defaultdict(set); servedby = collections.defaultdict(set)
for g in w['cut']: serves[g[2]].add(g[1]); servedby[g[1]].add(g[2])
print('targets served:', len(servedby), 'by #centres:', dict(collections.Counter(len(s) for s in servedby.values())))
print('centre frame pairwise intersection dims:', sorted({dim(C[a] & C[b]) for a, b in itertools.combinations(C, 2)}))
res = {}
for c in w['centers']:
    T = serves[c]; D = C[c]
    for t in T: D &= perp(ports[t - V])
    D2 = D
    for t in T:
        for c2 in servedby[t]: D2 &= C[c2]
    res[c] = dict(targets=len(T), dim_C_perp=dim(D), dim_with_cocentres=dim(D2), cocentres=sorted({c2 for t in T for c2 in servedby[t]} - {c}))
    print('centre', c, res[c])
# data registers whose port vector lies in D (cheap dummy-pair carriers at the start of A)
for c in w['centers']:
    T = serves[c]; D = C[c]
    for t in T: D &= perp(ports[t - V])
    carriers = [r for r in range(V) if ports[r] in D and ports[r] != 0]
    print('centre', c, 'data carriers with p_r in D_c:', carriers[:12], len(carriers))
