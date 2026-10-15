"""inspect_groups: the three (5,9) groups of the base word, their members, early B reads (before each member's first
write), readers, and the 45 equal-cost hyperplane choices from r4 D-widths' JOINT-base.jsonl."""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
w = C.base_word(); paid, centre, widths, starts, ends, endB = C.W.recount(w); v, R = w['report']['v'], w['report']['R']
typ = lambda q: (C.W.dimension(starts[q]), C.W.dimension(ends[q]))
groups = collections.defaultdict(list)
for q in range(2 * v, 2 * v + R):
    if typ(q) == (5, 9): groups[tuple(sorted(w['start_extra'][str(q)]))].append(q)
B = w['B']; first = {}
for i, g in enumerate(B): first.setdefault(g[1], i)
out = {}
for frame, mem in sorted(groups.items(), key=lambda x: x[1][0]):
    reads = [(i, g[1], g[2], g[3]) for i, g in enumerate(B) if g[0] == 'add' and g[2] in mem and i < first.get(g[2], len(B))]
    readers = sorted({t for _, t, _, _ in reads})
    Areads = [(i, g[1], g[2]) for i, g in enumerate(w['A']) if g[0] == 'add' and g[2] in mem]
    Awrites = [(i, g[1]) for i, g in enumerate(w['A']) if g[1] in mem]
    label = f'start:{mem[0]}..{mem[-1]}'
    out[label] = dict(members=mem, start_frame=list(frame), first_writes={q: first.get(q) for q in mem}, early_reads=reads,
                      readers=readers, reader_types={t: typ(t) for t in readers}, A_reads=len(Areads), A_writes=len(Awrites))
    print(label, 'members', mem, 'frame', list(frame)); print('   first writes', out[label]['first_writes'])
    print('   early B reads', len(reads), reads[:16]); print('   readers', readers, {t: typ(t) for t in readers}, 'A reads', len(Areads), 'A writes', len(Awrites))
D = os.path.join(C.SCR, 'r4', 'agents', 'D-widths', 'out', 'JOINT-base.jsonl')
rows = [json.loads(l) for l in open(D) if l.strip()]
eq = [r for r in rows if r.get('label', '').startswith('start:') and r.get('delta') == 8458352]
print('equal-cost variants:', len(eq), collections.Counter(r['label'] for r in eq))
json.dump(dict(groups=out, variants=[dict(label=r['label'], members=r['members'], basis=r['basis']) for r in eq]),
          open(os.path.join(os.path.dirname(__file__), '..', 'out', 'GROUPS.json'), 'w'), indent=1)
