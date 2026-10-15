"""summarize.py: collect runs/*/out.json + logs into out/RESULTS.json and print a table."""
import glob, json, os, re, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); rows = []
for d in sorted(glob.glob(os.path.join(D, 'runs', '*'))):
    if not os.path.isdir(d): continue
    name = os.path.basename(d); out = os.path.join(d, 'out.json'); log = os.path.join(d, 'log.txt')
    cap = None
    if os.path.exists(log):
        m = re.search(r'\[capped\] exit (\d+) wall ([\d.]+)s peak_rss_gib ([\d.]+)', open(log).read())
        if m: cap = dict(exit=int(m.group(1)), wall=float(m.group(2)), peak_rss_gib=float(m.group(3)))
    if not os.path.exists(out): rows.append(dict(run=name, status='running' if cap is None else 'no output', capped=cap)); continue
    for r in json.load(open(out)):
        props = []
        for e in r['round1']:
            p = dict(terms=len(e['terms']), interacting=e['interacting'], exact=e['exact'], est=e['est'])
            if 'price' in e: p['price'] = e['price']
            if e.get('round2'): p['round2'] = [dict(terms=len(x['terms']), exact=x['exact'], price=x.get('price')) for x in e['round2']]
            props.append(p)
        gains = [p for p in props if p.get('price', {}).get('delta') is not None and p['price']['delta'] < 0]
        gains += [x for p in props for x in p.get('round2', []) if (x.get('price') or {}).get('delta') is not None and x['price']['delta'] < 0]
        rows.append(dict(run=name, dels=r['dels'], depth=r['opts']['depth'], ban=r['opts']['r1_ban'], ddel=r['ddel'], family_regs=len(r['family_regs']),
                         basis=r['basis'], residual_rank=r['residual_rank'], ncand=r['ncand1'], cone_rejected=r['cone_rejected1'],
                         shape=r['shape1'], gen_seconds=r['gen_seconds1'], proposals=props, r1_stop=r.get('r1_stop'),
                         cone_cuts=len(r.get('r1_cone_cuts', [])), gains=gains, seconds=r['seconds'], capped=cap))
json.dump(rows, open(os.path.join(D, 'out', 'RESULTS.json'), 'w'), indent=1, default=str)
for x in rows:
    if 'dels' not in x: print(x['run'], x['status']); continue
    print(f"{x['run']:10s} ddel {x['ddel']:7d} fam {x['family_regs']:3d} basis {x['basis']:3d} cand {x['ncand']:6d} shape {x['shape']!s:5s} "
          f"props {len(x['proposals'])} exact {sum(p['exact'] for p in x['proposals'])} stop {x['r1_stop']} cone-cuts {x['cone_cuts']} "
          f"gains {len(x['gains'])} {x['seconds']}s")
