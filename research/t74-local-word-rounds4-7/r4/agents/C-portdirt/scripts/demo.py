"""demo.py: semantics demonstration of a compensation-absorbed edit.  Insert t += h (t a port, h an ORDINARY helper that
still holds only its initial value, so the read is pure ordinary dirt) at a B position where agent B's exact single-insert
cone test passes on the base word.  The A+cut+B map changes only in port row t, column h; the re-derived compensation
gains one gate (t, h); the frames are re-solved; the word is written back and checked by the unchanged audit_local.py
(with --main), which derives the compensation itself.  usage: demo.py WORD.json.gz OUTDIR [MAX_TRIES]"""
import json, os, sys, gzip, subprocess
from fractions import Fraction as Fr
HERE = os.path.dirname(os.path.abspath(__file__)); SCR = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(SCR, 'r3', 'toolkit-rev3')); sys.path.insert(1, HERE)
MAIN = os.path.join(SCR, 'r3', 'main'); os.environ.setdefault('IMB_ROOT', MAIN); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from conelu import LU
from writeback import write_back
P = H.Pricer(sys.argv[1], check_literal=True, interval=True); w = P.base; out = sys.argv[2]; os.makedirs(out, exist_ok=True)
V = w['report']['v']; n = 2 * V + w['report']['R']; NA, NC = len(w['A']), len(w['cut'])
ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
ordn = [k for k in range(2 * V, n) if k not in ent and k not in low]
seq = w['A'] + w['cut'] + w['B']
first_write = {}
for j, e in enumerate(seq): first_write.setdefault(e[1], j)
lu = LU(P, w); tries = 0; found = None
for p in range(0, len(w['B']) + 1, 7):
    sp = NA + NC + p
    for h in ordn:
        if first_write.get(h, 10 ** 9) < sp: continue          # h must still hold only its initial value
        for t in range(V, 2 * V):
            if lu.ok(t, h, sp):
                found = (t, h, p); break
        if found: break
    if found: break
print('candidate insert', found, flush=True)
t, h, p = found
w1 = H.compile_edits(w, dict(delete=[], insert=[(p, ['add', t, h, 1, 1, []])]))
assert H.program_violation(w1) is None
caps, comp = cone_caps(w1)
newg = [e[:5] for e in comp if [x for x in e[:5]] not in [list(c[:5]) for c in P.compensation]]
g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
r = F.optimal_frames(inline(w1, True), P.costs, check_literal=False, graph=g, interval=True)
word = write_back(w1, g, r['assign'])
pth = os.path.join(out, 'DEMO-WORD.json.gz'); open(pth, 'wb').write(gzip.compress(json.dumps(word, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
aud = os.path.join(MAIN, 'research/gauge44-frames-x/independent/audit_local.py')
rc = subprocess.run([sys.executable, '-B', aud, '--word', pth, '--output', os.path.join(out, 'DEMO-AUDIT.json'), '--main', MAIN],
                    capture_output=True, text=True)
rec = dict(insert=dict(t=t, h=h, before_B=p), comp_gates_base=len(P.compensation), comp_gates_new=len(comp),
           new_comp_gates=newg, caps_changed=caps != P.caps, delta=r['cost'] - P.base_cost, certified=r['certified'],
           profile=dict(sorted(r['profile'].items())), audit_exit=rc.returncode, audit_tail=(rc.stdout + rc.stderr).strip().splitlines()[-3:])
if rc.returncode == 0:
    a = json.load(open(os.path.join(out, 'DEMO-AUDIT.json'))); rec['audit_status'] = a['status']; rec['audit_compensation_gates'] = a['compensation_gates']
json.dump(rec, open(os.path.join(out, 'DEMO.json'), 'w'), indent=1); print(json.dumps(rec, indent=1))
