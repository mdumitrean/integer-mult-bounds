"""Pinned word readers and canonical Lane A output language.

The canonical extraction is adapted from planning/A-lsys-word/extract_strings.py
and the pinned PR2679 audit frame calculus. FULL-WORD early cleanup follows the
vendored toolkit-rev3/word.py recount. No data file is imported or executed.

Six alphabets, each with section as its first field:
  full      (section, operation, coefficient, target_role, source_role,
             frame_rank, target_paid_climb, source_paid_climb)
  mid       (section, operation, coefficient, frame_rank)
  rank      (section, frame_rank)
  op        (section, operation, coefficient)
  role      (section, operation, coefficient, target_role, source_role)
  registers (section, operation, coefficient, target_register, source_register,
             frame_rank)
The first four are Lane A's exact projections. Roles are P/T/C/H/L/F/X with
BUFFER: prefixed for a restored-input buffer. Registers is deliberately sensitive
to index relabelling; equality-only statistics of it are invariant to a bijection.
All alphabet values use exact reduced rational coefficients, signed as in Lane A.
B warps are letters (including a warp after the last B gate); their op is WARP.
Cleanup and compensation are derived outputs and never independent screen text.
"""
from __future__ import annotations

import copy
import gzip
import hashlib
import importlib
import json
import os
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "research/styles-r11"
PINS_PATH = RESEARCH / "data/words/PINS.json"
ALPHABETS = ("full", "mid", "rank", "op", "role", "registers")
FORWARD_SECTIONS = ("A", "cut", "B")


def basis(vectors):
    """Canonical reduced F2 basis; descending integer pivots."""
    piv = {}
    for value in vectors:
        while value:
            bit = value.bit_length() - 1
            if bit in piv:
                value ^= piv[bit]
            else:
                piv[bit] = value
                break
    for bit in sorted(piv):
        for other in piv:
            if other > bit and (piv[other] >> bit) & 1:
                piv[other] ^= piv[bit]
    return tuple(piv[k] for k in sorted(piv, reverse=True))


def contained(a, b):
    return basis(tuple(a) + tuple(b)) == tuple(b)


@lru_cache(None)
def perp(port, h=9):
    return basis(x for x in range(1, 1 << h) if (x & port).bit_count() % 2 == 0)


def registers(gate):
    return tuple(gate[1:3] if gate[0] == "add" else gate[1:2])


def coefficient(gate):
    if gate[0] == "add":
        q = Fraction(gate[3], gate[4])
    elif gate[0] == "scale":
        q = Fraction(gate[2], gate[3])
    else:
        return "w"
    return ("+" if q > 0 else "-") + str(abs(q))


def read_json(path):
    """Read JSON as inert data, optionally gzip compressed."""
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith(".gz") else data)


@lru_cache(None)
def pins():
    return read_json(PINS_PATH)["files"]


def pinned_paths():
    return [(ROOT / key if "/" in key else PINS_PATH.parent / key,
             dict(info, pin_key=key)) for key, info in pins().items()]


def attribution_for(path, pin=None):
    path = Path(path).resolve()
    if pin is None:
        for candidate, metadata in pinned_paths():
            if candidate.resolve() == path:
                pin = metadata
                break
    if pin is None:
        raise ValueError(f"Missing source attribution for {path}; supply pin metadata")
    metadata = copy.deepcopy(pin)
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if metadata.get("sha256") and metadata["sha256"] != actual:
        raise ValueError(f"Compressed SHA256 mismatch for {path}")
    git_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if metadata.get("git_blob") and metadata["git_blob"] != git_blob:
        raise ValueError(f"Git blob mismatch for {path}")
    metadata.update(sha256=actual, git_blob=git_blob, path=str(path.relative_to(ROOT))
                    if path.is_relative_to(ROOT) else str(path))
    return metadata


