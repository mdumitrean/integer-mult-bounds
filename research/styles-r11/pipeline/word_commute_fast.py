"""Exact NumPy execution of the registered commuting-window sweep.

For a gate at position i, frames.move_window stops just inside the nearest
noncommuting occurrence on either side. We precompute every such occurrence
ID, then locate the same two boundaries with an inverse-position array.

certify_predicate() MUST run in the parent before any samples: it compares
EVERY ordered pair within each section against the unchanged toolkit scalar
commute predicate and the registered formal-warp extension. Each move rechecks
that no certified conflict position lies in the crossed interval. Random.shuffle
and random.randint calls have exactly the same order/arguments as the reference
CommutingSampler, so seed-for-seed output equality is a required control.

This file launches no experiment, benchmark, or compilation on import.
"""
from __future__ import annotations

from collections import Counter
import random
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wordio


class FastCommutingSampler:
    def __init__(self, word, sections=wordio.FORWARD_SECTIONS, verify=False):
        self.word = word
        self.events = word.section_events(sections)
        if any(event.section in ("cleanup", "compensation") for event in self.events):
            raise ValueError("Derived sections are not independent null text")
        F, _ = wordio.toolkit()
        self.scalar_commute = F.commute
        blocks = []
        for event in self.events:
            if not blocks or blocks[-1][0].section != event.section:
                blocks.append([])
            blocks[-1].append(event)
        self.blocks = []
        self.certification = None
        for events in blocks:
            operations = np.array([{"add": 0, "scale": 1, "warp": 2}[e.gate[0]] for e in events], dtype=np.int8)
            targets = np.array([e.gate[1] for e in events], dtype=np.int32)
            sources = np.array([e.gate[2] if e.gate[0] == "add" else -1 for e in events], dtype=np.int32)
            generators = np.array([abs(e.gate[2]) if e.gate[0] == "warp" else -1 for e in events], dtype=np.int32)
            conflicts = []
            for i, operation in enumerate(operations):
                target, source = targets[i], sources[i]
                if operation == 0:
                    # add/add: a target equals the other source; add/scale and
                    # add/warp: the unary register equals either add register.
                    mask = np.where(operations == 0,
                                    (target == sources) | (targets == source),
                                    (targets == target) | (targets == source))
                elif operation == 1:
                    # Scalar scaling commutes with every scale and warp.
                    mask = (operations == 0) & ((target == targets) | (target == sources))
                else:
                    mask = ((operations == 0) & ((target == targets) | (target == sources))) | (
                        (operations == 2) & (target == targets) & (generators != generators[i]))
                ids = np.flatnonzero(mask).astype(np.int32)
                if i in ids:
                    raise AssertionError("A gate occurrence must commute with itself")
                ids.flags.writeable = False
                conflicts.append(ids)
            self.blocks.append(dict(events=events, conflicts=tuple(conflicts),
                                    positions_template=np.arange(len(events), dtype=np.int32)))
        if verify:
            self.certify_predicate()

    def reference_commute(self, left, right):
        """Unchanged toolkit scalar predicate plus the frozen warp extension."""
        if left[0] != "warp" and right[0] != "warp":
            return self.scalar_commute(left, right)
        if left[0] != "warp":
            left, right = right, left
        if right[0] == "scale":
            return True
        if right[0] == "add":
            return left[1] not in right[1:3]
        return left[1] != right[1] or abs(left[2]) == abs(right[2])

    def certify_predicate(self):
        """All-pairs exact equivalence; call once in the parent, record its cost."""
        if self.certification is not None:
            return dict(self.certification)
        t0, c0 = time.monotonic(), time.process_time()
        comparisons = 0
        scalar_pairs, warp_pairs, failures = 0, 0, 0
        sections = []
        for block in self.blocks:
            gates = [event.gate for event in block["events"]]
            n = len(gates)
            for i, gate in enumerate(gates):
                reference = np.fromiter((not self.reference_commute(gate, other) for other in gates),
                                        dtype=np.bool_, count=n)
                actual = np.zeros(n, dtype=np.bool_)
                actual[block["conflicts"][i]] = True
                if not np.array_equal(reference, actual):
                    failures += 1
                    mismatch = np.flatnonzero(reference != actual)[:8].tolist()
                    raise AssertionError(("commute matrix differs from toolkit", i, mismatch))
                comparisons += n
            nw = sum(g[0] == "warp" for g in gates)
            scalar_pairs += (n - nw) ** 2
            warp_pairs += n * n - (n - nw) ** 2
            sections.append(dict(section=block["events"][0].section, gates=n,
                                 ordered_pairs=n * n,
                                 conflicts=sum(len(x) for x in block["conflicts"])))
        self.certification = dict(all_ordered_pairs_verified=True, ordered_pairs=comparisons,
                                  scalar_pairs=scalar_pairs, formal_warp_pairs=warp_pairs,
                                  invariant_failures=failures, sections=sections,
                                  seconds=time.monotonic() - t0, cpu_seconds=time.process_time() - c0)
        return dict(self.certification)

    def sample_events(self, seed_or_rng, sweeps=1):
        if self.certification is None:
            raise RuntimeError("certify_predicate() must run in the parent before sampling")
        rng = seed_or_rng if isinstance(seed_or_rng, random.Random) else random.Random(seed_or_rng)
        result = []
        metadata = dict(null="N1b", sweeps=sweeps, attempted_moves=0, moved_gates=0,
                        crossed_pairs=0, invariant_failures=0,
                        protocol="one uniformly located move per gate in a randomized visitation sweep",
                        exact_semantics="scalar gates plus formal operator warps",
                        execution="nearest certified conflict; seed-identical to toolkit window sweep",
                        all_pairs_preverified=True)
        for block in self.blocks:
            events, conflicts = block["events"], block["conflicts"]
            order = block["positions_template"].copy()
            inverse = order.copy()
            n = len(order)
            for _ in range(sweeps):
                visit = order.tolist()
                rng.shuffle(visit)
                for occurrence in visit:
                    i = int(inverse[occurrence])
                    conflicting_positions = inverse[conflicts[occurrence]]
                    left = conflicting_positions[conflicting_positions < i]
                    right = conflicting_positions[conflicting_positions > i]
                    lo = int(left.max()) + 1 if left.size else 0
                    hi = int(right.min()) - 1 if right.size else n - 1
                    j = rng.randint(lo, hi)
                    metadata["attempted_moves"] += 1
                    if i == j:
                        continue
                    a, b = min(i, j), max(i, j)
                    # This is exactly the conjunction of the reference commute
                    # checks for every crossed gate: the all-pairs certificate
                    # identified the complete complement of commuting gates.
                    if np.any((conflicting_positions >= a) & (conflicting_positions <= b)):
                        metadata["invariant_failures"] += 1
                        raise AssertionError(("noncommuting move", i, j))
                    metadata["crossed_pairs"] += b - a
                    if j < i:
                        order[j + 1:i + 1] = order[j:i].copy()
                    else:
                        order[i:j] = order[i + 1:j + 1].copy()
                    order[j] = occurrence
                    inverse[order[a:b + 1]] = block["positions_template"][a:b + 1]
                    metadata["moved_gates"] += 1
            if not np.array_equal(np.sort(order), block["positions_template"]):
                raise AssertionError("Gate multiset changed")
            result.extend(events[int(i)] for i in order)
        metadata["degenerate"] = metadata["moved_gates"] == 0
        return result, metadata

    def sample(self, seed_or_rng, alphabet="mid", sweeps=1):
        events, metadata = self.sample_events(seed_or_rng, sweeps)
        return [event.project(alphabet) for event in events], metadata


