"""price3.py: price run3.py's exact proposals with the rev3 toolkit's compensation-aware option (absorb.py).
usage: price3.py WORD RUN3-OUT.json PRICED.json [AUDITDIR]"""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from absorb import AbsorbPricer
word, inp, outp = sys.argv[1:4]; adir = sys.argv[4] if len(sys.argv) > 4 else None
P = AbsorbPricer(word, check_literal=True, interval=True); res = []
for ji, rec in enumerate(json.load(open(inp))):
    for pi, e in enumerate(rec['proposals']):
        ad = os.path.join(adir, f'j{ji}p{pi}') if adir else None; t0 = time.time()
        if e.get('edit_ab'):
            x = e['edit_ab']; ed = dict(delete=[tuple(d) for d in x['delete']], insert=[(s, p, g) for s, p, g in x['insert']], tail=[(j, g) for j, g in x['tail']])
            pr = P.price_ab(ed, audit_dir=ad)
        elif e.get('edit'):
            x = e['edit']; ed = dict(delete=list(x['delete']), insert=[(p, g) for p, g in x['insert']], tail=[(j, g) for j, g in x['tail']])
            pr = P.price_absorb(ed, audit_dir=ad)
        else: continue
        pr = {k: v for k, v in pr.items() if k != 'word'}; pr['seconds'] = round(time.time() - t0, 1)
        res.append(dict(job=ji, dels=rec['dels'], proposal=pi, terms=e['terms'], est=e['est'], price=pr))
        print(ji, rec['dels'], pi, pr.get('status'), pr.get('delta'), pr.get('comp_gates'), pr.get('audit', {}).get('status') if pr.get('audit') else '', flush=True)
json.dump(res, open(outp, 'w'), indent=1, default=str); print('priced', len(res))
