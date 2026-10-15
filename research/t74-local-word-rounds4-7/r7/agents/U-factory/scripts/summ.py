"""summ.py: summarise a batch vs the baseline.  usage: summ.py JOBS.json OUTDIR [SUMMARY.json]"""
import json, sys, collections
from pathlib import Path
U = Path(__file__).resolve().parents[1]
base = json.load(open(U / 'out/v-base/RESULT.json')); fc1 = set(json.load(open(U / 'out/FULL-C1.json')))
B = set(base['read']); BE = set(base['entering']); BR = base['pairing_ranks']
jobs = json.load(open(sys.argv[1])); od = Path(sys.argv[2]); rows = []; st = collections.Counter()
for j in jobs:
    p = od / ('v-%s' % j['id']) / 'RESULT.json'
    r = json.load(open(p)) if p.exists() else dict(stage='MISSING')
    stage = r.get('stage', '?'); st[stage.split(':')[0] + (':' + stage.split(':')[1] if stage.startswith('FAIL') else '')] += 1
    if stage != 'OK': rows.append(dict(id=j['id'], stage=stage)); continue
    rd = set(r['read']); newzero = sorted(B - rd); newread = sorted(rd - B)
    rows.append(dict(id=j['id'], stage='OK', n_read=r['n_read'], ranks=r['pairing_ranks'], ranks_same=r['pairing_ranks'] == BR,
                     rank_sum=sum(r['pairing_ranks']), entering=len(r['entering']), entering_with_response=len(r['entering_with_response']),
                     ended=len(r['ended']), new_zero=newzero, new_zero_fc1=sorted(set(newzero) & fc1), new_read=newread, same_word=r['cold44_sha256'] == base['cold44_sha256']))
ok = [x for x in rows if x['stage'] == 'OK']
print('stages:', dict(st))
print('OK variants:', len(ok), '| identical word:', sum(x['same_word'] for x in ok), '| ranks unchanged:', sum(x['ranks_same'] for x in ok),
      '| entering with response >0:', sum(x['entering_with_response'] > 0 for x in ok))
print('n_read distribution:', sorted(collections.Counter(x['n_read'] for x in ok).items()))
hits = [x for x in ok if x['new_zero']]
print('variants with any new zero-response helper:', len(hits), '| with a new zero-response FULL-C1 helper:', sum(bool(x['new_zero_fc1']) for x in ok))
for x in sorted(hits, key=lambda x: (-len(x['new_zero_fc1']), x['n_read']))[:15]:
    print('  ', x['id'], 'read', x['n_read'], 'ranks', x['rank_sum'], 'ent', x['entering'], 'entR', x['entering_with_response'], 'ended', x['ended'], 'newzero', x['new_zero'][:8], 'fc1', x['new_zero_fc1'], 'newread', x['new_read'][:8])
if len(sys.argv) > 3: json.dump(rows, open(sys.argv[3], 'w'))
