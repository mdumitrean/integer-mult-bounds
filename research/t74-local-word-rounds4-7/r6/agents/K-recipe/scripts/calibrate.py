"""calibrate.py: rebuild the current 566+554 words from the documented recipe chain (stdlib; vendor code is NOT run).
Steps: (a) PR1148 JOINT-WORD + PR1193 FOUR-RECIPE -> FOUR-WORD (full content);
       (b) PR1286 inputs + PR1297 RECIPE-{base,extra} -> PR1297 words (full content);
       (c) PR1297 words + EDITS.json (pivot 566, PR1625) -> step0 (scalar program + interfaces; frames are solver output);
       (d) step0 + EDITS-1.json (pivot 554, PR1672) -> current words (scalar program + interfaces).
usage: calibrate.py SCRATCH OUT.json"""
import gzip, hashlib, json, sys
from pathlib import Path
S = Path(sys.argv[1]); OUT = Path(sys.argv[2])
P1297 = S / 'r3/vendor/pr1672/research/gmx-t74-k554-signed-001/vendor/pr1297'; P1193 = P1297 / 'vendor/pr1193'
P1672 = S / 'r3/vendor/pr1672/research/gmx-t74-k554-signed-001'
def load(p):
    raw = Path(p).read_bytes(); return json.loads(gzip.decompress(raw) if str(p).endswith('.gz') else raw)
canon = lambda x: hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
INTERFACE = ('A', 'cut', 'precondition', 'ports', 'centers', 'center_frames', 'start_extra', 'helper_final', 'root_lines', 'scatter', 'target_levels')
ops = lambda g: list(g[:-1])
def compile_edits(w, ed):   # PR1625 rebuild.py semantics (B indices refer to the base word; tail inserts spliced in order)
    B = w['B']; dele = set(ed['delete']); at = {}
    for p, g in ed['insert']: at.setdefault(p, []).append(list(g))
    out = []
    for i, e in enumerate(B):
        out.extend(at.get(i, []))
        if i not in dele: out.append(list(e))
    out.extend(at.get(len(B), []))
    assert not ed.get('prepend')
    C = [list(g) for g in w['cleanup']]; early = [list(x) for x in w['early_cleanup']]; ins = []
    for j, g in ed['tail']: C.append(list(g)); ins.append((j, len(C) - 1))
    for j, ci in sorted(ins): early.insert(j, [ci, []])
    w2 = dict(w); w2['B'] = out; w2['cleanup'] = C; w2['early_cleanup'] = early; return w2
def scalar_eq(a, b):
    return dict(B=[ops(g) for g in a['B']] == [ops(g) for g in b['B']], cleanup=[ops(g) for g in a['cleanup']] == [ops(g) for g in b['cleanup']],
                early_order=[i for i, U in a['early_cleanup']] == [i for i, U in b['early_cleanup']],
                interfaces={k: a.get(k) == b.get(k) for k in INTERFACE})
res = {}
# (a)
j = load(P1193 / 'vendor/pr1148/JOINT-WORD.json.gz'); rc = load(P1193 / 'data/FOUR-RECIPE.json'); four = load(P1193 / 'data/FOUR-WORD.json.gz')
w = json.loads(json.dumps(j))
for h, old, new in rc['start_extra']: assert w['start_extra'][h] == old; w['start_extra'][h] = new
for i, old, new in rc['B']: assert w['B'][i] == old and old[:-1] == new[:-1]; w['B'][i] = new
w['report'] = rc['report']
res['a_FOUR'] = dict(content_equal=canon(w) == canon(four), start_extra_changed=[h for h, o, n in rc['start_extra']], B_frames_changed=len(rc['B']))
# (b)
for name, inp, rec, ref in (('base', 'inputs/base.json.gz', 'RECIPE-base.json.gz', 'gauge44-word.json.gz'), ('extra', 'inputs/extra.json.gz', 'RECIPE-extra.json.gz', 'extra-word.json.gz')):
    w = load(P1297 / inp); rc = load(P1297 / rec)
    for k, v in rc.items(): assert w[k] == v['old'], k; w[k] = v['new']
    res['b_1297_' + name] = dict(content_equal=canon(w) == canon(load(P1297 / ref)), recipe_keys=sorted(rc))
# (c), (d)
E0 = load(P1672 / 'new/EDITS.json'); E1 = load(P1672 / 'new/EDITS-1.json')
for name, ref1297, step0, cur, mine in (('gauge44', 'gauge44-word.json.gz', 'new/steps/0/gauge44.json.gz', 'r3/inputs/gauge44-word-566-554.json.gz', 'wt-566/research/t74-pivot566-kernel/inputs/gauge44-word-566.json.gz'),
                                        ('extra', 'extra-word.json.gz', 'new/steps/0/extra.json.gz', 'r3/inputs/extra-word-566-554.json.gz', 'wt-566/research/t74-pivot566-kernel/inputs/extra-word-566.json.gz')):
    w0 = load(P1297 / ref1297); s0 = load(P1672 / step0); c = load(S / cur); m = load(S / mine)
    w1 = compile_edits(w0, E0['edit']); w2 = compile_edits(s0, E1['edit'])
    res['c_566_' + name] = dict(vs_pr1672_step0=scalar_eq(w1, s0), vs_pr1625_word=scalar_eq(w1, m), pr1625_word_equals_step0_content=canon(m) == canon(s0))
    res['d_554_' + name] = dict(vs_current=scalar_eq(w2, c), current_frames_from_solver=sum(1 for a, b in zip(w2['B'], c['B']) if a[-1] != b[-1]))
json.dump(res, open(OUT, 'w'), indent=1)
for k, v in res.items(): print(k, json.dumps(v)[:400])