@lru_cache(None)
def toolkit():
    """Load held, reviewed code only. Never load anything from a word's data path."""
    sys.dont_write_bytecode = True
    os.environ["IMB_ROOT"] = str(ROOT)
    path = str(ROOT / "research/t74-r10-hosting-leads/deps/toolkit-rev3")
    sys.path.insert(0, path)
    return importlib.import_module("frames"), importlib.import_module("word")


@lru_cache(None)
def borrow_modules():
    toolkit()
    path = str(ROOT / "research/t74-r10-hosting-leads/J-dim1/code")
    sys.path.insert(0, path)
    return tuple(importlib.import_module(name) for name in ("wordmodel", "bounds", "borrow_price"))


@dataclass(frozen=True)
class Event:
    section: str
    index: int
    gate: tuple
    token: tuple
    registers: tuple
    time: int
    origin: str = "literal"

    def project(self, alphabet="mid", relabel=None):
        t = self.token
        if alphabet == "full":
            return t
        if alphabet == "mid":
            return t[0], t[1], t[2], t[5]
        if alphabet == "rank":
            return t[0], t[5]
        if alphabet == "op":
            return t[:3]
        if alphabet == "role":
            return t[:5]
        if alphabet == "registers":
            rr = self.registers
            if relabel is not None:
                rr = tuple(relabel.get(r, r) for r in rr)
            return t[0], t[1], t[2], rr[0], (rr[1] if len(rr) > 1 else -1), t[5]
        raise ValueError(f"Unknown alphabet {alphabet!r}")


