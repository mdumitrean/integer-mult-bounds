"""afront.py: A gates with a nonzero literal frame that can commute back to a position where both of their registers are
still at frame 0 (zero start frame and only frame-0 events before that position): there the gate can run at frame 0, exactly
as in the zero-frame precondition, without changing the map or the compensation.  usage: afront.py WORD.json.gz OUT.json"""
import json, gzip, sys, collections
V = 112
w = json.load(gzip.open(sys.argv[1])); A = w['A']
start0 = lambda r: r >= 2 * V and str(r) not in w['start_extra']    # ordinary or cold helpers start at frame 0 (targets: none in A)
def regs(e): return [e[1]] + ([e[2]] if e[0] == 'add' else [])
def commute(g1, g2):
    if g1[0] == 'scale' and g2[0] == 'scale': return True
    if g1[0] == 'scale': return g1[1] not in (g2[1], g2[2])
    if g2[0] == 'scale': return g2[1] not in (g1[1], g1[2])
    return g1[1] != g2[2] and g2[1] != g1[2]
first_nonzero = {}
for i, e in enumerate(A):
    if e[-1]:
        for r in regs(e): first_nonzero.setdefault(r, i)
cands = []; why = collections.Counter()
for i, e in enumerate(A):
    if not e[-1]: continue
    rs = regs(e)
    if not all(start0(r) for r in rs): why['register not zero-start'] += 1; continue
    k = i
    while k > 0 and commute(e, A[k - 1]): k -= 1
    # both registers at frame 0 at position k: no nonzero-frame event on them before k
    if all(first_nonzero.get(r, 10 ** 9) >= k for r in rs) and k < i:
        cands.append(dict(i=i, to=k, gate=e))
        why['candidate'] += 1
    else: why['blocked'] += 1
res = dict(word=sys.argv[1].split('/')[-1], a_gates=len(A), counts=dict(why), candidates=cands)
json.dump(res, open(sys.argv[2], 'w'), indent=1); print({k: v for k, v in res.items() if k != 'candidates'}); print(cands[:8])
