"""Collect r3's exact pre-moves on the base word (neutral and small-positive), with their known deltas.  -> out/PREMOVES.json"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__)); import common
R3A = os.path.join(common.R3, 'agents'); out = []
def jl(p): return [json.loads(l) for l in open(p) if l.strip()]
# D: compensated single-crossing re-timings (base) and multi-crossing moves
cands = {c['id']: c for c in json.load(open(os.path.join(R3A, 'D-families/out/CMOVE-cands.json')))}
for r in jl(os.path.join(R3A, 'D-families/out/CMOVE-base.jsonl')):
    if r.get('status') == 'ok': out.append(dict(id='D1:' + r['id'], src='D-cmove', delta1=r['delta'], ed=cands[r['id']]['ed']))
cm = {c['id']: c for c in json.load(open(os.path.join(R3A, 'D-families/out/CMULTI-cands.json')))}
for r in jl(os.path.join(R3A, 'D-families/out/CMULTI-base.jsonl')):
    if r.get('status') == 'ok': out.append(dict(id='D2:' + r['id'], src='D-cmulti', delta1=r['delta'], ed=cm[r['id']]['ed']))
# D: two-column (copy-window) edits priced ok on base
tp = {c['id']: c for c in json.load(open(os.path.join(R3A, 'D-families/out/TS-prio.json')))}
for r in jl(os.path.join(R3A, 'D-families/out/TS-base.jsonl')):
    if r.get('status') == 'ok' and r['id'] in tp: out.append(dict(id='D3:' + r['id'], src='D-twocol', delta1=r['delta'], ed=tp[r['id']]['ed']))
# C: feasible fusions without repair steps, and feasible position classes (base)
for i, x in enumerate(json.load(open(os.path.join(R3A, 'C-repair/runs/repair-gauge44.json')))):
    b = x.get('best')
    if b and not b['steps']: out.append(dict(id=f"C1:{i}:t{x['t']}A{x['A']}H{x['H']}p{x['p']}{x['rest']}", src='C-fusion', delta1=b['delta'], ed=x['ed']))
for i, x in enumerate(json.load(open(os.path.join(R3A, 'C-repair/runs/pos-gauge44.json')))):
    p = x.get('price', {})
    if p.get('status') == 'ok': out.append(dict(id=f"C2:{i}:t{x['t']}A{x['A']}H{x['H']}p{x['p']}{x['rest']}", src='C-fuspos', delta1=p['delta'], ed=x['ed']))
# A: exact relocations of the width-interface reads (priced on extra; same gate program on base, delta re-priced later)
a = json.load(open(os.path.join(R3A, 'A-extra/out/jointmove-extra.json')))
for i, x in enumerate(a['results']):
    if x.get('status') == 'ok': out.append(dict(id=f"A1:{i}:{x['kind']}:{x['reader']}", src='A-reloc', delta1=None, ed=x['ed']))
for e in out:
    for k in ('delete', 'insert', 'tail', 'prepend'): e['ed'].setdefault(k, [])
seen = {}; uniq = []
for e in out:
    key = json.dumps(e['ed'], sort_keys=True)
    if key in seen: continue
    seen[key] = e['id']; uniq.append(e)
import collections
print('pre-moves', len(out), 'unique edits', len(uniq), collections.Counter((e['src'], e['delta1']) for e in uniq).most_common(20))
json.dump(uniq, open(os.path.join(common.OUT, 'PREMOVES.json'), 'w'))
