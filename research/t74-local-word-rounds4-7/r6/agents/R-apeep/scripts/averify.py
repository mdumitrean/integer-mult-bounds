"""averify.py: full checks for one priced A-window alternative (a JSON line on argv[1]): interval re-price (gain_certified),
edited word written, the unchanged audit_local.py --main, the toolkit native chain (base word), and the same edit on the
extra word (same program; r3 A-extra).  Writes out/verify/<tag>/VERIFY.json."""
import os, sys, json, gzip, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import absorb, aprice
r = json.loads(sys.argv[1]); tag = f"A{r['i']}k{r['k']}"; OUT = os.path.join(HERE, '..', 'out', 'verify', tag); os.makedirs(OUT, exist_ok=True)
res = {}
for name, word in (('base', 'gauge44-word-566-554.json.gz'), ('extra', 'extra-word-566-554.json.gz')):
    Pr = absorb.AbsorbPricer(os.path.join(absorb.SCR, 'r3/inputs', word), b=aprice.B_, check_literal=True, interval=True)
    p = Pr.price_ab(aprice.edit(r), want_word=True, timeout=300, audit_dir=os.path.join(OUT, name + '-audit'))
    wd = p.pop('word', None); res[name] = p
    if wd is not None and name == 'base':
        fn = os.path.join(OUT, 'base.json.gz'); open(fn, 'wb').write(gzip.compress(json.dumps(wd).encode(), mtime=0))
        n = subprocess.run([sys.executable, '-B', os.path.join(HERE, '..', 'toolkit', 'native.py'), fn, os.path.join(OUT, 'native')],
                           capture_output=True, text=True, env=dict(os.environ, IMB_ROOT=absorb.MAIN))
        res[name]['native'] = 'PASS' if n.returncode == 0 else 'FAIL ' + (n.stdout + n.stderr)[-400:]
json.dump(dict(record=r, checks=res), open(os.path.join(OUT, 'VERIFY.json'), 'w'), indent=1, default=str); print(json.dumps(res, default=str)[:2000])
