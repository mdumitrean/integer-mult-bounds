"""report.py: write REPORT.md for agent M-bigB from out/EVIDENCE.json (run summarize.py first)."""
import json, os, collections
M = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev = json.load(open(os.path.join(M, 'out', 'EVIDENCE.json'))); jobs = json.load(open(os.path.join(M, 'out', 'JOBS.json')))
main_rows = [r for r in ev['rows'] if not r['rerun'] and not r['nobans'] and not r.get('rowgen') and r['run'] not in {'B%d' % k for k in json.load(open(os.path.join(M, 'out', 'POOL.json')))['skipped']}]
done_reps = {r['rep'] for r in main_rows}
bycls = collections.defaultdict(list)
for r in main_rows: bycls[r['delta_class']].append(r)
reruns = [r for r in ev['rows'] if r['rerun']]
pr = collections.defaultdict(list)
for p in ev['priced']: pr[p['dels'][0][1]].append(p)
L = []
L.append('# r6 / M-bigB: compensation census for the large B-deletion classes (566+554 base word)\n')
L.append('Agent M-bigB (round r6, 2026-10-15, start 06:08Z). Word `r3/inputs/gauge44-word-566-554.json.gz` (#1672 blob 76c01583),'
         ' b = 0.001679754956125544. Local only: no commits, pushes or posts.\n')
L.append(f"**Outcome: no gain (κ unchanged).** {len(main_rows)} of {len(jobs)} class/shape representatives searched;"
         f" status counts {dict(collections.Counter(r['status'] for r in main_rows))}; {len(ev['priced'])} exact proposals priced,"
         f" {len(ev['gains'])} with a negative delta.\n")
vals = sorted({q['delta'] for q in ev['priced'] if isinstance(q['delta'], (int, float))})
unk = [r for r in main_rows if 'UNKNOWN' in r['status']]
L.append(f"Every exact proposal prices at Δ >= 0 (distinct values {vals}): the Δ = 0 ones are neutral alternatives, the others"
         " cost more than the deletion saves. No negative delta arose, so no gain_certified interval, audit_local.py or native"
         " chain run was needed. Time-limited: " + ', '.join(f"B{r['rep']} ({r['ddel']}, {r['ncand']} candidates)" for r in unk) + '.\n')
L.append('## Model\n')
L.append('- r5 D-compsplit\'s projected split-key model (`sk3.PRound`, driver `run3.py`), unchanged except candidate generation'
         ' (`scripts/sk5.py`, driver `scripts/run5.py`): inserts anywhere in B or the early tail, quarter-step |λ| <= 4, <= 12 inserts,'
         ' budget |gain| - 1 (#1957 oracle), r3 B\'s exact single-insert cone test, compensation re-derived (port-row ordinary-helper'
         ' columns projected out), direct exactness and frame checks with lazy cuts, exact proposals priced by r5 D\'s `price3.py`.')
L.append('- **Sentinels:** an insert the #1957 oracle prices at INF (2^60) is never pruned by cost. If it passes the cone test it is'
         ' kept at cost 0 (optimistic lower bound), so INFEASIBLE / shape-infeasible remain proofs within the model. In these'
         ' large-deletion models sentinels are most of the candidates (thousands to tens of thousands per job): every earlier'
         ' cost-pruned run dropped them.')
L.append('- **Re-insertion ban:** inserts re-reading the deleted (target, source) pair are excluded (`ban_reinsert`). Without the ban'
         ' (control run B1061, `runs/RUN-t1061.json`) the cheapest exact solutions are pure relocations of the deleted read,'
         ' which #1957\'s 4,461-move census and r3 D\'s re-timing families already price at >= 0.')
L.append('- **Structural reruns:** for jobs whose first proposals are variants of one structure, `pair_nogood` forbids the same set'
         ' of (x, y) pairs so each further proposal is structurally different (K = 8).')
L.append('- **Calibration:** on #1672\'s pivot-566-only word, deleting B342 returns k554 in three equivalent 5-insert placements'
         ' (`runs/RUN-calib.json`), as in r5 D.\n')
L.append('## Per class (representative per gate shape; `out/TABLE.md` has every job)\n')
L.append('| Class Δ | Members | Reps run | Status of reps | Priced proposals |')
L.append('|---:|---:|---:|---|---|')
for d in sorted(bycls):
    rs = bycls[d]; n = sum(j['n_members'] for j in jobs if j['delta'] == d)
    st = dict(collections.Counter(r['status'] for r in rs))
    pp = [f"B{r['rep']}: " + ', '.join(sorted({str(p['delta']) for p in pr.get(r['rep'], [])})) for r in rs if pr.get(r['rep'])]
    L.append(f"| {d} | {n} | {len(rs)} of {sum(1 for j in jobs if j['delta'] == d)} | {st} | {'; '.join(pp) or '-'} |")
