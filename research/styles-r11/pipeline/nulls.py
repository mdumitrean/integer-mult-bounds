"""Registered word controls N0, N1, N1b, N1c, N2 and N2b.

N1b uses toolkit frames.move_window/moved and rechecks each crossed pair with
frames.commute. The toolkit's scalar predicate is extended to formal operator
warps exactly: disjoint registers commute; scalar scales commute with warps;
warps on the same register commute only for the same generator up to inverse.
This is the auditor's free-operator algebra, not the discarded dataflow null.

N2 is a symmetric single-vertex Metropolis walk in the exact finite frame
lattice. Both nesting and the entire paid histogram are hard constraints. It is
not claimed to mix uniformly; accepted moves and degeneracy are always returned.
"""
from __future__ import annotations

import copy
import random
import signal
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wordio


def _rng(seed_or_rng):
    return seed_or_rng if isinstance(seed_or_rng, random.Random) else random.Random(seed_or_rng)


def N0(tokens, seed_or_rng):
    """Iid draws from empirical unigram frequencies, retaining total length."""
    rng = _rng(seed_or_rng)
    return [rng.choice(tokens) for _ in tokens] if tokens else []


def N1(events, seed_or_rng, alphabet="mid"):
    """Shuffle independently within contiguous sections; cleanup is inadmissible."""
    rng = _rng(seed_or_rng)
    result = []
    blocks = []
    for event in events:
        if event.section in ("cleanup", "compensation"):
            raise ValueError("Derived cleanup/compensation cannot be independent N1 text")
        if not blocks or blocks[-1][0].section != event.section:
            blocks.append([])
        blocks[-1].append(event)
    for block in blocks:
        shuffled = block[:]
        rng.shuffle(shuffled)
        result.extend(e.project(alphabet) for e in shuffled)
    return result


def section_shuffle(word, seed_or_rng, alphabet="mid", sections=wordio.FORWARD_SECTIONS):
    return N1(word.section_events(sections), seed_or_rng, alphabet)


class CommutingSampler:
    """Independent samples: one random visitation sweep from the shipped order.

    Every original gate occurrence is visited exactly once per sweep and moved
    uniformly within its current exact commutation window (endpoints included).
    The visitation permutation and every destination are seeded. Gate-attached
    token labels are transported, so N1b preserves the per-section multiset.
    Frame admissibility of reordered programs is NOT asserted by this semantic
    null; N2 is the distinct frame-assignment control.
    """
    def __init__(self, word, sections=wordio.FORWARD_SECTIONS, cache_pairs=500000):
        self.word = word
        self.events = word.section_events(sections)
        if any(e.section in ("cleanup", "compensation") for e in self.events):
            raise ValueError("Derived sections are not independent null text")
        self.frames, _ = wordio.toolkit()
        self.scalar_commute = self.frames.commute
        self.blocks = []
        for event in self.events:
            if not self.blocks or self.blocks[-1][0].section != event.section:
                self.blocks.append([])
            self.blocks[-1].append(event)

        @lru_cache(maxsize=cache_pairs)
        def commute(a, b):
            g1, g2 = self.events[a].gate, self.events[b].gate
            if g1[0] != "warp" and g2[0] != "warp":
                return self.scalar_commute(g1, g2)
            if g1[0] != "warp":
                g1, g2 = g2, g1
            if g2[0] == "scale":
                return True
            if g2[0] == "add":
                return g1[1] not in g2[1:3]
            return g1[1] != g2[1] or abs(g1[2]) == abs(g2[2])
        self._commute = commute
        self._indices = {id(event): i for i, event in enumerate(self.events)}
        self._gate_ids = {id(event.gate): i for i, event in enumerate(self.events)}

    def sample_events(self, seed_or_rng, sweeps=1):
        rng = _rng(seed_or_rng)
        before = self.frames.commute
        # frames.move_window dynamically resolves this module-level predicate.
        # Workers are single-threaded; the context is restored even on failure.
        self.frames.commute = lambda a, b: self._commute(self._gate_ids[id(a)], self._gate_ids[id(b)])
        output = []
        metadata = dict(null="N1b", sweeps=sweeps, attempted_moves=0, moved_gates=0,
                        crossed_pairs=0, invariant_failures=0,
                        protocol="one uniformly located move per gate in a randomized visitation sweep",
                        exact_semantics="scalar gates plus formal operator warps")
        try:
            for block in self.blocks:
                order = [self._indices[id(e)] for e in block]
                gates = [self.events[i].gate for i in order]
                locations = {value: i for i, value in enumerate(order)}
                for _ in range(sweeps):
                    visit = order[:]
                    rng.shuffle(visit)
                    for occurrence in visit:
                        i = locations[occurrence]
                        lo, hi = self.frames.move_window(gates, i)
                        j = rng.randint(lo, hi)
                        metadata["attempted_moves"] += 1
                        if i == j:
                            continue
                        crossed = range(j, i) if j < i else range(i + 1, j + 1)
                        for k in crossed:
                            if not self.frames.commute(gates[i], gates[k]):
                                metadata["invariant_failures"] += 1
                                raise AssertionError(("noncommuting move", i, j, k))
                            metadata["crossed_pairs"] += 1
                        gates = self.frames.moved(gates, i, j)
                        moved_id = order.pop(i)
                        order.insert(j, moved_id)
                        for k in range(min(i, j), max(i, j) + 1):
                            locations[order[k]] = k
                        metadata["moved_gates"] += 1
                assert sorted(order) == sorted(self._indices[id(e)] for e in block)
                output.extend(self.events[i] for i in order)
        finally:
            self.frames.commute = before
        metadata["cache"] = self._commute.cache_info()._asdict()
        metadata["degenerate"] = metadata["moved_gates"] == 0
        return output, metadata

    def sample(self, seed_or_rng, alphabet="mid", sweeps=1):
        events, metadata = self.sample_events(seed_or_rng, sweeps)
        return [e.project(alphabet) for e in events], metadata


