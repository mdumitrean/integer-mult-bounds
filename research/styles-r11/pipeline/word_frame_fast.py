"""Exact N2 token projection without rebuilding derived WordData per sample.

The lattice graph, proposal sweep, random calls, nesting/profile acceptance and
final graph-profile assertion are inherited unchanged from nulls.FrameSampler.
Only _write differs: calibration mid/rank/op/role/registers tokens are projected
from the accepted frame assignment at the original event occurrences. Full
paid-climb tokens and raw words materialize through the original exact writer.

accelerate(word_tasks, enabled=True) is explicit and mutates only prepared
in-memory sampler caches. No experiment is launched and no file is written.
"""
from __future__ import annotations

from collections import Counter
import random
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import nulls
import wordio


class FrameView:
    def __init__(self, sampler, assignment, update_profile=False):
        self.sampler = sampler
        self.assignment = dict(assignment)
        self.update_profile = update_profile
        self._materialized = None
        original = sampler.word
        self.attribution = original.attribution
        self.family = original.family
        self.path = original.path
        paid = Counter(sampler.graph.profile(self.assignment))
        paid.update(original.centre_paid)
        self.paid = dict(sorted(paid.items()))
        if not update_profile:
            assert self.paid == original.paid, ("N2 fast projection changed paid profile", self.paid, original.paid)
        self.rank_at = {}
        for k, frame in assignment.items():
            _, _, section, index = sampler.graph.nodes[k]
            if section == "A":
                source_index = sampler.meta["A_idx"][index] if sampler.meta is not None else index
                self.rank_at["A", source_index] = len(frame)
            elif section == "B":
                self.rank_at["B", index] = len(frame)
            elif section == "tail":
                if sampler.meta is not None:
                    self.rank_at["restore", index] = len(frame)
                else:
                    source_index = original.raw["early_cleanup"][index][0]
                    self.rank_at["early_cleanup", source_index] = len(frame)

    def _materialize(self):
        if self._materialized is None:
            self._materialized = nulls.FrameSampler._write(self.sampler, self.assignment,
                                                           update_profile=self.update_profile)
            assert self._materialized.paid == self.paid
        return self._materialized

    def __getattr__(self, name):
        return getattr(self._materialize(), name)

    def section_tokens(self, alphabet="mid", sections=wordio.FORWARD_SECTIONS, relabel=None):
        if alphabet == "full":
            # Paid dt/ds depend on neighbouring accepted frames. Reuse the
            # original canonical replay instead of approximating those labels.
            return self._materialize().section_tokens(alphabet, sections, relabel)
        if alphabet not in wordio.ALPHABETS:
            raise ValueError(alphabet)
        answer = []
        for event in self.sampler.word.section_events(sections):
            token = event.project(alphabet, relabel)
            rank = self.rank_at.get((event.section, event.index)) if event.origin != "Bwarp" else None
            if rank is not None:
                if alphabet == "mid": token = (*token[:3], rank)
                elif alphabet == "rank": token = (token[0], rank)
                elif alphabet == "registers": token = (*token[:5], rank)
            answer.append(token)
        return answer


class FastFrameSampler(nulls.FrameSampler):
    @classmethod
    def from_reference(cls, reference):
        """Share the already constructed immutable graph, domains and edge map."""
        result = cls.__new__(cls)
        result.__dict__.update(reference.__dict__)
        return result

    def _write(self, assignment, update_profile=False):
        return FrameView(self, assignment, update_profile)


def accelerate(word_tasks_module, *, enabled=False, commuting=True, frames=True):
    """Explicit parent-only switch after registration; certify all N1b pairs.

    Existing samplers are retained as reference_commuting/reference_frames for
    the registered seed-for-seed verification. New samples use the same RNG
    sequence and the same finite-state sampler as those references.
    """
    if not enabled:
        return dict(enabled=False, words=[])
    from word_commute_fast import FastCommutingSampler
    reports = []
    for path, state in word_tasks_module._CACHE.items():
        word = state["word"]
        row = dict(path=path, attribution=word.attribution)
        if commuting:
            if "commuting" not in state:
                state["commuting"] = nulls.CommutingSampler(word)
            state.setdefault("reference_commuting", state["commuting"])
            if not isinstance(state["commuting"], FastCommutingSampler):
                state["commuting"] = FastCommutingSampler(word)
            row["commutation_predicate_certificate"] = state["commuting"].certify_predicate()
        if frames:
            if "frames" not in state:
                state["frames"] = nulls.FrameSampler(word)
            state.setdefault("reference_frames", state["frames"])
            if not isinstance(state["frames"], FastFrameSampler):
                state["frames"] = FastFrameSampler.from_reference(state["frames"])
            row["frame_transition_logic"] = "unchanged inherited FrameSampler.walk; only lazy output projection"
        reports.append(row)
    return dict(enabled=True, commuting=commuting, frames=frames, words=reports)


def equivalence_control(word, seed, reference=None, fast=None):
    """Registered reference equality for all six alphabets and paid profiles."""
    reference = reference or nulls.FrameSampler(word)
    fast = fast or FastFrameSampler.from_reference(reference)
    reference_rng, fast_rng = random.Random(seed), random.Random(seed)
    reference_t0, reference_c0 = time.monotonic(), time.process_time()
    original, original_info = reference.walk(reference_rng)
    reference_seconds = time.monotonic() - reference_t0
    reference_cpu_seconds = time.process_time() - reference_c0
    fast_t0, fast_c0 = time.monotonic(), time.process_time()
    projected, projected_info = fast.walk(fast_rng)
    fast_seconds = time.monotonic() - fast_t0
    fast_cpu_seconds = time.process_time() - fast_c0
    assert original_info == projected_info
    assert original.paid == projected.paid
    assert reference_rng.getstate() == fast_rng.getstate()
    # Mid comes first so its non-materializing path is tested independently.
    checked = {}
    token_t0, token_c0 = time.monotonic(), time.process_time()
    for alphabet in ("mid", "rank", "op", "role", "registers", "full"):
        eq = original.section_tokens(alphabet) == projected.section_tokens(alphabet)
        assert eq, ("N2 projected tokens differ", alphabet)
        checked[alphabet] = eq
    return dict(status="PASS", attribution=word.attribution, seed=seed,
                paid_profile_equal=True, all_alphabet_tokens_equal=checked,
                seed_identical_rng_state=True, diagnostics=projected_info,
                timings=dict(reference_seconds=reference_seconds, reference_cpu_seconds=reference_cpu_seconds,
                             accelerated_seconds=fast_seconds, accelerated_cpu_seconds=fast_cpu_seconds,
                             token_comparison_seconds=time.monotonic() - token_t0,
                             token_comparison_cpu_seconds=time.process_time() - token_c0,
                             measured_scope="one walk and lazy view; all-alphabet comparison separately timed"))


def verification_task(args):
    """pool.py worker after parent accelerate(...,enabled=True)."""
    import word_tasks
    from word_commute_fast import equivalence_control as commute_check
    state = word_tasks._state(args["path"])
    word, seed = state["word"], args["seed"]
    return dict(status="PASS", attribution=word.attribution, seed=seed,
                N1b=commute_check(word, seed, sweeps=args.get("sweeps", 1), sampler=state["commuting"]),
                N2=equivalence_control(word, seed, reference=state["reference_frames"], fast=state["frames"]))
