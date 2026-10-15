"""r10 F-lenders: package-format stage inputs for retired7 on top of the retired5 words.
refit7 (frames: lenders 564/565 last gates B911/B912 to their exact floor, dim 6 -> 5) -> hostmove2 (the hostees of warps 30/31
move from 401/403 onto the retired lenders 564/565; warp records replaced in place) -> alias2 (667 <- 401, 669 <- 403 with
alias_build.alias, the PR2679 retired-lender alias) -> refit7c (certified optimal frames: B1170/B1171 dim 6 -> 5).
Every state is checked against the verified r10 words (frames, warps, profile) and audited by the pinned PR2679 auditor.
usage: python3 -I mk_stages7.py CODE PKG5 CERT_BASE CERT_EXTRA OUTDIR"""
import copy, gzip, json, subprocess, sys
from pathlib import Path
CODE, PKG, CB, CE, OUT = map(Path, sys.argv[1:6]); sys.path.insert(0, str(CODE))
import importlib.util as iu
def load(name, p):
    s = iu.spec_from_file_location(name, p); m = iu.module_from_spec(s); s.loader.exec_module(m); return m
WP = load('word_patch_pr2679', PKG / 'vendor/word_patch_pr2679.py')
import alias_build as AB
rd = lambda p: json.loads(gzip.decompress(Path(p).read_bytes()) if str(p).endswith('.gz') else Path(p).read_bytes())
def wgz(p, w): Path(p).write_bytes(gzip.compress(json.dumps(w, separators=(',', ':')).encode(), mtime=0))
def regs(e): return e[1:3] if e[0] == 'add' else e[1:2]
def refit_apply(w0, p):
    w = copy.deepcopy(w0)
    for sec, i, fr in p['frames']:
        assert w[sec][i][:-1] == w0[sec][i][:-1]; w[sec][i][-1] = fr
    w['report']['local_profile'] = p['local_profile']; return w
def report_of(w):
    lp, wi = AB.profile(w); return dict(w['report'], local_profile=lp, width_inventory=wi)
