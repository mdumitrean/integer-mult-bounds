"""table.py RESULTS.json: markdown table of every job."""
import json, sys
rows = json.load(open(sys.argv[1])); out = ['| Run | Deletions | Relaxation (units) | Basis / residual rank | Round-1 candidates | Shape | Round 1 | Round 2 (repair) | Exact priced | Gain |', '|---|---|---:|---|---:|---|---|---|---|---|']
for r in rows:
    if r.get('incomplete'): out.append(f"| {r['run']} | {r.get('jobs')} | | | | | incomplete | | | |"); continue
    dels = '+'.join(f'{s}{i}' for s, i in r['dels']); o = r.get('opts', {})
    r1 = f"{r['round1_solutions']} proposals ({r['round1_interacting']} interacting), then {r.get('round1_stop') or 'K reached'}"
    r2 = '; '.join(f"{x['ncand2']} cand: {x['solutions']} sol / {x['exact']} exact, {x['stop'] or 'K reached'}" for x in r['round2'] if x.get('ncand2') is not None) or '-'
    pr = [p for p in r['round1_prices']] + [p for x in r['round2'] for p in x['prices']]
    prs = ', '.join(f"{p.get('status')} {p.get('delta', '')}" for p in pr) or '-'
    gain = 'yes' if any(p.get('delta') is not None and p['delta'] < 0 for p in pr) else 'no'
    tag = f"{r['run']} (lam/{o.get('lam_den', 2)}, ban {o.get('r1_ban')}{', no budget r2' if o.get('r2_nobud') else ''}{', depth ' + str(o.get('depth')) if o.get('depth', 1) != 1 else ''})"
    out.append(f"| {tag} | {dels} | {r['ddel']} | {r['basis']} / {r['residual_rank']} | {r['ncand1']} | {r['shape1']} | {r1} | {r2} | {prs} | {gain} |")
print('\n'.join(out))