if reruns:
    L.append('\n**Structural reruns** (`pair_nogood`, K = 8):\n')
    for r in reruns:
        L.append(f"- {r['run']} (Δdel {r['ddel']}): {r['proposals']} proposal(s), then {r['stop']}; prices "
                 f"{sorted({p['delta'] for p in ev['priced'] if p['file'] == 'PRICED-' + r['run'] + '.json'})}.")
missing = [j for j in jobs if j['rep'] not in done_reps]
L.append(f"\n**Not run (time):** {len(missing)} representatives: " + ', '.join(f"B{j['rep']} ({j['delta']})" for j in missing[:60]) + ('...' if len(missing) > 60 else ''))
L.append('\n**Remaining:** structural reruns (`pair_nogood`) of the Δ = 0 proposal jobs, the time-limited jobs with a longer'
         ' limit, the unrun representatives above, and A-section inserts.')
pool = json.load(open(os.path.join(M, 'out', 'POOL.json')))
fu_b = [x for x in ev['rows'] if x['run'] in {'B%d' % k for k in pool['skipped']}]
fu_r = [x for x in ev['rows'] if x['run'] in {'R%d' % k for k in pool['zero']}]
def pv(run): return sorted({q_['delta'] for q_ in ev['priced'] if q_['file'] == 'PRICED-' + run + '.json'})
L.append('\n## Follow-up (07:30-08:30Z): skipped representatives, Δ = 0 reruns, timeouts\n')
L.append(f"- **Skipped representatives:** {len(fu_b)} of {len(pool['skipped'])} run; outcomes {dict(collections.Counter(x['status'] for x in fu_b))};"
         f" priced deltas {sorted({d for x in fu_b for d in pv(x['run'])})}.")
L.append(f"- **Δ = 0 reruns** (`pair_nogood`, K = 8): {len(fu_r)} of {len(pool['zero'])} run; stop states {dict(collections.Counter(str(x['stop']) for x in fu_r))};"
         f" priced deltas {sorted({d for x in fu_r for d in pv(x['run'])})}.")
for b in (975, 1180):
    rg = json.load(open(os.path.join(M, 'runs', f'RG-B{b}.json'))) if os.path.exists(os.path.join(M, 'runs', f'RG-B{b}.json')) else None
    chk = json.load(open(os.path.join(M, 'runs', f'RUN-RG{b}-checks.json'))) if os.path.exists(os.path.join(M, 'runs', f'RUN-RG{b}-checks.json')) else []
    if rg:
        L.append(f"- **B{b} (timeout) via r6 I-resolve's row generation** (`scripts/export_sys.py` + I's `rowgen.py`, ROWGEN_BAN=0):"
                 f" {rg['status']} after {rg['iterations']} iterations, {len(rg['proposals'])} first-order proposals;"
                 f" {sum(1 for c in chk if c.get('exact') and c.get('frames_ok'))} pass full exactness + frames; priced deltas {pv('RG%d' % b)}."
                 " Positive control: B949's exported system yields its known window solutions (`runs/RG-B949.json`).")
L.append('\n## Scope\n')
L.append('- Base word only (the extra word shares the gate sequence, r3 A). One representative per (class, gate shape); members of a'
         ' shape were assumed equivalent, not proven. First order with exact checks, one round, <= 12 inserts, |λ| <= 4 in quarter'
         ' steps, B/tail inserts only (no A-section inserts), deleted pair not re-read, at most K proposals and 15-20 cuts per job.')
L.append('- INFEASIBLE / shape-infeasible are proofs within this model (sentinels optimistic at 0), not supplier lower bounds.'
         ' Jobs that stopped on a time or cut limit are reported as such.\n')
L.append('## Evidence\n')
L.append('`out/EVIDENCE.json` (every job, priced proposals, gains), `out/TABLE.md`, `out/CLASSES.json`, `out/JOBS.json`,'
         ' `out/LANES.json`; `runs/RUN-*.json`, `runs/*.cap.log` (solver logs), `runs/PRICED-*.json`; scripts in `scripts/`'
         ' (sk5.py, run5.py, queue.sh, lane3b.sh, classes.py, summarize.py, report.py). Files in `runs/` whose names contain spaces'
         ' come from a first launch whose lane arguments were not split; they hold no results.\n')
L.append('Prepared with substantial AI assistance (Anthropic Claude, via Claude Code).')
open(os.path.join(M, 'REPORT.md'), 'w').write('\n'.join(L) + '\n'); print('REPORT.md written')
