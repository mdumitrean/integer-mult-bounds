"""classes.py: large B-deletion classes on the 566+554 words (from r3 A's extra-word relaxation; same program on base),
with gate shapes, excluding targets already searched by r5 D-compsplit.  usage: classes.py OUT.json"""
import json, gzip, sys, glob, collections
S = '.'
V = 112
rel = json.load(open(S + '/r3/agents/A-extra/out/relax-extra.json'))['results']
base = json.load(gzip.open(S + '/r3/inputs/gauge44-word-566-554.json.gz'))
B = base['B']; ent = set(map(int, base['start_extra'])); low = set(map(int, base['helper_final']))
done = set()
for f in glob.glob(S + '/r5/agents/D-compsplit/out/RUN-*.json'):
    try:
        for rec in json.load(open(f)):
            for s, i in rec['dels']: done.add((s, i))
    except Exception: pass
def kind(r):
    if r < V: return 'D'
    if r < 2 * V: return 'P'
    return 'E' if r in ent else ('L' if r in low else 'H')
first_write = {}
for i, g in enumerate(B): first_write.setdefault(g[1], i)
cls = collections.defaultdict(list)
for k, e in rel.items():
    d = e.get('delta')
    if isinstance(d, (int, float)) and d <= -9592: cls[d].append(int(k))
out = []
for d in sorted(cls):
    mem = sorted(cls[d]); shapes = collections.defaultdict(list)
    for i in mem:
        g = B[i]
        if g[0] == 'add':
            t, s = g[1], g[2]; c = (g[3], g[4])
            early = i < first_write.get(s, 10 ** 9)
            sh = ('add', kind(t), kind(s), c, 'early' if early else 'late')
        else: sh = ('scale', kind(g[1]), (g[2], g[3]))
        shapes[sh].append(i)
    rec = dict(delta=d, n=len(mem), members=mem, searched=[i for i in mem if ('B', i) in done],
               shapes=[dict(shape=list(map(str, k)), members=v, rep=v[0], gate=B[v[0]][:5]) for k, v in shapes.items()])
    out.append(rec)
    print(d, len(mem), 'searched', len(rec['searched']), '|', ' ; '.join(f"{'/'.join(map(str, k))} x{len(v)} rep B{v[0]} {B[v[0]][:5]}" for k, v in shapes.items()))
json.dump(out, open(sys.argv[1], 'w'), indent=1, default=str)
