"""Fixed M1/L-5 motif scoring and the actual retired7 path census.

Call prepare once in the parent, then task through pool.py after registration.
This module neither launches jobs nor writes files.  The exact Bounds/census is
from the pinned PR2679/PR2745 toolkit through matching.py.  Source words and
refit7 patch records are JSON data; later hostmove/alias outcomes are not inputs
to the score.  Unchosen augmenting paths are never assigned failure labels.
"""
from __future__ import annotations

from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import copy
from fractions import Fraction
import gzip
import hashlib
import io
import json
from pathlib import Path
import random
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import matching
import wordio
import word_tasks

REALIZED_PATHS = (
    ("follower:667", "segment:401", "hosted:30", "free:564"),
    ("follower:669", "segment:403", "hosted:31", "free:565"),
)
_EXPECTED_PATHS = 192
_STATES = {}
_PAIR_CACHE = {}
_PATH_CACHE = {}


def _artifact(path):
    path = Path(path)
    data = path.read_bytes()
    return dict(path=str(path.relative_to(wordio.ROOT)), sha256=hashlib.sha256(data).hexdigest(),
                git_blob=hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest())


def _role(raw, register):
    if register in raw["centers"]:
        return "C"
    v = raw["report"]["v"]
    return "P" if register < v else "T" if register < 2 * v else "H"


def _motif_token(raw, gate, focal):
    """No IDs, times, bounds, paid climbs, outcomes, or dynamic host roles."""
    op = gate[0]
    if op not in ("add", "scale"):
        raise ValueError("Only scalar gates enter local motifs")
    target = "SELF" if gate[1] == focal else _role(raw, gate[1])
    source = ("SELF" if gate[2] == focal else _role(raw, gate[2])) if op == "add" else "-"
    return op, wordio.coefficient(gate), len(wordio.basis(gate[-1])), target, source


def _ngrams(context):
    return Counter((size, tuple(context[i:i + size]))
                   for size in (1, 2, 3) for i in range(len(context) - size + 1))


def _contexts(bounds, lives, slots):
    raw = bounds.Wd.w
    scalar, warps = defaultdict(list), defaultdict(list)
    for time, (section, gate) in enumerate(bounds.ev):
        if section not in ("A", "B", "Bwarp", "restore"):
            continue
        if gate[0] == "warp":
            warps[gate[1]].append(time)
        elif gate[0] in ("add", "scale"):
            for register in wordio.registers(gate):
                scalar[register].append((time, gate))
    slot_contexts, life_contexts = {}, {}
    for slot, row in slots.items():
        register, last = row["register"], row["last"]
        boundaries = warps[register]
        index = bisect_right(boundaries, last)
        lower = boundaries[index - 1] if index else -1
        gates = [g for time, g in scalar[register] if lower < time <= last][-3:]
        slot_contexts[slot] = tuple(_motif_token(raw, g, register) for g in gates)
    for life, row in lives.items():
        register = row.get("register")
        if register is None:
            register = row["lender"]
        first = row["first"]
        boundaries = warps[register]
        index = bisect_right(boundaries, first)
        upper = boundaries[index] if index < len(boundaries) else len(bounds.ev)
        gates = [g for time, g in scalar[register] if first <= time < upper][:3]
        life_contexts[life] = tuple(_motif_token(raw, g, register) for g in gates)
    return life_contexts, slot_contexts


def prepare(variants=("base", "extra")):
    """Parent preparation only, with no calls to task or hidden experiment pool.

    Construct refit7 from pinned retired5 plus the explicit two-frame patch;
    all large Bounds/word/census objects are retained once for forked workers.
    """
    _, boundmod, _ = wordio.borrow_modules()
    summaries = []
    for variant in variants:
        if variant not in ("base", "extra"):
            raise ValueError(variant)
        if variant not in _STATES:
            predecessor_path = wordio.RESEARCH / f"data/words/retired5-WORD-{variant}.json.gz"
            predecessor = wordio.load(predecessor_path)
            patch_path = wordio.ROOT / f"research/t74-joint-twelve-retired7/inputs/refit7_43{variant}.json"
            patch = wordio.read_json(patch_path)
            raw = copy.deepcopy(predecessor.raw)
            for section, index, frame in patch["previous_frames"]:
                if raw[section][index][-1] != frame:
                    raise ValueError(("refit7 previous frame mismatch", variant, section, index))
            for section, index, frame in patch["frames"]:
                raw[section][index][-1] = copy.deepcopy(frame)
            raw["report"]["local_profile"] = copy.deepcopy(patch["local_profile"])
            data = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
            patch_source = _artifact(patch_path)
            patch_source["retained_credit"] = patch.get("credit")
            attribution = dict(
                path=f"derived:retired5-{variant}+refit7", pin_key=f"derived:refit7-{variant}",
                source_attribution=[predecessor.attribution], patch_source=patch_source,
                derived_json_sha256=hashlib.sha256(data).hexdigest(),
                source="Pinned retired5 word plus only the declared refit7 frame assignments")
            word = wordio.WordData(raw, attribution)
            bounds = boundmod.Bounds(io.BytesIO(gzip.compress(data, mtime=0)))
            census = matching.census(attribution["path"], bounds=bounds)
            lives, slots = matching.graph_data(census)
            adj = matching.adjacency(lives, slots)
            life_contexts, slot_contexts = _contexts(bounds, lives, slots)
            _STATES[variant] = dict(
                variant=variant, word=word, bounds=bounds, census=census,
                lives=lives, slots=slots, adj={k: set(v) for k, v in adj.items()},
                life_contexts=life_contexts, slot_contexts=slot_contexts,
                life_grams={k: _ngrams(v) for k, v in life_contexts.items()},
                slot_grams={k: _ngrams(v) for k, v in slot_contexts.items()},
                source_attribution=attribution)
        state = _STATES[variant]
        summaries.append(dict(variant=variant, source_attribution=state["source_attribution"],
                              exact_profile_match=state["word"].profile_match,
                              words_loaded_once_in_parent=True))
    return summaries


