"""build_variants: the 45 equal-cost extra interfaces (3 groups x 15 hyperplanes, r4 D-widths), each built from the base
word with the group's start frames reduced to the hyperplane, exact optimal frames re-solved and written back.
Records cost (must be 11,691,748,602), certificate, profile, inventory and B-frame differences."""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, pool as P
from compat import deadline, Timeout
OUT = os.path.join(os.path.dirname(__file__), '..', 'out'); WORDS = os.path.join(os.path.dirname(__file__), '..', 'words')
G = json.load(open(os.path.join(OUT, 'GROUPS.json')))
BASE = EXTRA = COSTS = BCOST = None
def init():
    global BASE, EXTRA, COSTS, BCOST
    BASE = C.base_word(); EXTRA = C.extra_word(); COSTS = C.F.Costs(C.B); BCOST = C.solve(BASE, COSTS)[0]['cost']
def name_of(v): return v['label'].split(':')[1].replace('..', '-') + '-' + '-'.join(map(str, v['basis']))
def run(v):
    t0 = time.time(); w = C.variant(BASE, v['members'], v['basis'])
    try:
        with deadline(300):
            r, g, caps, comp = C.solve(w, COSTS)
    except Timeout: return dict(v, status='timeout')
    except C.F.Infeasible: return dict(v, status='infeasible')
    w2 = C.write_back(w, g, r['assign'])
    paid, centre, widths, starts, ends, endB = C.W.recount(w2)
    nm = name_of(v); gzip.open(os.path.join(WORDS, nm + '.json.gz'), 'wt').write(json.dumps(w2, sort_keys=True))
    dB_base = [i for i, (x, y) in enumerate(zip(w2['B'], BASE['B'])) if x != y]
    dB_extra = [i for i, (x, y) in enumerate(zip(w2['B'], EXTRA['B'])) if x != y]
    dtail = [i for i, (x, y) in enumerate(zip(w2['early_cleanup'], BASE['early_cleanup'])) if x != y]
    return dict(v, name=nm, status='ok' if r['certified'] else 'uncertified', cost=r['cost'], delta=r['cost'] - BCOST,
                profile=dict(sorted(r['profile'].items())), inventory=w2['report']['width_inventory'], comp_gates=len(comp),
                caps=len(caps), B_diff_base=dB_base, B_diff_extra=len(dB_extra), tail_diff_base=dtail,
                same_as_extra=all(w2[s] == EXTRA[s] for s in ('A', 'cut', 'B', 'cleanup', 'early_cleanup', 'start_extra', 'helper_final')),
                seconds=round(time.time() - t0, 1))
if __name__ == '__main__':
    os.makedirs(WORDS, exist_ok=True); res = []; t0 = time.time()
    def done(r):
        res.append(r); print(len(res), r.get('name'), r.get('status'), r.get('delta'), 'Bdiff', len(r.get('B_diff_base', [])), 'same_as_extra', r.get('same_as_extra'), r.get('seconds'), flush=True)
    killed = P.run_pool(run, G['variants'], workers=4, init=init, maxtasks=12, on_result=done)
    json.dump(dict(results=sorted(res, key=lambda r: r.get('name', '')), killed=killed, seconds=round(time.time() - t0)),
              open(os.path.join(OUT, 'VARIANTS.json'), 'w'), indent=1)
    print('done', len(res), 'killed', killed, f'{time.time()-t0:.0f}s')
