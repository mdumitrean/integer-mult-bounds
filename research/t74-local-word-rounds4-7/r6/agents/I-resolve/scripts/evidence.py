"""evidence.py: aggregate I-resolve's runs into EVIDENCE.json (paths relative to scratchpad/r6/agents/I-resolve)."""
import json
R = 'runs'
def J(p):
    try: return json.load(open(p))
    except Exception: return None
def rgsum(rg, vf):
    return dict(status=rg['status'], iterations=rg['iterations'], final_rows=len(rg.get('final_K') or []), final_cand=len(rg.get('final_cand') or []),
                excluded=len(rg.get('excluded') or []), proposals=len(rg['proposals']), seconds=rg['seconds'], verify=(vf or {}).get('checks'), log=rg['log'])
ev = dict(agent='I-resolve', round='r6', b='0.001679754956125544', word='r3/inputs/gauge44-word-566-554.json.gz',
          model='D-depth2 round-1 depth-2 split-key model (gen2.FastRound, cone-aware candidates, per-insert cap = budget = deletion gain - 1, quarter-step |lambda|<=4, <=12 inserts, PR2142 direct interaction ban)',
          variants={'D': "D-depth2's candidate set exactly (oracle-sentinel 2^60 candidates excluded by its cap)",
                    'C': 'corrected: each sentinel candidate priced exactly as a standalone insert into the deleted word (rigorous frame lower bound); kept at that cost if <= budget, excluded if provably over budget',
                    'A': 'no per-insert cap and all costs 0 (no oracle information); diagnostic only'},
          method='row generation (scripts/rowgen.py): restricted equation set K (start: the 18 nonzero target rows), candidates touching K, interaction ban, cardinality and budget; an all-rows-exact solution is a proposal, otherwise its violated rows join K; INFEASIBLE on a restriction proves the full model infeasible. Final restricted models re-solved independently as MIPs (scripts/verify_small.py: HiGHS, and SCIP where it finished in 240 s).')
cal = {}
for name, d in (('B783_D_negative_control', 'rgb-cal783'), ('k554_positive_control', 'rgb-k554')):
    cal[name] = rgsum(J(f'{R}/{d}/ROWGEN.json'), J(f'{R}/{d}/VERIFY.json'))
cal['k554_positive_control']['first_proposal'] = '122 += 554, 126 += 554, 186 -= 554, 74 -= 554 (x2) = k554-signed-001'
cal['lp_relaxation_B783_D'] = J(f'{R}/cal-783D/out.json')['phase1']
cal['lp_relaxation_k554'] = J(f'{R}/cal-k554/out.json')['phase1']
ev['calibration'] = cal
tg = {}
for t in (822, 840, 858, 876):
    s = J(f'{R}/s{t}/SENTINEL.json')
    rec = dict(ddel=s['ddel'], budget=s['bud'], sentinel=dict(n=s['n_sentinel'], within_budget=s['within_budget'], provably_over_budget=s['provably_over_budget'],
               statuses=s['status_counts'], relocations=s['relocations'],
               cheap=[(r_['x'], r_['y'], r_['p'], r_.get('lower')) for r_ in s['rows'] if not r_['provably_over_budget']]))
    for v in ('D', 'C'): rec[v] = rgsum(J(f'{R}/rg{t}{v}/ROWGEN.json'), J(f'{R}/rg{t}{v}/VERIFY.json'))
    tg[f'B{t}'] = rec
ev['targets'] = tg
pa = J(f'{R}/rg822A/PRICED.json'); rga = J(f'{R}/rg822A/ROWGEN.json')
ev['B822_variant_A'] = dict(status=rga['status'], iterations=rga['iterations'], exact_proposals=pa['proposals'])
ev['gains'] = []
json.dump(ev, open('EVIDENCE.json', 'w'), indent=1, default=str); print('EVIDENCE.json written')
for t, r in tg.items(): print(t, 'D', r['D']['status'], r['D']['final_rows'], r['D']['final_cand'], [c['solver'] + ':' + c['status'] for c in (r['D']['verify'] or [])], '| C', r['C']['status'], r['C']['final_rows'], r['C']['final_cand'], [c['solver'] + ':' + c['status'] for c in (r['C']['verify'] or [])])
print('cal', {k: (v.get('status') if isinstance(v, dict) else v) for k, v in cal.items()})
