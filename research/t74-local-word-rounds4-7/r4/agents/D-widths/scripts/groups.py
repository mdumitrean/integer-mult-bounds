import gzip, json, sys, collections
sys.path.insert(0, sys.argv[1]); import word as W
w = json.load(gzip.open(sys.argv[2] + '/gauge44-word-566-554.json.gz'))
paid, centre, widths, starts, ends, endB = W.recount(w); v, R = w['report']['v'], w['report']['R']
def typ(q): return (W.dimension(starts[q]), W.dimension(ends[q]))
sel = [q for q in range(2*v, 2*v+R) if typ(q) == (5, 9)]
print('(5,9) helpers:', sel)
for q in sel: print(' ', q, 'start', sorted(w['start_extra'][str(q)]))
# readers/writers of these in A/B before their first write
for q in sel:
    first = next((i for i, g in enumerate(w['B']) if g[1] == q), None)
    readsB = [(i, g[1]) for i, g in enumerate(w['B']) if g[0] == 'add' and g[2] == q and (first is None or i < first)]
    readsA = sum(1 for g in w['A'] if g[0] == 'add' and g[2] == q)
    writesA = sum(1 for g in w['A'] if g[1] == q)
    print(f'  {q}: first B write {first}; early B reads {readsB[:6]}{"..." if len(readsB) > 6 else ""} ({len(readsB)}); A reads {readsA}, A writes {writesA}')
t04 = [q for q in range(2*v, 2*v+R) if typ(q) == (0, 4)]
print('(0,4) helpers:', t04)
print('  their helper_final (first 3):', [(q, sorted(w['helper_final'][str(q)])) for q in t04[:3]])