def audit(w, name):
    p = OUT / (name + '.json.gz'); wgz(p, w)
    r = subprocess.run([sys.executable, '-I', '-B', str(PKG / 'vendor/audit_local_pr2679.py'), '--word', str(p), '--output', str(OUT / (name + '.audit.json'))], capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip().splitlines()[-1:] if r.returncode else 'PASS'
CRED = 'retired7: Marius-Paul Dumitrean, with substantial AI assistance (Anthropic Claude, via Claude Code)'
MOVES = [(29, 401, 564, 911), (30, 403, 565, 912)]          # (warp index 0-based, old lender, new lender, new lender's last B gate)
NEW = [(667, 401), (669, 403)]
summary = {}
for tag, cp in (('base', CB), ('extra', CE)):
    s3 = rd(PKG / f'inputs/WORD-{tag}.json.gz'); fin = rd(cp)
    # refit7: the two lenders' last gates to their exact floors (the frames of the verified word)
    p7 = dict(kind='FRAME_REFIT_FOR_TWO_HOSTEE_MOVES', credit=CRED + ': new/borrow/refit/search lowers the last gates of the free retired lenders 564 (B911) and 565 (B912) from dim 6 to their exact propagated floor dim 5 (meet closure: no other gate changes); gates unchanged',
              frames=[['B', g, fin['B'][g][-1]] for _, _, _, g in MOVES], local_profile=None)
    assert all(len(s3['B'][g][-1]) == 6 and len(fin['B'][g][-1]) == 5 and L in regs(s3['B'][g]) for _, _, L, g in MOVES)
    s4 = refit_apply(s3, dict(p7, local_profile={})); p7['local_profile'] = report_of(s4)['local_profile']; s4 = refit_apply(s3, p7)
    # hostmove2: the hostees of warps 30/31 move onto 564/565 (gate relabel from the warp position, warp record replaced in place)
    s5 = copy.deepcopy(s4); moves = []
    for k, L0, L1, g in MOVES:
        pos0 = s3['warps'][k][0]; assert s3['warps'][k][1] == L0
        assert not any(L0 in regs(e) for e in s4['B'][:pos0]) and not any(L0 in regs(e) for e in s4['restore'])
        assert max(i for i, e in enumerate(s4['B']) if L1 in regs(e)) == g and not any(L1 in regs(e) for e in s4['restore'])
        for i in range(pos0, len(s5['B'])):
            e = s5['B'][i]
            if e[0] == 'add':
                if e[1] == L0: e[1] = L1
                if e[2] == L0: e[2] = L1
            elif e[1] == L0: e[1] = L1
        rec = fin['warps'][k]; assert rec[1] == L1 and len(rec[3]) == len(rec[4]) == 5
        first = min(i for i, e in enumerate(s5['B']) if L1 in regs(e) and i > g); assert rec[0] == first
        U = AB.frame_at_B(dict(s5, warps=s5['warps'][:k] + s5['warps'][k + 1:]), L1, first)
        assert list(U) == rec[3] and AB.contained(AB.basis(rec[4]), AB.basis(s5['B'][first][-1])) and AB.make_G(rec[3], rec[4]) == rec[2]
        s5['warps'][k] = rec; moves.append(dict(op=k + 1, L_old=L0, L_new=L1, old_pos=pos0, pos=first, U=rec[3], E=rec[4], G=rec[2]))
    t = copy.deepcopy(s5); t['A'] = s5['A'][s5['prelude_events']:]; s5['cleanup'] = WP.derive_cleanup(t, WP.restored_of(s4)); s5['report'] = report_of(s5)
    ph = dict(kind='HOSTEE_MOVES_ONTO_RETIRED_LENDERS', credit=CRED + ': the hostees of B-warps 30 and 31 (lenders 401 and 403, whose own lives end in A) move onto the free retired lenders 564 and 565 (last B use B911/B912 before the hostees enter); each gate of the hostee is relabelled and its warp record is replaced in place (op ids 30/31 kept), U = the lender frame after its refitted last gate, E = the hostee entrance frame, explicit invertible G with G(U) = E',
              moves=moves, declared_gate_edit=WP.kernel_gate_edit(s4['B'], s5['B']), fields={k: s5[k] for k in ('start_extra', 'removed', 'B', 'restore', 'warps')}, prelude_events=s5['prelude_events'], report=s5['report'])
    assert WP.apply_lowfour(s4, ph) == s5, 'hostmove2 patch reproduces its state'
    # alias2: 667 <- 401, 669 <- 403 (PR2679 retired-lender alias; E = the follower's first-gate frame, dims agree)
    s6 = copy.deepcopy(s5); recs = []
    for h, L in NEW:
        first = min(p for p, e in enumerate(s6['B']) if e[0] != 'warp' and h in AB.registers(e))
        s6, r = AB.alias(s6, h, L, list(AB.basis(s6['B'][first][-1]))); recs.append(r)
    s6['report'] = report_of(s6)
    for r in recs:
        f = next(x for x in fin['warps'][70:] if x[1] == r['L']); assert [r['pos'], r['L'], r['G'], r['U'], r['E']] == f, ('alias record', r['h'])
    pa = dict(kind='TWO_RETIRED_LENDER_ALIASES_AFTER_HOSTEE_MOVES', credit=CRED + ': new/borrow/alias_build.alias 667 <- 401 and 669 <- 403 (the PR2679 retired-lender alias), one B warp each with an explicit invertible G, G(U) = E, dim 4; the helpers are removed',
              aliases=recs, declared_gate_edit=WP.kernel_gate_edit(s5['B'], s6['B']), fields={k: s6[k] for k in ('start_extra', 'removed', 'B', 'restore', 'warps')}, prelude_events=s6['prelude_events'], report=s6['report'])
    assert WP.apply_lowfour(s5, pa) == s6, 'alias2 patch reproduces its state'
    # refit7c: certified optimal frames of the final program (the frames of the verified word)
    diff = [(sec, i) for sec in ('A', 'B', 'restore') for i, (x, y) in enumerate(zip(s6[sec], fin[sec])) if x[-1] != y[-1]]
    pc = dict(kind='FRAME_REFIT_CERTIFIED_OPTIMAL_RETIRED7', credit=CRED + ': certified optimal frames of the aliased program (our #1186 toolkit optimal_frames on the borrow-word model, certified=True); gates, warps, start/final frames, compensation and widths unchanged',
              frames=[[sec, i, fin[sec][i][-1]] for sec, i in diff], local_profile=fin['report']['local_profile'])
    s7 = refit_apply(s6, pc); assert report_of(s7)['local_profile'] == fin['report']['local_profile'] and report_of(s7)['width_inventory'] == fin['report']['width_inventory']
    for k in s7:
        if k not in ('removed', 'warps', 'cleanup'): assert s7[k] == fin[k], ('field differs from verified word', k)
    assert sorted(s7['removed']) == sorted(fin['removed']) and s7['warps'][:70] == fin['warps'][:70] and sorted(map(json.dumps, s7['warps'][70:])) == sorted(map(json.dumps, fin['warps'][70:]))
    for n, p in (('refit7', p7), ('hostmove2', ph), ('alias2', pa), ('refit7c', pc)): (OUT / f'{n}_43{tag}.json').write_text(json.dumps(p, separators=(',', ':')))
    wgz(OUT / f'WORD-{tag}.json.gz', s7)
    au = {n: audit(w, f'{tag}-{n}') for n, w in (('refit7', s4), ('hostmove2', s5), ('alias2', s6), ('retired7', s7))}
    summary[tag] = dict(refit7=len(p7['frames']), hostmove2_edits=len(ph['declared_gate_edit']), alias2_edits=len(pa['declared_gate_edit']), refit7c=[d for d in diff],
                        profiles={n: report_of(w)['local_profile'] for n, w in (('refit7', s4), ('hostmove2', s5), ('alias2', s6), ('retired7', s7))}, audits=au)
    print(tag, json.dumps(summary[tag]), flush=True)
(OUT / 'STAGES7.json').write_text(json.dumps(summary, indent=1))