def commuting_window(word, seed_or_rng, alphabet="mid", sweeps=1, sampler=None):
    return (sampler or CommutingSampler(word)).sample(seed_or_rng, alphabet, sweeps)


def register_relabelling(word, seed_or_rng):
    """Permute port, target and helper classes independently, including buffers."""
    rng = _rng(seed_or_rng)
    mapping = {}
    helper_classes = defaultdict(list)
    for r in range(2 * word.v, word.n):
        helper_classes[word.role[r]].append(r)
    for cls in (range(word.v), range(word.v, 2 * word.v), *helper_classes.values()):
        old = list(cls)
        new = old[:]
        rng.shuffle(new)
        mapping.update(zip(old, new))
    mapping.update({r + word.n: mapping[r] + word.n for r in range(word.n)})
    return mapping


def N1c(word, seed_or_rng, alphabet="mid", sections=wordio.FORWARD_SECTIONS):
    mapping = register_relabelling(word, seed_or_rng)
    tokens = word.section_tokens(alphabet, sections, relabel=mapping)
    return tokens, dict(null="N1c", relabelled_registers=sum(r != mapping[r] for r in range(word.n)),
                       note="A bijection preserves token equality, so equality-only compression/entropy must be invariant.")


class FrameSampler:
    """Exact frame graph + profile-preserving local proposal walk.

    Uses Graph.lower/upper and full finite domains for FULL, and BorrowGraph's
    warp-split exact lattice for BORROW. That lattice includes the Bounds pins
    and pins the end of every virtual life to its exact pre-warp frame.
    """
    def __init__(self, word):
        self.word = word
        F, W = wordio.toolkit()
        if word.family == "BORROW-WORD":
            _, _, bp = wordio.borrow_modules()
            inline, self.meta = bp.build_problem(word.raw)
            self.graph = bp.BorrowGraph(inline, self.meta["eq_end"], check_literal=True,
                                        tail_mutable=True, cut_equality=True)
        else:
            self.meta = None
            self.graph = F.Graph(W.inline(word.raw, True), check_literal=True,
                                 tail_mutable=True, cut_equality=True)
        self.F = F
        g = self.graph
        self.literal = {k: tuple(g.nodes[k][1]) for k in g.var}
        self.profile = dict(g.profile(self.literal))
        prof = Counter(self.profile)
        prof.update(word.centre_paid)
        assert dict(prof) == word.paid, ("graph profile mismatch", dict(prof), word.paid)
        self.variables = list(g.var)
        self.domains = {k: tuple(tuple(frame) for frame in g.dom[k]) for k in g.var}
        self.edges = {}
        for k in self.variables:
            related = set()
            for r in g.nodes[k][0]:
                if (k, r) in g.prev: related.add((g.prev[k, r], k, r))
                if (k, r) in g.nxt: related.add((k, g.nxt[k, r], r))
            self.edges[k] = tuple(related)

    def _write(self, assignment, update_profile=False):
        w = copy.deepcopy(self.word.raw)
        g = self.graph
        for k, frame in assignment.items():
            _, _, sec, idx = g.nodes[k]
            if sec == "A":
                index = self.meta["A_idx"][idx] if self.meta is not None else idx
                w["A"][index][-1] = list(frame)
            elif sec == "B":
                w["B"][idx][-1] = list(frame)
            elif sec == "tail":
                if self.meta is not None:
                    w["restore"][idx][-1] = list(frame)
                else:
                    w["early_cleanup"][idx][1] = list(frame)
        if update_profile:
            p = Counter(g.profile(assignment))
            p.update(self.word.centre_paid)
            w["report"]["local_profile"] = {str(k): v for k, v in p.items()}
        return wordio.WordData(w, self.word.attribution, assert_profile=True)

    def walk(self, seed_or_rng, steps=None, start=None):
        rng = _rng(seed_or_rng)
        assignment = dict(self.literal if start is None else start)
        g = self.graph
        current = lambda k: assignment.get(k, tuple(g.nodes[k][1]))
        metadata = dict(null="N2", attempts=0, accepted_moves=0, identity_proposals=0,
                        profile_rejections=0, feasibility_rejections=0, invariant_failures=0,
                        variables=len(self.variables), proposal="randomized single vertex sweep and uniform exact lattice domain" if steps is None else "uniform vertex and uniform exact lattice domain",
                        mixing="local Metropolis chain; no uniformity or mixing claim")
        if self.variables:
            if steps is None:
                proposal_order = self.variables[:]
                rng.shuffle(proposal_order)
            else:
                proposal_order = [rng.choice(self.variables) for _ in range(steps)]
            for k in proposal_order:
                metadata["attempts"] += 1
                old = assignment[k]
                new = rng.choice(self.domains[k])
                if old == new:
                    metadata["identity_proposals"] += 1
                    continue
                delta = Counter()
                valid = True
                for left, right, r in self.edges[k]:
                    before_l, before_r = current(left), current(right)
                    after_l = new if left == k else before_l
                    after_r = new if right == k else before_r
                    if not wordio.contained(after_l, after_r):
                        valid = False
                        break
                    old_rank = len(before_r) - len(before_l)
                    new_rank = len(after_r) - len(after_l)
                    if old_rank: delta[old_rank] -= 1
                    if new_rank: delta[new_rank] += 1
                if not valid:
                    metadata["feasibility_rejections"] += 1
                elif any(delta.values()):
                    metadata["profile_rejections"] += 1
                else:
                    assignment[k] = new
                    metadata["accepted_moves"] += 1
        if dict(g.profile(assignment)) != self.profile:
            metadata["invariant_failures"] += 1
            raise AssertionError("N2 profile changed")
        changed = sum(assignment[k] != self.literal[k] for k in assignment)
        metadata.update(changed_vertices=changed, degenerate=not changed,
                        acceptance_rate=metadata["accepted_moves"] / max(1, metadata["attempts"]))
        return self._write(assignment), metadata


