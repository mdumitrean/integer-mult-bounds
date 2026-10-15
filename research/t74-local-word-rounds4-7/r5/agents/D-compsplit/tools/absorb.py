"""absorb.py: compensation-aware pricing option for the PR #1186 toolkit (rev3 copy in ../toolkit), agent D-compsplit r5.

AbsorbPricer.price_absorb(ed) differs from harness.Pricer.price in exactly two places:
  1. exactness: instead of an unchanged B+tail map, the A+cut+B+early-tail map (A-start coordinates) must be unchanged on
     every non-port row, and on every port row except the columns of ORDINARY helpers (k >= 2V, not entering = start_extra,
     not low-end = helper_final).  Those entries are exactly what the derived compensation cancels.  The precondition writes
     only ports on these words, and no tail or later cleanup gate touches a port, so this is the whole call map up to the
     re-derived compensation.
  2. compensation: re-derived by model.cone_caps for the candidate (caps recomputed from it); only the auditor's residual
     rule is enforced (no compensation gate reads an entering or low-end helper), not equality with the base compensation.
Everything else is the unchanged rev3 path: static program rules, exact optimal frames (cone caps, tail-mutable, cut
equality), true-moment interval, write-back + the unchanged audit_local.py --main on every negative delta (or on request)."""
import gzip, json, os, subprocess, sys, tempfile
from fractions import Fraction as Q
HERE = os.path.dirname(os.path.abspath(__file__)); AGENT = os.path.dirname(HERE)
SCR = os.path.abspath(os.path.join(AGENT, '..', '..', '..'))
sys.path.insert(0, os.path.join(AGENT, 'toolkit'))
MAIN = os.path.join(SCR, 'r3', 'main'); os.environ.setdefault('IMB_ROOT', MAIN); os.environ.setdefault('IMB_B', '0.001679754956125544')
import harness as H, frames as F
from word import inline
from model import cone_caps
from compat import deadline, Timeout
AUDIT = os.path.join(MAIN, 'research/gauge44-frames-x/independent/audit_local.py')

def coefq(e): return Q(e[3], e[4]) if e[0] == 'add' else Q(e[2], e[3])

def main_rows(w, npre=0):
    """{reg: {col: Q}} of A + cut + B + early tails (+ cleanup prepends) from the identity (A-start coordinates)."""
    seq = list(w['A']) + list(w['cut']) + list(w['B']) + [w['cleanup'][i] for i, U in w['early_cleanup']] + list(w['cleanup'][:npre])
    rows = {}; get = lambda x: rows.get(x, {x: Q(1)})
    for e in seq:
        t = e[1]
        if e[0] == 'add':
            a = dict(get(t)); c = coefq(e)
            for k, v in get(e[2]).items():
                a[k] = a.get(k, 0) + c * v
                if not a[k]: del a[k]
        else: a = {k: v * coefq(e) for k, v in get(t).items()}
        rows[t] = a
    return rows

def absorbable(w):
    V = w['report']['v']; n = 2 * V + w['report']['R']
    ent = set(map(int, w['start_extra'])); low = set(map(int, w['helper_final']))
    return {k for k in range(2 * V, n) if k not in ent and k not in low}

def projected_diff(w0, w1, npre=0):
    """(nonport_diff_rows, port_diff_nonabsorbed, port_diff_absorbed) between the two words' main maps."""
    V = w0['report']['v']; ab = absorbable(w0); r0 = main_rows(w0); r1 = main_rows(w1, npre)
    nonport, port_hard, port_abs = {}, {}, {}
    for x in set(r0) | set(r1):
        a = r0.get(x, {x: Q(1)}); b = r1.get(x, {x: Q(1)})
        d = {k: b.get(k, 0) - a.get(k, 0) for k in set(a) | set(b)}; d = {k: v for k, v in d.items() if v}
        if not d: continue
        if V <= x < 2 * V:
            h = {k: v for k, v in d.items() if k not in ab}; s = {k: v for k, v in d.items() if k in ab}
            if h: port_hard[x] = h
            if s: port_abs[x] = s
        else: nonport[x] = d
    return nonport, port_hard, port_abs