def _similarity(left, right):
    a, b = sum(left.values()), sum(right.values())
    if not a or not b:
        return Fraction(0)
    overlap = sum(min(count, right.get(gram, 0)) for gram, count in left.items())
    return Fraction(2 * overlap, a + b)


def _edge_score(state, life, slot):
    return _similarity(state["slot_grams"][slot], state["life_grams"][life])


def all_augmenting_paths(state):
    """Every legal length-3 path relative to the actually occupied slots."""
    lives, slots, adj = state["lives"], state["slots"], state["adj"]
    occupied_lives = {row["occupied_by"] for row in slots.values() if row["occupied_by"] is not None}
    paths = []
    for root in sorted(set(lives) - occupied_lives):
        for occupied in sorted(adj[root]):
            hosted = slots[occupied]["occupied_by"]
            if hosted is None:
                continue
            if hosted not in lives:
                raise ValueError(("occupied slot names absent life", occupied, hosted))
            for free in sorted(adj[hosted]):
                if slots[free]["occupied_by"] is None:
                    paths.append((root, occupied, hosted, free))
    if len(set(paths)) != len(paths):
        raise AssertionError("Duplicate augmenting path")
    if len(paths) != _EXPECTED_PATHS:
        raise ValueError(("registered path-count mismatch", state["variant"], len(paths), _EXPECTED_PATHS))
    for path in paths:
        root, occupied, hosted, free = path
        assert occupied in adj[root] and slots[occupied]["occupied_by"] == hosted
        assert free in adj[hosted] and slots[free]["occupied_by"] is None
    return paths


def _fraction(value):
    return dict(numerator=value.numerator, denominator=value.denominator, value=float(value))


def _rank_interval(scores, value):
    better = sum(s > value for s in scores)
    ties = sum(s == value for s in scores)
    return dict(best_rank=1 + better, worst_rank=better + ties,
                midrank=better + (ties + 1) / 2, tie_count=ties,
                top5_demonstrated=better + ties <= 5,
                top5_possible=better < 5)


def rank_paths(state):
    """Scores depend only on pre-host local motifs; realized IDs queried last."""
    variant = state["variant"]
    if variant in _PATH_CACHE:
        return _PATH_CACHE[variant]
    paths = all_augmenting_paths(state)
    scores, floor_scores, records = [], [], []
    lives, slots = state["lives"], state["slots"]
    for root, occupied, hosted, free in paths:
        one, two = _edge_score(state, root, occupied), _edge_score(state, hosted, free)
        score = (one + two) / 2
        floor_score = -((lives[root]["hi"] - slots[occupied]["lo"])
                        + (lives[hosted]["hi"] - slots[free]["lo"]))
        scores.append(score)
        floor_scores.append(floor_score)
        records.append(dict(path=[root, occupied, hosted, free],
                            motif_score=_fraction(score), edge_scores=[_fraction(one), _fraction(two)],
                            floor_slack_score=floor_score))
    realized = []
    for path in REALIZED_PATHS:
        if path not in paths:
            raise ValueError(("realized path absent", variant, path))
        index = paths.index(path)
        realized.append(dict(path=list(path), motif_score=_fraction(scores[index]),
                             motif_rank=_rank_interval(scores, scores[index]),
                             floor_slack_rank=_rank_interval(floor_scores, floor_scores[index]),
                             exact_guard_rank=_rank_interval([1] * len(paths), 1)))
    result = dict(variant=variant, candidate_paths=len(paths), all_paths=records,
                  realized_paths=realized,
                  ranking_bar_pass=all(r["motif_rank"]["top5_demonstrated"] for r in realized),
                  tie_rule="worst rank <=5; a display order never breaks a decision tie",
                  unselected_paths_labeled_negative=False)
    _PATH_CACHE[variant] = result
    return result


