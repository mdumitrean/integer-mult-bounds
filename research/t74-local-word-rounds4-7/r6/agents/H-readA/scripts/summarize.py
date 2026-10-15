"""summarize.py: EVIDENCE.json for agent H-readA from out/PAIRS-*.json, out/CSCREEN*-*.json and out/PK-*.json."""
import glob, json, os, collections
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
pairs = json.load(open('out/PAIRS-base.json'))
ev = dict(agent='H-readA', round='r6', b='0.001679754956125544',
          words=dict(base='r3/inputs/gauge44-word-566-554.json.gz', extra='r3/inputs/extra-word-566-554.json.gz'),
          scope='78 full-c1 (8,1,9) narrowings (r5 C NARROW-base.jsonl, delta -2,116,454) whose helper q is read in A')
P = pairs['pairs']
ev['structure'] = dict(pairs=len(P), helpers=len({p['q'] for p in P}), first_write_in_A=sum(1 for p in P if p['first_write_sec'][0] == 'A'),
                       pure_reads_before_first_write=sum(len(p['pure_reads_A']) for p in P),
                       A_reads_after_first_write=collections.Counter(len(p['reads_A']) for p in P).most_common(),
                       leak_targets=collections.Counter(len(p['leak']) for p in P).most_common())
scr = {}
for f in sorted(glob.glob('out/CSCREEN*-*.json')):
    if 'one' in f: continue
    d = json.load(open(f)); rs = d['results']
    scr[os.path.basename(f)] = dict(pairs=len(rs), pass_admissible=d['pass_admissible'], pass_all_copies=len(d['pass_all_copies']),
                                    errors=d['errors'], max_admissible_columns=max(r['admissible_columns'] for r in rs),
                                    max_rank_admissible=max(r['rank_admissible'] for r in rs))
ev['copy_screen'] = scr
pk = {}
for f in sorted(glob.glob('out/PK-*.json')):
    try: r = json.load(open(f))
    except Exception: continue
    pk[os.path.basename(f)] = {k: r.get(k) for k in ('q', 'u', 'budget', 'narrowed_cost', 'leak_ACB_rows', 'readers', 'target_rank', 'ncand',
                                                    'cone_rejected', 'cost_rejected', 'shape', 'stop', 'seconds')} | dict(proposals=len(r.get('proposals', [])), cuts=len(r.get('cuts', [])))
ev['projected_B_tail_search'] = pk
json.dump(ev, open('EVIDENCE.json', 'w'), indent=1, default=str)
print(json.dumps(ev['structure'])); print(json.dumps(scr)); print(json.dumps(pk, default=str)[:1500])
