"""price16.py: exact optimal frames of each rebuilt word with tail caps on (toolkit default) and off (end-of-B caps only).
usage: price16.py TOOLKIT BASE_WORD WORDS_DIR OUT.json"""
import gzip, json, os, sys, time
sys.path.insert(0, sys.argv[1])
import frames as F
from word import inline
from model import cone_caps
base_path, wdir, outp = sys.argv[2:5]
costs = F.Costs("0.001679754956125544")
def price(w, tc):
    caps, comp = cone_caps(w)
    try:
        g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True, tail_caps=tc)
        r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g, interval=True)
        return dict(status='ok' if r['certified'] else 'uncertified', cost=r['cost'], profile=dict(sorted(r['profile'].items())),
                    interval=[str(r['interval']['lower']), str(r['interval']['upper'])]), comp
    except F.Infeasible as e: return dict(status='infeasible', why=str(e.args[0])[:160]), comp
base = json.load(gzip.open(base_path)); b0, comp0 = price(base, True); b1, _ = price(base, False)
assert b0['cost'] == b1['cost']; base_cost = b0['cost']; print('base', base_cost, b0['profile'], flush=True)
out = dict(base=b0)
for row in json.load(open(os.path.join(wdir, 'INDEX.json'))):
    w = json.load(gzip.open(os.path.join(wdir, row['name'])))
    on, comp = price(w, True); off, _ = price(w, False)
    for x in (on, off):
        if 'cost' in x: x['delta'] = x['cost'] - base_cost
    row.update(tail_caps=on, endB_caps_only=off, compensation_same=[e[:5] for e in comp] == [e[:5] for e in comp0])
    out[row['name']] = row
    print(row['name'], 'ON', on['status'], on.get('delta', on.get('why', ''))[:90] if isinstance(on.get('delta', on.get('why')), str) else on.get('delta'),
          '| OFF', off['status'], off.get('delta', off.get('why', '')), '| comp same', row['compensation_same'], flush=True)
json.dump(out, open(outp, 'w'), indent=1)