def _average_ranks(scores):
    ordered = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = np.empty(len(scores), dtype=float)
    index = 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and scores[ordered[end]] == scores[ordered[index]]:
            end += 1
        ranks[ordered[index:end]] = (index + 1 + end) / 2
        index = end
    return ranks


def _auc_from_ranks(labels, ranks):
    positives = int(np.sum(labels))
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    return float((np.dot(labels, ranks) - positives * (positives + 1) / 2)
                 / (positives * negatives))


def _pair_table(state):
    variant = state["variant"]
    if variant in _PAIR_CACHE:
        return _PAIR_CACHE[variant]
    lives, slots, adj = state["lives"], state["slots"], state["adj"]
    labels, scores = [], []
    for life in sorted(lives):
        for slot in sorted(slots):
            if slots[slot]["register"] == lives[life].get("register"):
                continue
            guard = (slots[slot]["last"] < lives[life]["first"]
                     and slots[slot]["lo"] <= lives[life]["hi"])
            assert guard == (slot in adj[life])
            labels.append(int(guard))
            scores.append(_edge_score(state, life, slot))
    label_array = np.asarray(labels, dtype=np.int8)
    motif_ranks, guard_ranks = _average_ranks(scores), _average_ranks(labels)
    actual = dict(motif=_auc_from_ranks(label_array, motif_ranks),
                  exact_guard=_auc_from_ranks(label_array, guard_ranks))
    assert actual["exact_guard"] in (None, 1.0)
    table = dict(labels=labels, motif_ranks=motif_ranks, guard_ranks=guard_ranks,
                 actual=actual, pairs=len(labels), positives=sum(labels),
                 missing_context_pairs=sum(not state["life_contexts"][life] or not state["slot_contexts"][slot]
                    for life in lives for slot in slots
                    if slots[slot]["register"] != lives[life].get("register")))
    _PAIR_CACHE[variant] = table
    return table


def task(args):
    """Pool task {variant, seed, start=0, n=10}; the root aggregates two seeds."""
    variant, seed = args.get("variant", "base"), args["seed"]
    if variant not in _STATES:
        raise RuntimeError("Call word_alias_score.prepare in the parent first")
    state = _STATES[variant]
    ranking = rank_paths(state)
    pairs = _pair_table(state)
    start, n = args.get("start", 0), args.get("n", 10)
    values = dict(motif=[], exact_guard=[])
    if pairs["actual"]["motif"] is None:
        raise ValueError("Feasibility AUC is undefined: the registered pair set has one class")
    for index in range(start, start + n):
        rng = random.Random(word_tasks.sample_seed(seed, variant, "L5:pair-labels", index))
        labels = pairs["labels"][:]
        rng.shuffle(labels)
        array = np.asarray(labels, dtype=np.int8)
        values["motif"].append(_auc_from_ranks(array, pairs["motif_ranks"]))
        values["exact_guard"].append(_auc_from_ranks(array, pairs["guard_ranks"]))
    actual = pairs["actual"]
    ranking_pass = ranking["ranking_bar_pass"]
    return dict(
        experiment="L-5", status="PASS", variant=variant, seed=seed, start=start, n=n,
        source_attribution=state["source_attribution"],
        ranking=ranking, real_auc=actual, null_auc=values,
        pair_summary={k: pairs[k] for k in ("pairs", "positives", "missing_context_pairs")},
        numerical_subbars=dict(guard_label_auc_at_least_0_9=actual["motif"] >= .9,
                               both_realized_paths_top5=ranking_pass,
                               auc_increment_over_exact_guard=actual["motif"] - actual["exact_guard"]),
        scientific_status="EXPLORATORY" if ranking_pass else "NULL",
        scientific_scope=("The complete beyond-floor question lacks distinct path-outcome labels"
                          if ranking_pass else "Fixed local motif ranking failed its necessary top-5 bar under the registered tie rule"),
        missing_proof_obligation="Distinct realized-outcome labels for the remaining candidate paths; exact feasibility labels are the baseline rule itself",
        decision_scope="Batch execution status is separate from the seed-confirmed scientific decision",
        note="No training or label-based scorer selection. Exact-guard feasibility AUC=1 leaves no improvement headroom. Unselected paths are unlabeled, not negative examples; the M4 held-out check remains outstanding.")
