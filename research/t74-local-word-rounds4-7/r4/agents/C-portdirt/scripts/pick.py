"""pick.py: choose up to K placements per read from PRIORITY (nearest to the original position on both sides, the
extremes of the window, and evenly spaced points).  usage: pick.py PRIORITY.json OUT.json K"""
import json, sys, collections
pr = json.load(open(sys.argv[1])); K = int(sys.argv[3]); by = collections.defaultdict(list)
for c in pr['cands']: by[(c['B'], c['y'])].append(c)
out = []
for (i, y), cs in sorted(by.items()):
    cs.sort(key=lambda c: c['p']); ps = [c['p'] for c in cs]; pick = set()
    before = [c for c in cs if c['p'] <= i]; after = [c for c in cs if c['p'] > i]
    if before: pick.add(before[-1]['p']); pick.add(before[0]['p'])
    if after: pick.add(after[0]['p']); pick.add(after[-1]['p'])
    step = max(1, len(cs) // max(1, K - len(pick)))
    for c in cs[::step]:
        if len(pick) >= K: break
        pick.add(c['p'])
    out += [c for c in cs if c['p'] in pick]
json.dump(dict(cands=out), open(sys.argv[2], 'w')); print('picked', len(out), 'of', len(pr['cands']), 'over', len(by), 'read/source pairs')