class WordData:
    def __init__(self, raw, attribution, path=None, assert_profile=True):
        self.raw = raw
        self.w = raw
        self.attribution = copy.deepcopy(attribution)
        self.path = str(path) if path is not None else None
        self.family = "BORROW-WORD" if raw.get("kind") == "BORROW-WORD" or "warps" in raw else "FULL-WORD"
        self.v, self.h, self.R = (raw["report"][k] for k in ("v", "h", "R"))
        self.n = 2 * self.v + self.R
        self.full = basis(1 << k for k in range(self.h))
        self.removed = set(raw.get("removed", []))
        self.live = [r for r in range(self.n) if r not in self.removed]
        self.helpers = [r for r in self.live if r >= 2 * self.v]
        self.start = [(p,) for p in raw["ports"]] + [()] * (self.v + self.R)
        self.end = [self.full] * self.v + [perp(p, self.h) for p in raw["ports"]] + [self.full] * self.R
        for r, frame in raw.get("start_extra", {}).items():
            self.start[int(r)] = basis(frame)
        for r, frame in raw.get("helper_final", {}).items():
            self.end[int(r)] = basis(frame)
        self._extract()
        self.expected_profile = {int(k): v for k, v in raw["report"]["local_profile"].items()}
        self.profile_match = self.paid == self.expected_profile
        if assert_profile:
            assert self.profile_match, (self.attribution.get("path"), self.paid, self.expected_profile)
            expected_width = {int(k): v for k, v in raw["report"]["width_inventory"].items()}
            actual_width = dict(Counter(len(self.end[r]) - len(self.start[r]) for r in self.helpers))
            assert actual_width == expected_width, ("width_inventory", actual_width, expected_width)

    def _extract(self):
        w, v = self.raw, self.v
        centres = set(w["centers"])
        warp_regs = {rec[1] for rec in w.get("warps", [])}
        warped = set()
        def role(r):
            if r >= self.n:
                return "BUFFER:" + role(r - self.n)
            if r in self.removed: return "X"
            if r in centres: return "C"
            if r < v: return "P"
            if r < 2 * v: return "T"
            if r in warp_regs: return "F" if r in warped else "L"
            return "H"
        self.role = {r: role(r) for r in range(self.n)}
        cur = list(self.start)
        paid = Counter()
        centre_paid = Counter()
        jumps = defaultdict(list)
        chains = {r: [{"section": "start", "index": -1, "dimension": len(cur[r]), "kind": "start"}]
                  for r in self.live}
        events = []
        touches = defaultdict(list)

        def climb(r, frame, section, index):
            frame = basis(frame or ())
            assert r not in self.removed, ("removed register touched", r)
            assert contained(cur[r], frame), ("frame violation", section, index, r, cur[r], frame)
            delta = len(frame) - len(cur[r])
            if delta:
                paid[delta] += 1
                jumps[r].append(dict(section=section, index=index, rank=delta,
                                     **{"from": cur[r], "to": frame}, kind="climb"))
            cur[r] = frame
            chains[r].append(dict(section=section, index=index, dimension=len(frame), kind="climb"))
            return delta

        def emit(sec, index, e, framed=False, origin="literal"):
            rr = registers(e)
            if e[0] == "warp":
                frame = basis(e[-1])
                if sec in ("A", "B"):
                    old = basis(e[-2])
                    assert cur[e[1]] == old, ("warp frame mismatch", sec, index, e[1])
                    cur[e[1]] = frame
                    chains[e[1]].append(dict(section=sec, index=index, dimension=len(frame), kind="warp"))
                if sec == "B":
                    tok = (sec, "WARP", "w", "L>F", "-", len(frame), 0, 0)
                    warped.add(e[1])
                else:
                    tok = (sec, "warp", "w", role(e[1]), "-", len(frame), 0, 0)
            else:
                dt = climb(e[1], e[-1], sec, index) if framed else 0
                ds = climb(e[2], e[-1], sec, index) if framed and e[0] == "add" else 0
                tok = (sec, e[0], coefficient(e), role(e[1]), role(e[2]) if e[0] == "add" else "-",
                       len(basis(e[-1] or ())), dt, ds)
            event = Event(sec, index, tuple(tuple(x) if isinstance(x, list) else x for x in e),
                          tok, rr, len(events), origin)
            events.append(event)
            for r in rr:
                if r < self.n:
                    touches[r].append(event)

        for sec in ("precondition", "compensation", "A", "cut", "B", "restore"):
            if sec == "B":
                lev = {int(t): basis(frame) for t, frame in w.get("target_levels", {}).items()}
                for r, frame in zip(w["centers"], w["center_frames"]):
                    frame = basis(frame)
                    assert cur[r] == frame, ("centre frame", r, cur[r], frame)
                    served = sorted({lev.get(e[1] - v, ()) for e in w["cut"] if e[2] == r}, key=lambda f: (-len(f), f))
                    for j, target in enumerate(served):
                        assert contained(target, frame), ("centre path not nested", r)
                        if target != frame:
                            delta = len(frame) - len(target)
                            paid[delta] += 1
                            centre_paid[delta] += 1
                            jumps[r].append(dict(section="cut", index=j, rank=delta,
                                                 **{"from": frame, "to": target}, kind="centre_descent"))
                            chains[r].append(dict(section="cut", index=j, dimension=len(target), kind="centre_descent"))
                        frame = target
                for t in range(v):
                    assert cur[v + t] == lev.get(t, ()), ("target level", t)
            if sec == "B":
                bypos = defaultdict(list)
                for op, record in enumerate(w.get("warps", []), 1):
                    bypos[record[0]].append((op, record))
                for index in range(len(w["B"]) + 1):
                    for op, rec in bypos[index]:
                        emit("B", op, ["warp", rec[1], op, rec[3], rec[4]], origin="Bwarp")
                    if index < len(w["B"]):
                        emit("B", index, w["B"][index], framed=True)
            else:
                for index, gate in enumerate(w.get(sec, [])):
                    emit(sec, index, gate, framed=sec in ("A", "restore"))
        early = w.get("early_cleanup", [])
        early_ids = set()
        for order, (index, frame) in enumerate(early):
            assert index not in early_ids, ("duplicate early cleanup", index)
            early_ids.add(index)
            emit("early_cleanup", index, list(w["cleanup"][index][:-1]) + [frame], framed=True)
        for r in self.live:
            climb(r, self.end[r], "end", -1)
        for index, gate in enumerate(w.get("cleanup", [])):
            if index not in early_ids:
                emit("cleanup", index, gate)
        self.paid = dict(sorted(paid.items()))
        self.centre_paid = dict(sorted(centre_paid.items()))
        self.events = events
        self.forward = [e for e in events if e.section in FORWARD_SECTIONS]
        self.climbs = {}
        self.touches = touches
        for r in self.live:
            tt = [e for e in touches[r] if e.section in FORWARD_SECTIONS]
            self.climbs[r] = dict(role=self.role[r], final_role=role(r), entrance_dim=len(self.start[r]),
                                  end_dim=len(self.end[r]), width=len(self.end[r]) - len(self.start[r]),
                                  jumps=jumps[r], dimensions=chains[r],
                                  first_motif=tt[0].token[1:] if tt else None,
                                  last_motif=tt[-1].token[1:] if tt else None)

    def section_events(self, sections=FORWARD_SECTIONS):
        return [event for event in self.events if event.section in sections]

    def section_tokens(self, alphabet="mid", sections=FORWARD_SECTIONS, relabel=None):
        return [event.project(alphabet, relabel) for event in self.section_events(sections)]

    def cleanup_check(self, scalar_replay=True):
        return cleanup_check(self, scalar_replay=scalar_replay)

    def summary(self):
        return dict(attribution=self.attribution, family=self.family, registers=self.n,
                    live_registers=len(self.live), helpers=len(self.helpers), paid=self.paid,
                    report_profile=self.expected_profile, profile_match=self.profile_match,
                    centre_paid=self.centre_paid,
                    sections=dict(Counter(e.section for e in self.events)),
                    alphabets={a: len(set(self.section_tokens(a))) for a in ALPHABETS})


