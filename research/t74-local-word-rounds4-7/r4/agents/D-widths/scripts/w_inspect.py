import gzip, json, sys, collections
sys.path.insert(0, sys.argv[1])
import frames as F, word as W
B = "0.001679754956125544"
costs = F.Costs(B)
print('unit_bits', costs.unit_bits, 'c[1..9]:', [costs.c[r] for r in range(1, 10)])
print('marginal c[r+1]-c[r]:', [costs.c[r+1] - costs.c[r] for r in range(1, 9)])
for name in ('gauge44', 'extra'):
    w = json.load(gzip.open(sys.argv[2] + f'/{name}-word-566-554.json.gz'))
    paid, centre, widths, starts, ends, endB = W.recount(w)
    v, R = w['report']['v'], w['report']['R']
    inv = collections.Counter(widths)
    print(name, 'R', R, 'inventory', dict(sorted(inv.items())), 'paid', dict(sorted(paid.items())), 'centre', dict(centre))
    sd = collections.Counter((W.dimension(starts[q]), W.dimension(ends[q])) for q in range(2*v, 2*v+R))
    print('  (startdim,enddim) counts:', dict(sorted(sd.items())))
    print('  start_extra regs', len(w['start_extra']), 'helper_final regs', len(w['helper_final']), 'target_levels', len(w.get('target_levels', {})), 'centers', len(w['centers']))
    if name == 'gauge44': base = (w, widths, starts, ends)
    else:
        diff = [q for q in range(2*v, 2*v+R) if widths[q-2*v] != base[1][q-2*v] or starts[q] != base[2][q] or ends[q] != base[3][q]]
        print('  helpers whose start/end/width differ from base:', diff, [(base[1][q-2*v], widths[q-2*v]) for q in diff])
        for q in diff[:4]: print('   ', q, 'base start', sorted(base[0]['start_extra'].get(str(q), [])), 'extra start', sorted(w['start_extra'].get(str(q), [])))
