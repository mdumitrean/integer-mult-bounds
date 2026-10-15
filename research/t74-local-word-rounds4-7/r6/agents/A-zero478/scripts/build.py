"""build.py: copy-cancellation edit for helper q.  Inserts [c += k*q] for each holder (c, k) right before q's first write in A,
appends cleanup fixes [c -= k*q] at the very end of cleanup, optionally narrows q (start_extra[q] = [u]), then prices with
exact optimal frames (compensation and cone caps re-derived), writes frames back and runs the unchanged auditor.
usage: build.py TOOLKIT MAIN WORD OUTDIR NAME q u narrow(0/1) c:k [c:k ...]"""
import copy, gzip, json, os, sys, subprocess
from fractions import Fraction as Fr
TK, MAINDIR, WORD, OUT, NAME = sys.argv[1:6]; q = int(sys.argv[6]); u = int(sys.argv[7]); narrow = sys.argv[8] == '1'
hold = [(int(a.split(':')[0]), Fr(a.split(':')[1])) for a in sys.argv[9:]]
os.environ['IMB_ROOT'] = MAINDIR; sys.path.insert(0, TK)
import frames as F
from word import inline, recount
from model import cone_caps
from writeback import write_back
B = "0.001679754956125544"
w0 = json.load(gzip.open(WORD)); costs = F.Costs(B)
def solve(w):
    caps, comp = cone_caps(w)
    g = F.Graph(inline(w, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
    r = F.optimal_frames(inline(w, True), costs, check_literal=False, graph=g)
    return r, g, comp
r0, g0, comp0 = solve(w0)
w = copy.deepcopy(w0)
first = 0 if os.environ.get('BUILD_AT0') == '1' else next(i for i, g in enumerate(w['A']) if g[1] == q)
for c, k in reversed(hold): w['A'].insert(first, ['add', c, q, k.numerator, k.denominator, []])
for c, k in hold: w['cleanup'].append(['add', c, q, -k.numerator, k.denominator, []])
if narrow: w['start_extra'][str(q)] = [u]
res = dict(name=NAME, q=q, u=u, narrow=narrow, holders=[[c, str(k)] for c, k in hold], base_cost=r0['cost'], base_profile=dict(sorted(r0['profile'].items())))
try:
    r, g, comp = solve(w)
    res.update(status='ok' if r['certified'] else 'uncertified', cost=r['cost'], delta=r['cost'] - r0['cost'], profile=dict(sorted(r['profile'].items())),
               compensation_gates=len(comp), compensation_reads_q=any(e[2] == q for e in comp))
    w2 = write_back(w, g, r['assign'])
    p = os.path.join(OUT, NAME + '.json.gz'); open(p, 'wb').write(gzip.compress(json.dumps(w2, sort_keys=True).encode(), mtime=0))
    aud = subprocess.run([sys.executable, '-B', os.path.join(MAINDIR, 'research/gauge44-frames-x/independent/audit_local.py'), '--word', p,
                          '--output', os.path.join(OUT, NAME + '.AUDIT.json'), '--main', MAINDIR], capture_output=True, text=True)
    res['audit'] = 'PASS' if aud.returncode == 0 else (aud.stdout + aud.stderr).strip().splitlines()[-1][:300]
except F.Infeasible as e:
    res.update(status='infeasible', why=str(e.args[0])[:300] if e.args else '')
print(json.dumps(res)); json.dump(res, open(os.path.join(OUT, NAME + '.json'), 'w'), indent=1)
