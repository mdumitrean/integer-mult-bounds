"""verify_gain.py WORD OUT.json JOB R1 R2 OUTDIR: rebuild an exact candidate from runjob output and verify it
(exact rational map, exact frames + written-back FULL-WORD, audit_local --main, rev3 harness with interval bounds when all
edits are in B/early tails, kappa estimate at 249/666 calls)."""
import gzip, json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk2 import *
from runjob import exact
R3 = Path(__file__).resolve().parents[3]
word, outp, J, I1, I2, od = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), Path(sys.argv[6])
od.mkdir(parents=True, exist_ok=True); rec = json.load(open(outp))[J]; e1 = rec['round1'][I1]
dels = [tuple(d) for d in rec['dels']]; P = H.Pricer(word); bm = maps(P.base)
W1 = compile_AB(P.base, dict(delete=dels))
mk = lambda gg: list(gg[:5]) + [[]]
if I2 < 0: ins1 = [(p, mk(g)) for p, g in e1['ins1']] if 'ins1' in e1 else None
e2 = e1['round2'][I2] if I2 >= 0 else e1
ins1 = [(p, mk(g)) for p, g in e2['ins1']]; W2 = compile_AB(W1, word_seq_insert(W1, ins1))
W3 = compile_AB(W2, word_seq_insert(W2, [(p, mk(g)) for p, g in e2.get('ins2', [])])) if I2 >= 0 else W2
assert exact(bm, W3), 'not exact'
base_comp = [list(e[:5]) for e in cone_caps(P.base)[1]]
pr = price_word(P, W3, base_comp); res = dict(dels=dels, status=pr['status'], delta=pr.get('delta'), profile=pr.get('profile'))
if pr['status'] in ('ok', 'uncertified'):
    full = write_back(W3, pr['graph'], pr['assign']); fw = od / 'FULL-WORD.json.gz'
    with gzip.open(fw, 'wt') as f: json.dump(full, f)
    rc = subprocess.run([sys.executable, '-I', '-B', str(R3 / 'main/research/gauge44-frames-x/independent/audit_local.py'), '--word', str(fw),
                         '--output', str(od / 'AUDIT.json'), '--main', str(R3 / 'main')], capture_output=True, text=True)
    res['audit_local'] = json.load(open(od / 'AUDIT.json'))['status'] if rc.returncode == 0 else 'FAIL: ' + rc.stdout[-300:] + rc.stderr[-300:]
    # base-relative B / early-tail edits for the rev3 harness
    if all(s == 'B' for s, _ in dels):
        bB, wB = P.base['B'], W3['B']; i = j = 0; ed = dict(delete=[], insert=[], tail=[]); dB = {i_ for s, i_ in dels}
        while i < len(bB) or j < len(wB):
            if i < len(bB) and i in dB: ed['delete'].append(i); i += 1
            elif i < len(bB) and j < len(wB) and list(wB[j][:5]) == list(bB[i][:5]) and wB[j][-1] == bB[i][-1]: i += 1; j += 1
            elif j < len(wB): ed['insert'].append((i, list(wB[j][:5]) + [[]])); j += 1
            else: raise RuntimeError('B alignment')
        nC = len(P.base['cleanup'])
        for k, (ci, U) in enumerate(W3['early_cleanup']):
            if ci >= nC: ed['tail'].append((k, list(W3['cleanup'][ci][:5]) + [[]]))
        if W3['A'] == P.base['A']:
            sys.path.insert(0, str(R3 / 'toolkit-rev3'))
            for m in ('harness', 'frames', 'word', 'model', 'exchange', 'compat', 'writeback'): sys.modules.pop(m, None)
            sys.path = [p for p in sys.path if 'vendor/exact-frame-toolkit' not in p]
            import importlib; H3 = importlib.import_module('harness')
            P3 = H3.Pricer(word, b=os.environ.get('IMB_B'), interval=True); r3 = P3.price(ed, timeout=600)
            res['rev3_harness'] = {k: v for k, v in r3.items() if k != 'word'}; res['rev3_edit'] = ed
units = res.get('delta'); res['kappa_estimate'] = None if units is None else -units * 4.144e-8 / 1855 * 249 / 666
json.dump(res, open(od / 'VERIFY.json', 'w'), indent=1, default=str); print(json.dumps(res, default=str)[:3000])
