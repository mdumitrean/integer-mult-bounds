"""Full checks for one priced alternative (JSON line on argv[1]): interval re-price (gain_certified), edited word written,
unchanged audit_local.py --main, toolkit native chain, and the same edit on the extra word."""
import os, sys, json, gzip, subprocess, time
from fractions import Fraction as Q
S = os.environ['SCR']; sys.path.insert(0, S + '/r3/toolkit-rev3')
import harness as H
r = json.loads(sys.argv[1]); tag = f"w{r['i']}k{r['k']}"; OUT = S + '/r6/agents/P-peephole/out/verify/' + tag; os.makedirs(OUT, exist_ok=True)
def gate(t):
    if t[0] == 'add': c = Q(t[3]); return ['add', t[1], t[2], c.numerator, c.denominator, []]
    c = Q(t[2]); return ['scale', t[1], c.numerator, c.denominator, []]
ed = dict(delete=list(range(r['i'], r['i'] + r['k'])), insert=[[r['i'], gate(t)] for t in r['alt']])
res = {}
for name, word in (('base', 'gauge44-word-566-554.json.gz'), ('extra', 'extra-word-566-554.json.gz')):
    Pr = H.Pricer(S + '/r3/inputs/' + word, b='0.001679754956125544', check_literal=True, interval=True)
    p = Pr.price(ed, want_word=True, timeout=300); wd = p.pop('word', None)
    res[name] = {k: v for k, v in p.items() if k not in ('why',)}
    if wd is not None:
        fn = f'{OUT}/{name}.json.gz'; json.dump(wd, gzip.open(fn, 'wt'))
        a = subprocess.run([sys.executable, '-B', S + '/r3/main/research/gauge44-frames-x/independent/audit_local.py', '--word', fn,
                            '--output', fn + '.audit.json', '--main', S + '/r3/main'], cwd=S + '/r3/main', capture_output=True, text=True)
        res[name]['audit_local'] = json.load(open(fn + '.audit.json')).get('status') if a.returncode == 0 else 'FAIL ' + (a.stdout + a.stderr)[-300:]
        if name == 'base':
            n = subprocess.run([sys.executable, '-B', S + '/r3/toolkit-rev3/native.py', fn, OUT + '/native'], capture_output=True, text=True,
                               env=dict(os.environ, IMB_ROOT=S + '/r3/main'))
            res[name]['native'] = 'PASS' if n.returncode == 0 else 'FAIL ' + (n.stdout + n.stderr)[-400:]
json.dump(dict(record=r, checks=res), open(OUT + '/VERIFY.json', 'w'), indent=1, default=str); print(json.dumps(res, default=str)[:1500])