@contextmanager
def solver_timeout(seconds):
    """A solver receives at most 600 s; use outside permutation loops only."""
    seconds = min(600, max(1, int(seconds)))
    def expired(*args):
        raise TimeoutError(f"Frame optimum exceeded {seconds} seconds")
    previous = signal.signal(signal.SIGALRM, expired)
    prior_timer = signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if prior_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, *prior_timer)


def frame_walk(word, seed_or_rng, steps=None, sampler=None):
    return (sampler or FrameSampler(word)).walk(seed_or_rng, steps)


def optimal_frames_control(word, endpoint="0.001717409316335491", timeout=600, sampler=None):
    """N2b once per word: exact integer surrogate optimum, certification required.

    The certified flag proves optimality for toolkit Costs(endpoint), not a
    nonlinear global root. Shipped/optimum profiles and their costs are returned.
    """
    sampler = sampler or FrameSampler(word)
    F, _ = wordio.toolkit()
    begin = time.monotonic()
    with solver_timeout(timeout):
        costs = F.Costs(endpoint)
        result = F.optimal_frames(sampler.graph.w, costs, graph=sampler.graph,
                                  check_literal=True, interval=False)
    if not result["certified"]:
        return None, dict(null="N2b", status="UNCERTIFIED", certified=False,
                          seconds=time.monotonic() - begin, endpoint=endpoint,
                          parts=result["parts"])
    optimum = sampler._write(result["assign"], update_profile=True)
    metadata = dict(null="N2b", status="PASS", certified=True,
                    certification="exact integer moment surrogate, not global root",
                    endpoint=endpoint, cost=str(result["cost"]), literal_cost=str(result["literal_cost"]),
                    profile=optimum.paid, literal_profile=word.paid,
                    changed_vertices=sum(result["assign"][k] != sampler.literal[k] for k in sampler.literal),
                    seconds=time.monotonic() - begin, parts=result["parts"])
    return optimum, metadata


# Descriptive names and numbered aliases are both public.
N1b = commuting_window
N2 = frame_walk
N2b = optimal_frames_control