def load(path, pin=None, assert_profile=True):
    path = Path(path)
    if not path.exists():
        path = PINS_PATH.parent / path
    return WordData(read_json(path), attribution_for(path, pin), path, assert_profile)


Word = load


def inverse(gate, frame=None):
    e = list(gate)
    if e[0] == "add":
        e[3] = -e[3]
    elif e[0] == "scale":
        e[2], e[3] = e[3], e[2]
    elif e[0] == "warp":
        e = ["warp", e[1], -e[2], frame]
    else:
        raise ValueError(e[0])
    if frame is not None:
        e[-1] = list(frame)
    return e


def _normal_gate(gate):
    if gate[0] == "warp":
        return "warp", gate[1], gate[2], basis(gate[-1])
    q = Fraction(gate[3], gate[4]) if gate[0] == "add" else Fraction(gate[2], gate[3])
    return gate[0], registers(gate), q.numerator, q.denominator, basis(gate[-1] or ())


def derived_borrow_cleanup(word):
    w, v, n = word.raw, word.v, word.n
    restored = set(map(int, w.get("helper_final", {})))
    recorded = [list(e) for e in w["A"][w.get("prelude_events", 0):]]
    bypos = defaultdict(list)
    for op, rec in enumerate(w["warps"], 1):
        bypos[rec[0]].append(["warp", rec[1], op, list(word.full)])
    for i in range(len(w["B"]) + 1):
        recorded.extend(bypos[i])
        if i < len(w["B"]):
            recorded.append(w["B"][i])
    recorded.extend(w.get("restore", []))
    recorded = [e for e in recorded if e[0] == "warp" or not v <= e[1] < 2 * v]
    result = []
    for e in reversed(recorded):
        g = inverse(e, word.full)
        for pos in ([1, 2] if g[0] == "add" else [1]):
            if g[pos] in restored:
                g[pos] += n
        result.append(g)
    return result


