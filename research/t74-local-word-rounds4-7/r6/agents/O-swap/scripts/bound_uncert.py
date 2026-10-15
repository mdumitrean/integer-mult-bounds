"""bound_uncert: rigorous lower bounds for the uncertified single narrowings (and so for every swap that uses one): exact
optimal frames with the toolkit's true-moment interval (frames.moment_interval: chain-dual / exact-elimination lower bound),
compared with the base word's interval.  usage: bound_uncert.py TOOLKIT WORD.json.gz UNCERT.json OUT.json"""
import os, sys, json, copy
from fractions import Fraction as Q
sys.path.insert(0, sys.argv[1]); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frames as F, wcore as K
from model import cone_caps
from word import inline
base = K.load(sys.argv[2]); costs = F.Costs(K.B); unit = 1 << costs.unit_bits
def solve_iv(w):
    caps, comp = cone_caps(w); g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    return F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g, interval=True)
rb = solve_iv(base); out = dict(base=dict(cost=rb['cost'], certified=rb['certified'], lower=str(rb['interval']['lower']), upper=str(rb['interval']['upper'])), narrowings=[])
c1 = Q(costs.c[1])
for u in json.load(open(sys.argv[3])):
    w = copy.deepcopy(base); w['start_extra'][str(u['q'])] = u['basis']; r = solve_iv(w)
    # rigorous: no assignment of the narrowed word beats the base's returned assignment by more than max_gain (moment units)
    max_gain = max(Q(0), rb['interval']['upper'] - r['interval']['lower']) * unit
    out['narrowings'].append(dict(q=u['q'], basis=u['basis'], primal_delta=r['cost'] - rb['cost'], certified=r['certified'],
                                  max_gain_units=float(max_gain), max_gain_minus_c1=float(max_gain - c1),
                                  swap_can_gain=bool(max_gain > c1)))
    print(json.dumps(out['narrowings'][-1]), flush=True)
json.dump(out, open(sys.argv[4], 'w'), indent=1)
