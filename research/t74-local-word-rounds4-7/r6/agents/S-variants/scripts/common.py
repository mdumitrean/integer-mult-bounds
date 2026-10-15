"""common: shared helpers for S-variants (r6).  Paths are relative to scratchpad/ (set SCR to the scratchpad root)."""
import copy, gzip, json, os, sys, time
SCR = os.environ.get('SCR') or os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
TK = os.path.join(SCR, 'r3', 'toolkit-rev3')
os.environ.setdefault('IMB_ROOT', os.path.join(SCR, 'r3', 'main'))
if TK not in sys.path: sys.path.insert(0, TK)
import frames as F, word as W
from word import inline
from model import cone_caps
from writeback import write_back
B = "0.001679754956125544"
INP = os.path.join(SCR, 'r3', 'inputs')
def load(p): return json.load(gzip.open(p))
def base_word(): return load(os.path.join(INP, 'gauge44-word-566-554.json.gz'))
def extra_word(): return load(os.path.join(INP, 'extra-word-566-554.json.gz'))
def solve(w, costs):
    caps, comp = cone_caps(w)
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
    return r, g, caps, comp
def variant(base, members, basis):
    w = copy.deepcopy(base)
    for q in members: w['start_extra'][str(q)] = list(basis)
    return w