def run_audit(word, outdir):
    os.makedirs(outdir, exist_ok=True); pth = os.path.join(outdir, 'WORD.json.gz')
    open(pth, 'wb').write(gzip.compress(json.dumps(word, sort_keys=True, separators=(',', ':')).encode(), mtime=0))
    rc = subprocess.run([sys.executable, '-B', AUDIT, '--word', pth, '--output', os.path.join(outdir, 'AUDIT.json'), '--main', MAIN],
                        capture_output=True, text=True)
    st = None
    if rc.returncode == 0:
        try: a = json.load(open(os.path.join(outdir, 'AUDIT.json'))); st = (a.get('status'), a.get('compensation_gates'))
        except Exception: pass
    return rc.returncode, st, (rc.stdout + rc.stderr).strip().splitlines()[-3:]

def compile_ab(w, ed):
    """section-tagged edit on w (as PR1957 abkernel.compile_AB): delete=[('A'|'B', i)], insert=[('A'|'B', pos, gate)] before
    original index pos, tail=[(j, gate)] appended to cleanup and spliced into early_cleanup at j (ascending, sequential)."""
    w2 = dict(w)
    for sec in ('A', 'B'):
        S = w[sec]; dele = {i for s_, i in ed.get('delete', []) if s_ == sec}; at = {}
        for s_, p, g in ed.get('insert', []):
            if s_ == sec: at.setdefault(p, []).append(list(g[:-1]) + [list(g[-1])])
        out = []
        for i, e in enumerate(S):
            out.extend(at.get(i, []))
            if i in dele: continue
            out.append(list(e[:-1]) + [list(e[-1]) if e[-1] is not None else []])
        out.extend(at.get(len(S), [])); w2[sec] = out
    C = [list(g) for g in w['cleanup']]; early = [[i, list(U)] for i, U in w['early_cleanup']]; ins = []
    for j, g in ed.get('tail', []):
        C.append(list(g[:-1]) + [[]]); ins.append((j, len(C) - 1))
    for j, ci in sorted(ins): early.insert(j, [ci, []])
    w2['cleanup'] = C; w2['early_cleanup'] = early
    return w2

class AbsorbPricer(H.Pricer):
    def price_ab(self, ed, **kw):
        try: w1 = compile_ab(self.base, ed)
        except Exception as e: return dict(status='compile:' + str(e)[:60])
        return self.price_compiled(w1, 0, **kw)
    def price_absorb(self, ed, **kw):
        npre = len(ed.get('prepend', []))
        try: w1 = H.compile_edits(self.base, ed)
        except Exception as e: return dict(status='compile:' + str(e)[:60])
        return self.price_compiled(w1, npre, **kw)
    def price_compiled(self, w1, npre=0, timeout=300, want_word=False, audit_dir=None, always_audit=False):
        w = self.base
        why = H.program_violation(w1)
        if why: return dict(status='rule:' + why)
        nonport, hard, soft = projected_diff(w, w1, npre)
        if nonport or hard: return dict(status='inexact', nonport_rows=len(nonport), port_rows_hard=len(hard))
        try:
            with deadline(timeout):
                caps, comp = cone_caps(w1)
                ent = set(map(int, w1['start_extra'])); low = set(map(int, w1['helper_final']))
                if any(e[2] in ent | low for e in comp): return dict(status='compensation-touches-residual')
                g = F.Graph(inline(w1, True), check_literal=False, tail_mutable=True, caps=caps, cut_equality=True)
                r = F.optimal_frames(inline(w1, True), self.costs, check_literal=False, graph=g, interval=self.interval)
        except F.Infeasible as e: return dict(status='infeasible', why=str(e.args[0][:3]) if e.args else '')
        except ValueError as e: return dict(status='error:' + str(e)[:80])
        except Timeout: return dict(status='timeout')
        out = dict(status='ok' if r['certified'] else 'uncertified', delta=r['cost'] - self.base_cost,
                   profile=dict(sorted(r['profile'].items())), comp_gates=len(comp), comp_changed=comp != self.compensation,
                   caps_changed=caps != self.caps, absorbed_port_entries=sum(len(v) for v in soft.values()))
        if self.interval: out.update(self.compare(r['profile'], r['interval']))
        if want_word or always_audit or out['delta'] < 0:
            from writeback import write_back
            word = write_back(w1, g, r['assign'])
            if audit_dir:
                rc, st, tail = run_audit(word, audit_dir); out['audit'] = dict(exit=rc, status=st, tail=tail)
            if want_word: out['word'] = word
        return out
