"""gen_relocate: family 3 (cleanup-side relocation) and gate merges, exact by construction.
RELOC-B: a B gate g = (t += c*s) with t, s FULL-end registers (data rows < 112, or helpers >= 224 without helper_final),
  such that no later gate of B + early tail reads t or scales t and no later gate writes s: moving g to the start of the
  remaining cleanup (a prepend, frame-free) leaves the B + tail + prepend map unchanged.  Same for scale gates on FULL-end t
  not read later.  (Ports and low helpers are excluded by the auditor rule 'full cleanup reads a low end'.)
RELOC-T: an early-tail gate with FULL-end registers whose later tail gates neither read its target nor write its source:
  moved from the early tail to a prepend (same execution order: prepends run first in the remaining cleanup).
MERGE: two gates with the same (t, s) in B + tail, with no gate in between that writes s, reads t or scales t or s:
  merged into the earlier/later one (coefficient sum; both deleted if the sum is 0)."""
import json, sys, collections
from fractions import Fraction as Q
sys.path.insert(0, __file__.rsplit('/', 1)[0]); import common
def coef(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])
def gate(t, s, c): c = Q(c); return ['add', t, s, c.numerator, c.denominator, []]
def gen(w):
    B = w['B']; nB = len(B); tail = [w['cleanup'][i] for i, U in w['early_cleanup']]; seq = list(B) + tail; L = len(seq)
    low = {int(q) for q in w['helper_final']}
    fe = lambda r: r < 112 or (r >= 224 and r not in low)
    reads_after = collections.defaultdict(list); writes_after = collections.defaultdict(list)
    for i, g in enumerate(seq):
        if g[0] == 'add': reads_after[g[2]].append(i); writes_after[g[1]].append(i)
        else: writes_after[g[1]].append(i); reads_after[g[1]].append(i)
    def later(lst, i): return any(j > i for j in lst)
    out = []
    for i, g in enumerate(seq):
        regs = g[1:3] if g[0] == 'add' else g[1:2]
        if not all(fe(r) for r in regs): continue
        t = g[1]
        if later(reads_after[t], i): continue            # t read (or scaled) later
        if g[0] == 'add' and later(writes_after[g[2]], i): continue   # s written later
        pre = list(g[:-1]) + [[]]
        if i < nB: out.append(dict(id=f'RELOC-B{i}', fam='RELOC-B', ed=dict(delete=[i], insert=[], tail=[], prepend=[pre])))
        else: out.append(dict(id=f'RELOC-T{i - nB}', fam='RELOC-T', tailmove=i - nB, gate=pre))
    # merges
    for i, g in enumerate(seq):
        if g[0] != 'add': continue
        t, s = g[1], g[2]
        for j in range(i + 1, L):
            h = seq[j]
            if h[0] == 'add' and h[1] == t and h[2] == s:
                c = coef(g) + coef(h)
                out.append(dict(id=f'MERGE-{i}-{j}', fam='MERGE', i=i, j=j, c=str(c), inB=(i < nB, j < nB)))
                break
            if (h[0] == 'add' and (h[1] == s or h[2] == t)) or (h[0] == 'scale' and h[1] in (t, s)): break
    return out
if __name__ == '__main__':
    for name in ('base', 'extra'):
        w = common.load(name); c = gen(w)
        print(name, len(c), collections.Counter(x['fam'] for x in c))
        print('  ', [x['id'] for x in c][:40])
        json.dump(c, open(f'{sys.argv[1]}-{name}.json', 'w'))
