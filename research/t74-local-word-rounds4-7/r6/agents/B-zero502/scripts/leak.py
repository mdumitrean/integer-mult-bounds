"""leak.py: exact flow of one helper's initial value q_init through precondition / A / cut / B / tail / cleanup.
usage: leak.py WORD.json.gz Q [Q ...] -> JSON on stdout (scratchpad-relative paths in output)."""
import gzip, json, sys
from fractions import Fraction as F
def regs(e): return e[1:3] if e[0] == 'add' else e[1:2]
def coef(e): return F(e[3], e[4]) if e[0] == 'add' else F(e[2], e[3])
def flow(w, q, sections):
    col = {q: F(1)}; events = []
    for sec in sections:
        for i, e in enumerate(w[sec] if sec != 'tail' else [w['cleanup'][j] for j, U in w['early_cleanup']]):
            t = e[1]; c = coef(e)
            if e[0] == 'add':
                s = e[2]; x = col.get(s)
                if x:
                    old = col.get(t, F(0)); new = old + c * x
                    if new: col[t] = new
                    else: col.pop(t, None)
                    events.append((sec, i, e[:5], str(old), str(new)))
            else:
                if t in col: col[t] = col[t] * c
    return col, events
def main():
    w = json.load(gzip.open(sys.argv[1])); v = w['report']['v']; out = {}
    for q in map(int, sys.argv[2:]):
        colm, ev = flow(w, q, ['A', 'cut', 'B'])
        # auditor: dirt[y] = helper columns of raw[y] for targets, then precondition applied to dirt rows
        raw_targets = {y: colm[y] for y in range(v, 2 * v) if y in colm}
        dirt = {y: {q: a} for y, a in raw_targets.items()}
        for e in w['precondition']:
            t = e[1]; c = coef(e)
            if e[0] == 'add':
                s = e[2]
                if s in dirt:
                    d = dirt.setdefault(t, {}); a = d.get(q, F(0)) + c * dirt[s][q]
                    if a: d[q] = a
                    else: d.pop(q, None)
            else:
                if t in dirt: dirt[t] = {k: c * a for k, a in dirt[t].items()}
        resp = {y: str(d[q]) for y, d in dirt.items() if d.get(q)}
        reads_q = [(sec, i, e[:5]) for sec in ('A', 'cut', 'B') for i, e in enumerate(w[sec]) if e[0] == 'add' and e[2] == q]
        writes_q = [(sec, i, e[:5]) for sec in ('A', 'cut', 'B') for i, e in enumerate(w[sec]) if e[1] == q]
        tgt_events = [x for x in ev if v <= x[2][1] < 2 * v]
        out[q] = dict(raw_target_leak={y: str(a) for y, a in sorted(raw_targets.items())}, entrance_response=resp,
                      main_nonzero_rows=len(colm), reads_q=reads_q[:40], n_reads_q=len(reads_q), writes_q=writes_q[:40],
                      n_writes_q=len(writes_q), target_carrier_events=tgt_events[:60], n_target_events=len(tgt_events),
                      start_extra=w['start_extra'].get(str(q)), helper_final=w['helper_final'].get(str(q)))
    print(json.dumps(out, indent=1))
main()
