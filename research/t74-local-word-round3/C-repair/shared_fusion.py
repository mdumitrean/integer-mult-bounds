"""Shared (multi-target) read fusions: one donation H += q*A serving k >= 2 targets.

Every target t in the set reads A (coef a_t, index iA_t) and H (coef h_t, index iH_t) in B with the same dyadic ratio
q = a_t / h_t.  The edit deletes every t's read of A, inserts H += q*A at a donation position p before all the selected reads
of H, and H -= q*A at a restore position after all of them.  Preconditions (fusion.py's, applied to the whole window): A holds
the value each t read from p to the restore; every reader or scale of H inside [p, restore) is one of the selected reads;
each selected t is not read or scaled between its two reads.  Donation positions: one per event class of A/H before the first
selected read of H; restores: one per event class after the last one, before H's next other read/scale; plus the early-tail
restores at 0 and at the first tail event of A/H when A and H are untouched to the end of B.  Exactness is re-checked by the
harness (map, static rules, derived compensation)."""
import collections, itertools, json, sys
from fractions import Fraction as Q
def gen(w, G, kmax=4):
    I = G.index(w); B = I['B']; nB = len(B); reads = G.data_reads(w, I)
    def events(r): return sorted(set(I['W'][r]) | set(I['RD'][r]) | set(I['SC'][r]))
    by = collections.defaultdict(list)    # (A, H, q) -> [(t, iA, iH)]
    for t, rs in reads.items():
        for (iA, A, a) in rs:
            for (iH, H, h) in rs:
                if A == H or iA == iH or A == t or H == t: continue
                if G.any_in(I['RD'][t] + I['SC'][t], min(iA, iH), max(iA, iH) + 1): continue
                q = a / h
                if G.dyadic(q): by[(A, H, q)].append((t, iA, iH))
    out = []; seen = set()
    for (A, H, q), lst in by.items():
        if len(lst) < 2: continue
        ev = sorted(set(events(A)) | set(events(H)))
        for k in range(2, min(kmax, len(lst)) + 1):
            for sel in itertools.combinations(sorted(lst), k):
                if len({t for t, _, _ in sel}) < k: continue
                selH = {iH for _, _, iH in sel}; first, last = min(selH), max(selH)
                otherH = [x for x in I['RD'][H] + I['SC'][H] if x not in selH]
                cand_p = sorted({0} | {e + 1 for e in ev if e + 1 <= first} | {first})
                nxtH = min([x for x in otherH if x > last], default=nB)
                cand_r = sorted({last + 1} | {e + 1 for e in ev if last + 1 <= e + 1 <= nxtH} | {nxtH})
                for p in cand_p:
                    if G.any_in(otherH, p, last + 1): continue
                    okA = True
                    for t, iA, iH in sel:
                        lo, hi = (p, iA) if p <= iA else (iA + 1, p)
                        if G.any_in(I['W'][A], lo, hi): okA = False; break
                    if not okA: continue
                    rests = [('B', r) for r in cand_r if r <= nB and not G.any_in(I['W'][A], p, r) and not G.any_in(otherH, p, r)]
                    if not G.any_in(I['W'][A], p, nB) and not G.any_in(otherH, p, nB):
                        jmax = min(I['TW'][A] + I['TR'][H] + [len(I['T'])]); rests += [('T', j) for j in sorted({0, jmax})]
                    for kind, pos in rests:
                        g = ['add', H, A, q.numerator, q.denominator, []]; gr = ['add', H, A, -q.numerator, q.denominator, []]
                        ed = dict(delete=sorted(iA for _, iA, _ in sel), insert=[(p, g)], tail=[], prepend=[])
                        if kind == 'B': ed['insert'].append((pos, gr))
                        else: ed['tail'].append((pos, gr))
                        key = json.dumps(ed, sort_keys=True)
                        if key in seen: continue
                        seen.add(key); out.append(dict(A=A, H=H, q=[q.numerator, q.denominator], targets=[t for t, _, _ in sel], p=p, rest=f'{kind}@{pos}', ed=ed))
    return out, {str(k): n for k, n in sorted(collections.Counter(len(v) for v in by.values()).items())}
if __name__ == '__main__':
    sys.path.insert(0, sys.argv[1]); import harness as Hm, fusion as G
    cs, groups = gen(Hm.load(sys.argv[2]), G)
    print('shared-fusion candidates:', len(cs), '| (A,H,q) groups by size:', groups, '| distinct (A,H,targets):', len({(c['A'], c['H'], tuple(c['targets'])) for c in cs}))
