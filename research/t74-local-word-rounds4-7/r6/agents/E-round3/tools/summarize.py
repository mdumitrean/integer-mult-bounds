"""summarize.py RUNS_DIR OUT.json: collect every runjob out.json + log into one evidence file."""
import json, sys, re
from pathlib import Path
runs = Path(sys.argv[1]); rows = []
for d in sorted(p for p in runs.iterdir() if p.is_dir()):
    spec = json.load(open(d / 'spec.json')) if (d / 'spec.json').exists() else None
    out = json.load(open(d / 'out.json')) if (d / 'out.json').exists() else []
    log = (d / 'log.txt').read_text() if (d / 'log.txt').exists() else ''
    capped = re.findall(r'\[capped\] exit (\S+) wall (\S+)s peak_rss_gib (\S+)', log)
    for rec in out:
        r1 = rec.get('round1', [])
        rows.append(dict(run=d.name, dels=rec['dels'], ddel=rec.get('ddel'), basis=rec.get('basis'), residual_rank=rec.get('residual_rank'),
                         ncand1=rec.get('ncand1'), shape1=rec.get('shape1'), round1_solutions=len(r1), round1_stop=rec.get('round1_stop'),
                         round1_exact=sum(1 for e in r1 if e.get('exact')), round1_interacting=sum(1 for e in r1 if e.get('interacting')),
                         round2=[dict(ncand2=e.get('ncand2'), shape2=e.get('shape2'), stop=e.get('round2_stop'), solutions=len(e.get('round2', [])),
                                      exact=sum(1 for x in e.get('round2', []) if x.get('exact')),
                                      prices=[x.get('price') for x in e.get('round2', []) if x.get('price')]) for e in r1],
                         round1_prices=[e.get('price') for e in r1 if e.get('price')], seconds=rec.get('seconds'),
                         opts={k: v for k, v in (rec.get('opts') or {}).items()}))
    if not out and spec: rows.append(dict(run=d.name, jobs=spec.get('jobs'), incomplete=True, log_tail=log[-600:]))
    if capped: rows[-1]['capped'] = capped[-1] if rows else None
json.dump(rows, open(sys.argv[2], 'w'), indent=1, default=str); print(len(rows), 'rows')
