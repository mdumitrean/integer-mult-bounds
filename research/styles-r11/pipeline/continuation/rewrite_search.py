"""Bounded paired input/output grammar on the frozen PR2917 endpoint word.

No search is run on import.  The coordinator must preregister and use pool.py.
Only stdlib and the source-pinned, existing wordio implementation are imported.
Fetched producer/checker sources are data and are never imported or executed.

Mathematical attribution: Jeremy Diviney's PR2908 paired extraction, Mason
Hale's PR2917 composition and guarded refits, Jeremy Kothe's compensation and
cleanup conventions, and the complete source notices supplied in attribution.
This is a bounded continuation of those productions, not a saturation theorem.

API: prepare({provider: {raw, attribution}}) loads immutable parent structures;
task_specs(seed) returns grouped finite census tasks; screen_task(spec) returns
exact transform witnesses and full local invoices, without native admission;
construct(provider, transform) reproduces a selected candidate.  The independent
continuation/admission.py local_admission is a separate required validation.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from fractions import Fraction as Q
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys
import time

PAIR_CAP = 8
PIVOT_CAP = 16
MODES = ("literal", "downward_cap")
WORDIO_SHA = "a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4"
MAX_MATRIX_TERMS = 2_000_000
MAX_RATIONAL_BITS = 4096
ALLOWED_CHANGED_FIELDS = frozenset(("A", "B", "restore", "helper_final",
                                    "compensation", "report", "cleanup"))
_WORDS = {}
_W = None


class ExactBudgetExceeded(RuntimeError):
    """A resource cutoff is an incomplete task, never a scientific rejection."""


class CandidateRejected(ValueError):
    """A declared dyadic-factorization or frame guard rejects one choice."""


def reject_unless(condition,message):
    if not condition:
        raise CandidateRejected(message)


def need(condition, message):
    if not condition:
        raise ValueError(message)


def semantic_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def _wordio():
    global _W
    if _W is None:
        path = Path(__file__).resolve().parents[1] / "wordio.py"
        need(hashlib.sha256(path.read_bytes()).hexdigest() == WORDIO_SHA,
             "trusted wordio source drift")
        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("styles_paired_wordio", path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _W = module
    return _W


def _rational(q):
    q = Q(q)
    if max(q.numerator.bit_length(), q.denominator.bit_length()) > MAX_RATIONAL_BITS:
        raise ExactBudgetExceeded("exact rational bit cap exceeded; incomplete protocol task")
    return q


def _dyadic(q):
    q = Q(q)
    return q.denominator & (q.denominator - 1) == 0


def _unit(q):
    q = Q(q)
    a = abs(q.numerator)
    return bool(a) and _dyadic(q) and a & (a - 1) == 0


def _regs(g):
    return tuple(g[1:3]) if g[0] == "add" else (g[1],)


def _add(dst, src, factor):
    result = dict(dst)
    for key, value in src.items():
        q = _rational(result.get(key, Q(0)) + factor * value)
        if q:
            result[key] = q
        else:
            result.pop(key, None)
    return result


def _scale(row, factor):
    return {key: _rational(value * factor) for key, value in row.items() if value * factor}


def _apply(g, rows, formal=True):
    op = g[0]
    if op == "add":
        a, b = g[1:3]
        need(a != b, "self addition")
        rows[a] = _add(rows[a], rows[b], Q(g[3], g[4]))
    elif op == "scale":
        q = Q(g[2], g[3])
        need(q != 0, "zero scale")
        rows[g[1]] = _scale(rows[g[1]], q)
    else:
        need(op == "warp" and formal, "unsupported formal operation")
        symbol = g[2]
        rows[g[1]] = {(r, word[1:] if word and word[0] == -symbol else (symbol,) + word): q
                      for (r, word), q in rows[g[1]].items()}


def _inverse(g):
    e = list(g)
    if e[0] == "add":
        e[3] = -e[3]
    elif e[0] == "scale":
        e[2], e[3] = e[3], e[2]
    else:
        e[2] = -e[2]
    return e


def _program(raw):
    v = raw["report"]["v"]
    result = [g for g in raw["A"][raw.get("prelude_events", 0):]
              if g[0] == "warp" or not v <= g[1] < 2 * v]
    bypos = defaultdict(list)
    for op, rec in enumerate(raw["warps"], 1):
        bypos[rec[0]].append(["warp", rec[1], op])
    for i in range(len(raw["B"]) + 1):
        result.extend(bypos[i])
        if i < len(raw["B"]):
            g = raw["B"][i]
            if not v <= g[1] < 2 * v:
                result.append(g)
    result.extend(raw["restore"])
    return result


def _matrix(live, program, inverse=False):
    rows = {r: {(r, ()): Q(1)} for r in live}
    seq = (_inverse(g) for g in reversed(program)) if inverse else program
    for i, g in enumerate(seq):
        _apply(g, rows)
        if i % 128 == 0:
            if sum(map(len, rows.values())) > MAX_MATRIX_TERMS:
                raise ExactBudgetExceeded("formal matrix term cap exceeded; incomplete protocol task")
    if sum(map(len, rows.values())) > MAX_MATRIX_TERMS:
        raise ExactBudgetExceeded("formal matrix term cap exceeded; incomplete protocol task")
    return rows


def _compensation(raw):
    columns = defaultdict(dict)
    for g in raw["compensation"]:
        need(g[0] == "add" and g[-1] == [], "scalar zero-frame compensation required")
        r, t, q = g[2], g[1], Q(g[3], g[4])
        columns[r][t] = columns[r].get(t, Q(0)) + q
    return {r: {t: q for t, q in col.items() if q} for r, col in columns.items()}


@lru_cache(None)
def _basis(frame):
    return _wordio().basis(frame)


@lru_cache(None)
def _perp(frame):
    return _basis(tuple(x for x in range(1, 512)
                        if all((x & y).bit_count() % 2 == 0 for y in frame)))


@lru_cache(None)
def _meet(a, b):
    return _perp(_basis(_perp(a) + _perp(b)))


def _join(*frames):
    return _basis(tuple(x for frame in frames for x in frame))


def _inside(a, b):
    return _join(a, b) == b


def hyperplane(normal):
    need(type(normal) is int and 1 <= normal < 512, "nonzero nine-bit normal")
    return _perp((normal,))


def _geometry(raw, canonical):
    """Exact literal events and attained forward floors with cut/warp pins."""
    events, bypos = [], defaultdict(list)
    for i, g in enumerate(raw["A"]):
        events.append(("A", i, g))
    boundary = len(events)
    events.append(("boundary", -1, None))
    for op, rec in enumerate(raw["warps"], 1):
        bypos[rec[0]].append((op, rec))
    for i in range(len(raw["B"]) + 1):
        for op, rec in bypos[i]:
            events.append(("Bwarp", op, ["warp", rec[1], op, rec[3], rec[4]]))
        if i < len(raw["B"]):
            events.append(("B", i, raw["B"][i]))
    events.extend(("restore", i, g) for i, g in enumerate(raw["restore"]))
    v = canonical.v
    pins = {v + t: _basis(tuple(raw.get("target_levels", {}).get(str(t), []))) for t in range(v)}
    pins.update({r: _basis(tuple(f)) for r, f in zip(raw["centers"], raw["center_frames"])})
    xlo, last, last_a = {}, {}, {}
    for t, (section, _, g) in enumerate(events):
        if section == "boundary":
            for r, f in pins.items():
                if r in last_a:
                    xlo[last_a[r]] = _join(xlo.get(last_a[r], ()), f)
            continue
        if g[0] == "warp":
            r, fr = g[1], _basis(tuple(g[3]))
            if r in last:
                xlo[last[r]] = _join(xlo.get(last[r], ()), fr)
            else:
                need(tuple(canonical.start[r]) == fr, "unanchored initial warp")
            last.pop(r, None)
        else:
            for r in _regs(g):
                last[r] = t
                if section == "A":
                    last_a[r] = t
    floor, current, literal = {}, list(canonical.start), list(canonical.start)
    for t, (section, _, g) in enumerate(events):
        if section == "boundary":
            for r, f in pins.items():
                current[r] = _join(current[r], f)
                need(literal[r] == f, "literal centre boundary pin")
            continue
        if g[0] == "warp":
            r, fr, to = g[1], _basis(tuple(g[3])), _basis(tuple(g[4]))
            need(current[r] == fr and literal[r] == fr, "forward warp equality")
            current[r] = literal[r] = to
        else:
            rs, actual = _regs(g), _basis(tuple(g[-1]))
            value = _join(xlo.get(t, ()), *(current[r] for r in rs))
            need(_inside(value, actual), "attained floor must lie in the literal frame")
            floor[t] = value
            for r in rs:
                current[r], literal[r] = value, actual
    return dict(events=events, boundary=boundary, pins=pins, floor=floor,
                minimum_terminal=tuple(current), literal_terminal=tuple(literal))


def _prepare_one(raw, attribution):
    W = _wordio()
    canonical = W.WordData(raw, attribution)
    need((canonical.v, canonical.h, canonical.n) == (112, 9, 704), "pinned geometry")
    live = tuple(r for r in canonical.live if not canonical.v <= r < 2 * canonical.v)
    protected = set(map(int, raw["helper_final"])) | set(map(int, raw["start_extra"]))
    protected |= {c["source"] for c in raw["initial_corrections"]}
    # These must be untouched input coordinates at the insertion boundary.
    protected |= {r for g in raw["A"][:raw.get("prelude_events", 0)] for r in _regs(g)}
    H = tuple(r for r in live if r >= 2 * canonical.v and r not in protected)
    program = _program(raw)
    M, N = _matrix(live, program), _matrix(live, program, inverse=True)
    C = _compensation(raw)
    CN = {}
    for r, col in C.items():
        need(r in N, "compensation source must be a live non-target")
        for target, q in col.items():
            CN[target] = _add(CN.get(target, {}), N[r], q)
    return dict(raw=deepcopy(raw), attribution=deepcopy(attribution), canonical=canonical,
                raw_sha256=semantic_sha(raw), live=live, H=H, protected=protected,
                restored=set(map(int,raw["helper_final"])),
                M=M, N=N, C=C, CN=CN, geometry=_geometry(raw, canonical))


def prepare(records):
    """Parent-only immutable preparation; preregistration must already exist."""
    need(not _WORDS, "prepare is once-only")
    started = time.process_time()
    for provider in sorted(records):
        record = records[provider]
        _WORDS[provider] = _prepare_one(record["raw"], record["attribution"])
        need(len(record["raw"]["helper_final"]) == 82, "final PR2917 82-endpoint baseline required")
    summary = {}
    for provider, state in _WORDS.items():
        groups = []
        for mode in MODES:
            terminal = state["geometry"]["literal_terminal" if mode == "literal" else "minimum_terminal"]
            bins = defaultdict(list)
            for normal in range(1, 512):
                frame = hyperplane(normal)
                R = tuple(r for r in state["live"] if r not in state["restored"] and _inside(terminal[r], frame))
                bins[R].append(normal)
            for R, normals in sorted(bins.items()):
                groups.append(dict(mode=mode, output_registers=list(R), normals=normals))
        state["groups"] = groups
        summary[provider] = dict(word_semantic_sha256=state["raw_sha256"],
                                 independent_non_target_inputs=len(state["live"]),
                                 eligible_input_helpers=len(state["H"]),
                                 restored_endpoints=82, groups=len(groups), hyperplanes_per_mode=511,
                                 M_terms=sum(map(len, state["M"].values())),
                                 inverse_M_terms=sum(map(len, state["N"].values())),
                                 source_attribution=deepcopy(state["attribution"]))
    return dict(status="PREPARED", providers=summary, cpu_seconds=time.process_time()-started,
                imports={"wordio.py": WORDIO_SHA}, pairs_per_normal=PAIR_CAP,
                pivots_per_pair=PIVOT_CAP, excluded_scope="rank-seven helper408; no rank-seven frames")


def task_specs(seed):
    need(_WORDS, "parent prepare required")
    tasks = [dict(provider=provider, group=i, seed=int(seed))
             for provider in sorted(_WORDS) for i in range(len(_WORDS[provider]["groups"]))]
    # Seed changes scheduling only; basis/pair/pivot definitions are seed-free.
    random.Random(seed).shuffle(tasks)
    return tasks


def _kernel(columns, constraints):
    """Exact canonical echelon nullspace, free columns ascending.

    Constraint keys and variable IDs sort lexicographically. Every pivot is
    the smallest remaining variable and is normalized to +1. Basis vector f
    sets free coordinate f to 1, all other free coordinates to 0, and back
    substitutes pivots in descending order. No numeric rank decision occurs.
    """
    echelon = {}
    for key in sorted(constraints):
        row = {r: Q(q) for r, q in constraints[key].items() if q}
        while row:
            pivot = min(row)
            if pivot not in echelon:
                q = row[pivot]
                echelon[pivot] = _scale(row, 1 / q)
                break
            row = _add(row, echelon[pivot], -row[pivot])
    basis = []
    for free in sorted(set(columns) - set(echelon)):
        value = {free: Q(1)}
        for pivot in sorted(echelon, reverse=True):
            q = -sum((a * value.get(j, Q(0)) for j, a in echelon[pivot].items() if j != pivot), Q(0))
            if q:
                value[pivot] = _rational(q)
        basis.append(value)
    return basis, dict(columns=len(columns), constraints=len(constraints), rank=len(echelon),
                       nullity=len(basis), free_columns=sorted(set(columns)-set(echelon)))


def _spaces(state, R):
    Rset, H = set(R), set(state["H"])
    left, right = defaultdict(dict), defaultdict(dict)
    for r in R:
        for (c, ops), q in state["M"][r].items():
            if c not in H or ops:
                left[(c, ops)][r] = q
    for c, row in state["N"].items():
        for (r, ops), q in row.items():
            if r in Rset and (c not in H or ops):
                right[(0, c, ops)][r] = q
    for target, row in state["CN"].items():
        for (r, ops), q in row.items():
            if r in Rset:
                right[(1, target, ops)][r] = q
    alphas, left_meta = _kernel(R, left)
    ys, right_meta = _kernel(R, right)
    return alphas, ys, dict(alpha_space=left_meta, y_space=right_meta)


def _formal_row_product(vector, M):
    result = {}
    for r, q in vector.items():
        result = _add(result, M[r], q)
    return result


def _formal_column_product(M, vector):
    result = {}
    for r, row in M.items():
        values = defaultdict(Q)
        for (c, ops), q in row.items():
            values[ops] += q * vector.get(c, Q(0))
        for ops, q in values.items():
            if q:
                result[r, ops] = _rational(q)
    return result


def _scalar(formal, allowed):
    need(all(not ops and r in allowed for r, ops in formal), "non-scalar/protected support")
    return {r: q for (r, _), q in formal.items() if q}


def _vector_key(v):
    return tuple((r, q.numerator, q.denominator) for r, q in sorted(v.items()))


def _pairs(state, R):
    alphas, ys, meta = _spaces(state, R)
    pairs = []
    for i, alpha in enumerate(alphas):
        for j, y in enumerate(ys):
            pairing = sum((q * y.get(r, Q(0)) for r, q in alpha.items()), Q(0))
            if pairing:
                a = _scale(alpha, 1 / pairing)
                u = _scalar(_formal_row_product(a, state["M"]), set(state["H"]))
                v = _scalar(_formal_column_product(state["N"], y), set(state["H"]))
                pairs.append(dict(alpha=a, y=y, u=u, v=v, basis_indices=[i,j], pairing=pairing))
    pairs.sort(key=lambda p: (len(p["alpha"])+len(p["y"]), len(p["u"])+len(p["v"]),
                              _vector_key(p["alpha"]), _vector_key(p["y"]), p["basis_indices"]))
    meta.update(nonzero_basis_pairs=len(pairs), retained_basis_pairs=min(PAIR_CAP, len(pairs)),
                truncated_basis_pairs=max(0, len(pairs)-PAIR_CAP))
    return pairs[:PAIR_CAP], meta


def _gate_add(a, b, q, frame):
    q = Q(q)
    need(q and _dyadic(q) and a != b, "legal nonzero dyadic addition")
    return ["add", a, b, q.numerator, q.denominator, list(frame)]


def _gate_scale(a, q, frame):
    q = Q(q)
    need(_unit(q), "dyadic unit scale")
    return ["scale", a, q.numerator, q.denominator, list(frame)]


def _swap(a, b, frame):
    if a == b:
        return []
    return [_gate_add(a,b,1,frame), _gate_add(b,a,-1,frame),
            _gate_add(a,b,1,frame), _gate_scale(b,-1,frame)]


def _permute(vector, a, b):
    return {(b if r == a else a if r == b else r): q for r, q in vector.items()}


def _synthesize(pair, helper, frame):
    """Elementary dyadic factorization of the two dual scalar pairs."""
    u, v, alpha, y = (pair[k] for k in ("u", "v", "alpha", "y"))
    reject_unless(all(_dyadic(q) for vec in (u,v,alpha,y) for q in vec.values()),
                  "canonical basis pair is not dyadic")
    ip = helper if _unit(v.get(helper, 0)) else next((r for r in sorted(v) if _unit(v[r])), None)
    op = helper if _unit(alpha.get(helper, 0)) else next((r for r in sorted(alpha) if _unit(alpha[r])), None)
    reject_unless(ip is not None and op is not None, "no unit input/output pivot in this basis pair")
    up, vp = _permute(u, helper, ip), _permute(v, helper, ip)
    before = [_gate_add(helper,r,-q,()) for r,q in sorted(up.items()) if r != helper and q]
    if vp[helper] != 1:
        before.append(_gate_scale(helper,vp[helper],()))
    before.extend(_gate_add(r,helper,q/vp[helper],()) for r,q in sorted(vp.items()) if r != helper and q)
    before.extend(_swap(helper,ip,()))
    ap, yp = _permute(alpha, helper, op), _permute(y, helper, op)
    after = _swap(helper,op,frame)
    if ap[helper] != 1:
        after.append(_gate_scale(helper,ap[helper],frame))
    after.extend(_gate_add(helper,r,q,frame) for r,q in sorted(ap.items()) if r != helper and q)
    after.extend(_gate_add(r,helper,-q,frame) for r,q in sorted(yp.items()) if r != helper and q)
    if not after:
        after = [_gate_scale(helper,1,frame)]
    return before, after


def _refit(state, frame, support):
    """Largest frames below the literal ones meeting terminal output caps.

    The reverse meet propagation retains every original cut/warp pin. Its
    result must enclose the independently attained forward floor at each gate.
    This is a deterministic feasible-frame construction, not cost optimization.
    """
    geo, canonical = state["geometry"], state["canonical"]
    caps = list(canonical.end)
    for r in support:
        caps[r] = _meet(caps[r], frame)
    edits = []
    for t in range(len(geo["events"])-1, -1, -1):
        section, index, g = geo["events"][t]
        if section == "boundary":
            for r, pin in geo["pins"].items():
                reject_unless(_inside(pin, caps[r]), "terminal cap conflicts with centre boundary")
                caps[r] = pin
            continue
        if g[0] == "warp":
            fr, to = _basis(tuple(g[3])), _basis(tuple(g[4]))
            reject_unless(_inside(to, caps[g[1]]), "terminal cap conflicts with warp image")
            caps[g[1]] = fr
            continue
        rs, old = _regs(g), _basis(tuple(g[-1]))
        new = old
        for r in rs:
            new = _meet(new, caps[r])
        reject_unless(_inside(geo["floor"][t], new), "terminal cap below attained gate floor")
        if section == "A" and index < state["raw"].get("prelude_events", 0):
            reject_unless(new == old, "entry prelude is frozen")
        if new != old:
            edits.append(dict(section=section, parent_index=index, gate=deepcopy(g[:-1]),
                              old_frame=deepcopy(g[-1]), new_frame=list(new)))
        for r in rs:
            caps[r] = new
    reject_unless(all(_inside(canonical.start[r], caps[r]) for r in canonical.live), "entry cap conflict")
    return sorted(edits, key=lambda e: ({"A":0,"B":1,"restore":2}[e["section"]], e["parent_index"]))


def _plain_matrix(live, gates):
    rows = {r: {r: Q(1)} for r in live}
    for g in gates:
        _apply(g, rows, formal=False)
    return rows


def certificate(state, transform):
    """Derive all eight identities afresh from literal input/output gates."""
    h, before, after = transform["helper"], transform["before"], transform["after"]
    S, T = _plain_matrix(state["live"], before), _plain_matrix(state["live"], after)
    invT = _plain_matrix(state["live"], [_inverse(g) for g in reversed(after)])
    v = {r: row[h] for r,row in S.items() if row.get(h)}
    alpha = T[h]
    y = {r: row[h] for r,row in invT.items() if row.get(h)}
    u = _scalar(_formal_row_product(alpha,state["M"]), set(state["H"]))
    need(set(v) <= set(state["H"]), "input column touches protected helper")
    need(_formal_column_product(state["M"],v) == {(r,()):q for r,q in y.items()}, "M v = y")
    need(sum((q*y.get(r,Q(0)) for r,q in alpha.items()),Q(0)) == 1, "alpha y = 1")
    us = {}
    for r,q in u.items():
        us = _add(us,S[r],q)
    need(us == {h:Q(1)}, "u S = e_h^T")
    need(all(sum((q*y.get(c,Q(0)) for c,q in row.items()),Q(0)) == (1 if r==h else 0)
             for r,row in T.items()), "T y = e_h")
    Cv = {}
    for r,q in v.items():
        Cv = _add(Cv,state["C"].get(r,{}),q)
    need(not Cv, "C v = 0")
    return dict(status="PASS_EXACT_PAIRED_IDENTITIES", helper=h,
                vectors={name:{str(r):str(q) for r,q in sorted(vec.items())}
                         for name,vec in (("u",u),("v",v),("alpha",alpha),("y",y))},
                identities=["S e_h=v","u S=e_h^T","M v=y","alpha M=u","alpha y=1",
                            "T y=e_h","e_h^T T=alpha","C v=0"],
                scope="Finite free-operator production; native and complete owner/outer admission remain required")


def _apply_transform(state, transform):
    raw, h = state["raw"], transform["helper"]
    need(transform.get("parent_semantic_sha256",state["raw_sha256"]) == state["raw_sha256"],
         "transform bound to a different parent word")
    need(h in state["H"] and h != 408, "fresh unprotected helper; active helper408 lead excluded")
    frame = hyperplane(transform["normal"])
    before, after = transform["before"], transform["after"]
    need(all(g[0] in ("add","scale") and g[-1] == [] and set(_regs(g)) <= set(state["H"])
             for g in before), "zero-frame input production on eligible helpers only")
    need(all(g[0] in ("add","scale") and _basis(tuple(g[-1])) == frame and
             set(_regs(g)) <= set(state["live"])-state["restored"] for g in after),
         "common rank-eight output frame, preserving every old restored coordinate")
    for g in before+after:
        q = Q(g[3],g[4]) if g[0]=="add" else Q(g[2],g[3])
        need(_dyadic(q) and (g[0] != "scale" or _unit(q)), "dyadic gate hygiene")
    proof = certificate(state,transform)
    result, seen = deepcopy(raw), set()
    for edit in transform.get("frame_changes",[]):
        section,index = edit["section"],edit["parent_index"]
        need(section in ("A","B","restore") and (section,index) not in seen, "unique frame edit")
        need(section != "A" or index >= raw.get("prelude_events",0), "frozen entry prelude")
        seen.add((section,index))
        g = result[section][index]
        need(g[:-1] == edit["gate"] and g[-1] == edit["old_frame"], "literal frame edit preimage")
        new = _basis(tuple(edit["new_frame"]))
        need(list(new) == edit["new_frame"] and _inside(new,_basis(tuple(g[-1]))), "downward canonical frame edit")
        g[-1] = list(new)
    npre = raw.get("prelude_events",0)
    result["A"] = result["A"][:npre]+deepcopy(before)+result["A"][npre:]
    result["restore"] += deepcopy(after)
    result["helper_final"][str(h)] = list(frame)
    C = deepcopy(state["C"])
    for g in reversed(before):
        if g[0] == "scale":
            C[g[1]] = _scale(C.get(g[1],{}),Q(g[2],g[3]))
        else:
            t,s = g[1:3]
            C[s] = _add(C.get(s,{}),C.get(t,{}),Q(g[3],g[4]))
    need(not C.get(h), "new cold helper has nonzero compensation")
    result["compensation"] = [["add",t,r,q.numerator,q.denominator,[]]
                              for r,col in sorted(C.items()) for t,q in sorted(col.items()) if q]
    W = _wordio()
    canon = W.WordData(result,state["attribution"],assert_profile=False)
    result["report"]["local_profile"] = {str(r):n for r,n in canon.paid.items()}
    result["report"]["width_inventory"] = {str(r):n for r,n in sorted(Counter(
        len(canon.end[r])-len(canon.start[r]) for r in canon.helpers).items())}
    result["cleanup"] = W.derived_borrow_cleanup(canon)
    canon = W.WordData(result,state["attribution"])
    changed = {k for k in set(raw)|set(result) if raw.get(k)!=result.get(k)}
    need(changed <= ALLOWED_CHANGED_FIELDS, "undeclared word field changed")
    need(all(result["helper_final"].get(k)==f for k,f in raw["helper_final"].items()), "old endpoints preserved")
    need(len(result["helper_final"]) == len(raw["helper_final"])+1, "one charged additional buffer")
    old_mass = sum(int(r)*n for r,n in raw["report"]["local_profile"].items())
    need(sum(r*n for r,n in canon.paid.items()) == old_mass-1,
         "rank-eight extraction must save exactly one local rank unit")
    need(canon.helpers == state["canonical"].helpers, "physical helper roles preserved")
    return result, proof


def construct(provider, transform):
    need(provider in _WORDS, "parent prepare required")
    return _apply_transform(_WORDS[provider], transform)


def reconstruct_nominee(address):
    """Regenerate a compact recorded address and bind its exact word hash."""
    provider, group_index = address["provider"],int(address["group"])
    state, group = _WORDS[provider],_WORDS[provider]["groups"][group_index]
    normal,helper = address["normal"],address["helper"]
    need(normal in group["normals"] and address["mode"]==group["mode"],"nominee group binding")
    R = tuple(group["output_registers"])
    pairs,_ = _pairs(state,R)
    pair_index = address["canonical_pair"]
    need(0 <= pair_index < len(pairs),"bounded canonical pair binding")
    pivots = sorted(set(R)&set(state["H"])-{408},
                    key=lambda h:(len(state["geometry"]["literal_terminal"][h]),h))[:PIVOT_CAP]
    need(helper in pivots,"bounded helper pivot binding")
    pair,frame = pairs[pair_index],hyperplane(normal)
    before,after = _synthesize(pair,helper,frame)
    support = {r for g in after for r in _regs(g)}
    edits = [] if group["mode"]=="literal" else _refit(state,frame,support)
    transform = dict(helper=helper,normal=normal,before=before,after=after,
                     frame_changes=edits,mode=group["mode"],canonical_pair=pair_index,
                     basis_indices=pair["basis_indices"],parent_semantic_sha256=state["raw_sha256"])
    raw,proof = _apply_transform(state,transform)
    need(address.get("semantic_sha256",semantic_sha(raw))==semantic_sha(raw),"recorded nominee word hash")
    return raw,transform,proof


def apply_to_raw(raw, transform, attribution):
    """Standalone literal production for registered reconstruction controls.

    No fetched implementation is called. The supplied transform is inert JSON;
    exact preimages, all algebraic identities and the full invoice are derived.
    """
    return _apply_transform(_prepare_one(raw,attribution),transform)


def calibration_task(spec):
    """Registered positive control: reproduce nine published literal stages.

    The coordinator supplies parent/final inert words and transforms once in
    the pool task. Independent all-column/native audits are separate stages.
    """
    started = time.process_time()
    raw, stages = deepcopy(spec["parent_raw"]), []
    for transform in spec["transforms"]:
        raw, proof = apply_to_raw(raw,transform,spec["attribution"])
        stages.append(dict(helper=transform["helper"],certificate_status=proof["status"],
                           semantic_sha256=semantic_sha(raw),private_buffers=len(raw["helper_final"]),
                           local_profile=deepcopy(raw["report"]["local_profile"])))
    need(raw == spec["expected_raw"], "nine-stage reconstruction differs from full decoded final word")
    return dict(status="PASS_LITERAL_PAIRED_RECONSTRUCTION",seed=spec["seed"],stages=stages,
                exact_final_payload_equality=True,final_semantic_sha256=semantic_sha(raw),
                source_attribution=deepcopy(spec["attribution"]),
                cpu_seconds=time.process_time()-started,
                independent_all_column_audit="SEPARATE_REQUIRED_CONTROL")


def screen_task(spec):
    """One grouped pool task. No filesystem writes or scientific global claim."""
    started = time.process_time()
    state = _WORDS[spec["provider"]]
    group = state["groups"][int(spec["group"])]
    R, mode = tuple(group["output_registers"]),group["mode"]
    pairs, meta = _pairs(state,R)
    pivots = sorted(set(R)&set(state["H"])-{408})
    # Fixed pivot ordering: smallest literal terminal rank, then register ID.
    pivots.sort(key=lambda h:(len(state["geometry"]["literal_terminal"][h]),h))
    retained_pivots = pivots[:PIVOT_CAP]
    witnesses, rejects, constructions = [], Counter(), 0
    for normal in group["normals"]:
        frame = hyperplane(normal)
        for pair_index,pair in enumerate(pairs):
            for helper in retained_pivots:
                constructions += 1
                try:
                    before,after = _synthesize(pair,helper,frame)
                    support = {r for g in after for r in _regs(g)}
                    edits = [] if mode == "literal" else _refit(state,frame,support)
                    transform = dict(helper=helper,normal=normal,before=before,after=after,
                                     frame_changes=edits, mode=mode, canonical_pair=pair_index,
                                     basis_indices=pair["basis_indices"],
                                     parent_semantic_sha256=state["raw_sha256"])
                except CandidateRejected as exc:
                    rejects[f"{type(exc).__name__}: {exc}"[:180]] += 1
                    continue
                # A failed exact identity, canonical replay assertion, dictionary
                # lookup, resource cap or infrastructure condition is an ERROR,
                # never an individual scientific rejection or a scoped NULL.
                raw, proof = _apply_transform(state,transform)
                old = {int(r):n for r,n in state["raw"]["report"]["local_profile"].items()}
                new = {int(r):n for r,n in raw["report"]["local_profile"].items()}
                delta = {r:new.get(r,0)-old.get(r,0) for r in sorted(set(old)|set(new))
                         if new.get(r,0)!=old.get(r,0)}
                witnesses.append(dict(provider=spec["provider"],group=spec["group"],mode=mode,
                                      helper=helper,normal=normal,canonical_pair=pair_index,
                                      basis_indices=pair["basis_indices"],
                                      certificate_status=proof["status"],
                                      local_profile=new,local_profile_delta=delta,
                                      width_inventory=raw["report"]["width_inventory"],
                                      private_buffers=len(raw["helper_final"]),
                                      frame_edits=len(edits),input_gates=len(before),output_gates=len(after),
                                      semantic_sha256=semantic_sha(raw),
                                      independent_full_semantic_audit="PENDING",
                                      native_admission="PENDING",complete_cost="PENDING"))
    return dict(status="NOMINEES" if witnesses else "NULL_BOUNDED_GRAMMAR",
                protocol="G1-PAIRED-GRAMMAR", provider=spec["provider"], seed=spec["seed"],
                seed_effect="task traversal only; exact bases and bounded choices identical",
                group=spec["group"], mode=mode, normals=group["normals"],
                output_registers=list(R), spaces=meta, pair_cap=PAIR_CAP,pivot_cap=PIVOT_CAP,
                eligible_pivots=len(pivots),retained_pivots=retained_pivots,
                truncated_pivots_per_pair=max(0,len(pivots)-PIVOT_CAP),
                attempted_constructions=constructions,rejections=dict(rejects),witnesses=witnesses,
                source_attribution=deepcopy(state["attribution"]),
                parent_semantic_sha256=state["raw_sha256"],cpu_seconds=time.process_time()-started,
                completeness="Only the registered canonical basis pairs and bounded pivots; no saturation claim",
                certification_scope="Eight literal paired identities and canonical frame/cleanup invoice; full independent admission remains required")