def _apply_scalar(gate, rows, dual=False):
    if gate[0] == "add":
        target, source = gate[1:3]
        q = Fraction(gate[3], gate[4])
        if dual:
            target, source, q = source, target, -q
        dst = rows[target]
        for key, value in list(rows[source].items()):
            new = dst.get(key, Fraction()) + q * value
            if new: dst[key] = new
            else: dst.pop(key, None)
    elif gate[0] == "scale":
        target = gate[1]
        q = Fraction(gate[2], gate[3])
        if dual: q = 1 / q
        rows[target] = {key: q * value for key, value in rows[target].items()}
    else:
        raise ValueError("Scalar replay excludes operator warps")


def cleanup_check(word, scalar_replay=True):
    """Exact literal production for BORROW; exact endpoint for refactored FULL.

    FULL cleanup is Gauss-Jordan refactored and its gate list is not the literal
    reverse of A+B. Return both facts separately; an endpoint pass cannot turn
    a false literal gate-list equality into a pass.
    """
    w = word.raw
    if word.family == "BORROW-WORD":
        derived = derived_borrow_cleanup(word)
        supplied = w.get("cleanup", derived)
        equal = list(map(_normal_gate, derived)) == list(map(_normal_gate, supplied))
        return dict(attribution=word.attribution, family=word.family,
                    production="reverse(inverse(buffer(recorded A after prelude + B warps + B + restore)))",
                    recorded_gates=len(derived), cleanup_gates=len(supplied), literal_equality=equal,
                    exact=equal, status="PASS" if equal else "FAIL",
                    first_mismatch=next((i for i, (a, b) in enumerate(zip(derived, supplied))
                                         if _normal_gate(a) != _normal_gate(b)), None))
    main = w["A"] + w["cut"] + w["B"]
    recorded = [e for e in w["A"] + w["B"] if not word.v <= e[1] < 2 * word.v]
    simple = [inverse(e, word.full) for e in reversed(recorded)]
    literal = list(map(_normal_gate, simple)) == list(map(_normal_gate, w["cleanup"]))
    result = dict(attribution=word.attribution, family=word.family,
                  production="FULL refactored cleanup with ordered early_cleanup and derived compensation",
                  literal_equality=literal, cleanup_gates=len(w["cleanup"]),
                  expected_literal_production=False,
                  refactored_construction=w.get("refactored_cleanup", {}))
    if not scalar_replay:
        result.update(status="NOT_RUN", exact=None)
        return result
    ident = lambda: [{r: Fraction(1)} for r in range(word.n)]
    rows = ident()
    for e in main:
        _apply_scalar(e, rows)
    dirt = [{} for _ in range(word.n)]
    for target in range(word.v, 2 * word.v):
        dirt[target] = {k: c for k, c in rows[target].items() if k >= 2 * word.v}
    for e in w["precondition"]:
        _apply_scalar(e, dirt)
    compensation = [["add", target, k, -c.numerator, c.denominator, []]
                    for target in range(word.v, 2 * word.v) for k, c in sorted(dirt[target].items())]
    early = w.get("early_cleanup", [])
    early_ids = {index for index, _ in early}
    cleanup = [w["cleanup"][i][:-1] + [f] for i, f in early]
    cleanup += [e for i, e in enumerate(w["cleanup"]) if i not in early_ids]
    program = w["precondition"] + compensation + main + cleanup
    checks = {}
    for dual in (False, True):
        actual, expected = ident(), ident()
        for e in program:
            _apply_scalar(e, actual, dual)
        for r in range(word.v):
            expected[r if dual else word.v + r][word.v + r if dual else r] = Fraction(-1 if dual else 1)
        bad = [r for r in range(word.n) if actual[r] != expected[r]]
        checks["dual" if dual else "forward"] = dict(passed=not bad, bad_registers=bad[:20])
    exact = all(row["passed"] for row in checks.values())
    result.update(exact=exact, status="PASS" if exact else "FAIL", endpoint_checks=checks,
                  compensation_gates=len(compensation), arithmetic="fractions.Fraction")
    return result
