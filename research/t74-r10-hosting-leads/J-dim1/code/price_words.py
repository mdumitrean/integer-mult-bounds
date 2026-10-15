"""r10 F-lenders: certified optimal frames (our #1186 toolkit via borrow_price) + pinned PR2679 auditor for built words.
usage: python3 -B price_words.py OUT.json WORD.json.gz [...]   ('literal:' prefix = also validate stored frames)"""
import json, resource, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import borrow_price as bp
OUT = sys.argv[1]; res = json.loads(Path(OUT).read_text()) if Path(OUT).exists() else {}
for arg in sys.argv[2:]:
    lit = arg.startswith('literal:'); p = arg.split(':', 1)[1] if lit else arg
    t0 = time.monotonic(); w = bp.load(p)
    try: pf = bp.frame_profile(w, literal=lit)
    except bp.Infeasible as ex:
        res[p] = dict(status='infeasible', why=str(ex)[:200]); print(p, 'infeasible', flush=True); continue
    wf = bp.write_frames(w, pf); q = p.replace('.json.gz', '.cert.json.gz'); bp.dump(wf, q)
    a = bp.audit(wf, timeout=900)
    r = dict(status='ok' if pf['certified'] else 'uncertified', profile=pf['profile'], cost=str(pf['cost']), eval_profile=w['report'].get('local_profile'),
             audit=a['status'], audit_rc=a['rc'], audit_error=a.get('error'), cert_word=q, seconds=round(time.monotonic() - t0, 1))
    if lit: r['literal_profile'] = pf['literal_profile']
    res[p] = r; Path(OUT).write_text(json.dumps(res, indent=1))
    print(Path(p).name, r['status'], r['profile'], r['audit'], r['audit_error'] or '', r['seconds'], flush=True)
    if resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024 ** 3 > 6: print('RSS cap exit', flush=True); break