def equivalence_control(word, seed, sweeps=1, sampler=None):
    """Registered verification worker: same seed, same order, same diagnostics.

    The caller is responsible for preregistration, pool.py and RESULT recording.
    This helper never self-launches or writes files.
    """
    import nulls
    fast = sampler or FastCommutingSampler(word, verify=True)
    reference = nulls.CommutingSampler(word)
    reference_rng, accelerated_rng = random.Random(seed), random.Random(seed)
    reference_t0, reference_c0 = time.monotonic(), time.process_time()
    left, left_meta = reference.sample_events(reference_rng, sweeps)
    reference_seconds = time.monotonic() - reference_t0
    reference_cpu_seconds = time.process_time() - reference_c0
    fast_t0, fast_c0 = time.monotonic(), time.process_time()
    right, right_meta = fast.sample_events(accelerated_rng, sweeps)
    fast_seconds = time.monotonic() - fast_t0
    fast_cpu_seconds = time.process_time() - fast_c0
    left_ids = [(e.section, e.index, e.origin) for e in left]
    right_ids = [(e.section, e.index, e.origin) for e in right]
    assert left_ids == right_ids
    assert reference_rng.getstate() == accelerated_rng.getstate()
    for name in ("attempted_moves", "moved_gates", "crossed_pairs", "invariant_failures", "degenerate"):
        assert left_meta[name] == right_meta[name], (name, left_meta[name], right_meta[name])
    return dict(status="PASS", attribution=word.attribution, seed=seed, sweeps=sweeps,
                seed_identical_order=True, seed_identical_rng_state=True,
                original_diagnostics=left_meta, accelerated_diagnostics=right_meta,
                predicate_certificate=fast.certification,
                timings=dict(reference_seconds=reference_seconds, reference_cpu_seconds=reference_cpu_seconds,
                             accelerated_seconds=fast_seconds, accelerated_cpu_seconds=fast_cpu_seconds,
                             measured_scope="one sample, excluding constructor and predicate certification"))
