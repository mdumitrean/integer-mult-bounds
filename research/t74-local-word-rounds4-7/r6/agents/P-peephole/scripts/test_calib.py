import os, sys, json, gzip
S = os.environ['SCR']; sys.path.insert(0, S + '/r6/agents/P-peephole/scripts')
import peep, time
B = json.load(gzip.open(S + '/r3/inputs/gauge44-word-566-554.json.gz'))['B']
W = [peep.gt(B[42]), peep.gt(B[43])]
t0 = time.time(); alts = peep.equivalents(W, 3); print('window 42-43:', W, '->', len(alts), 'alternatives', round(time.time() - t0, 2), 's')
target = (('add', 586, 506, peep.Q(2)), ('add', 114, 586, peep.Q(1, 2)), ('add', 114, 506, peep.Q(-1)))
print('r3 D FW-42-past43-to44 rediscovered:', target in alts)
for s in alts[:12]: print('  ', s)
