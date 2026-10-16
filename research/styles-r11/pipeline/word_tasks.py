"""Pool-callable P1/P2/L2 entrypoints; orchestration and RESULT writes belong to runner.

prepare(paths, controls=True) loads words/samplers once in the parent before fork.
task accepts experiment/path/seed; P2 also null/n/start (global sample offset).
Every sample seed derives from those fixed identifiers, independent of batching.
No experiments launch on import.
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measures
import nulls
import wordio

_CACHE = {}


def prepare(paths, controls=True):
    for path in paths:
        key = str(Path(path).resolve())
        if key not in _CACHE:
            word = wordio.load(path)
            _CACHE[key] = dict(word=word)
        state = _CACHE[key]
        if controls:
            if "commuting" not in state:
                state["commuting"] = nulls.CommutingSampler(state["word"])
            if "frames" not in state:
                state["frames"] = nulls.FrameSampler(state["word"])
    return {key: value["word"].summary() for key, value in _CACHE.items()}


def _state(path, controls=False):
    path = Path(path)
    if not path.exists(): path = wordio.PINS_PATH.parent / path
    key = str(path.resolve())
    if key not in _CACHE: prepare([path], controls=controls)
    state = _CACHE[key]
    if controls:
        if "commuting" not in state: state["commuting"] = nulls.CommutingSampler(state["word"])
        if "frames" not in state: state["frames"] = nulls.FrameSampler(state["word"])
    return state


def sample_seed(seed, path, control, index):
    text = json.dumps([int(seed), str(path), control, int(index)], separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big")


def _formal_map(events, n):
    rows = [{(r, ()): Fraction(1)} for r in range(n)]
    for event in events:
        e = event.gate
        if e[0] == "warp":
            op = e[2]
            rows[e[1]] = {(r, word[1:] if word and word[0] == -op else (op,) + word): value
                           for (r, word), value in rows[e[1]].items()}
        else:
            wordio._apply_scalar(e, rows)
    return rows


def p1(path, seed, controls=True):
    state = _state(path, controls=controls)
    word = state["word"]
    summary = word.summary()
    if word.family == "BORROW-WORD":
        W, _, _ = wordio.borrow_modules()
        independent = W.Word(str(Path(word.path).resolve()))
        prof = dict(independent.paid)
        source = "pinned wordmodel.Word.paid (asserted by Word)"
    else:
        F, W = wordio.toolkit()
        graph = F.Graph(W.inline(word.raw, True), check_literal=True, cut_equality=True)
        prof = Counter(graph.profile(graph.literal()))
        prof.update(word.centre_paid)
        prof = dict(prof)
        source = "toolkit Graph.profile(literal) + independent recount centre children"
        rec, centre, *_ = W.recount(word.raw)
        assert dict(rec) == word.paid
        assert dict(centre) == word.centre_paid
    assert prof == word.paid
    summary["independent_loader"] = dict(source=source, profile=prof, match=True)
    expected_warps = len(word.raw.get("warps", []))
    actual_warps = sum(e.origin == "Bwarp" for e in word.forward)
    assert expected_warps == actual_warps
    without_bwarps = [e.project("mid") for e in word.forward if e.origin != "Bwarp"]
    summary["word_count_conventions"] = dict(
        forward_including_Bwarps=len(word.forward), Bwarps=actual_warps,
        A_prelude_warps=sum(e.section == "A" and e.gate[0] == "warp" for e in word.forward),
        D_planning_forward_excluding_Bwarps=len(without_bwarps),
        D_planning_lz76_excluding_Bwarps=measures.lz76(without_bwarps),
        canonical_lz76_including_Bwarps=measures.lz76(word.section_tokens("mid")))
    if controls:
        rng = random.Random(seed)
        tokens = word.section_tokens("mid")
        iid = nulls.N0(tokens, rng)
        assert len(iid) == len(tokens) and set(iid) <= set(tokens)
        relabelled, relabel_info = nulls.N1c(word, rng, "mid")
        assert relabelled == tokens
        original_registers = word.section_tokens("registers")
        relabelled_registers, _ = nulls.N1c(word, rng, "registers")
        # Equality-partition canonicalization is the exact metamorphic property;
        # every equality-only statistic is invariant under a token bijection.
        encode = lambda ts: measures._to_str(ts)[0]
        assert encode(original_registers) == encode(relabelled_registers)
        mutated, frame_info = state["frames"].walk(rng)
        assert mutated.paid == word.paid
        reordered, commuting_info = state["commuting"].sample_events(rng)
        section_checks = {}
        for section in wordio.FORWARD_SECTIONS:
            old = [e for e in word.forward if e.section == section]
            new = [e for e in reordered if e.section == section]
            assert Counter(e.token for e in old) == Counter(e.token for e in new)
            eq = _formal_map(old, word.n) == _formal_map(new, word.n)
            assert eq, ("N1b exact linear map", section)
            section_checks[section] = eq
        summary["controls"] = dict(N0=dict(length_preserved=True, support_preserved=True),
                                   N1c=dict(**relabel_info, mid_invariant=True, equality_partition_invariant=True),
                                   N2=frame_info, N1b=dict(**commuting_info, exact_section_map=section_checks))
    summary.update(experiment="P-1", seed=seed, status="PASS")
    return summary


def output_language(path):
    word = _state(path)["word"]
    sections = sorted({e.section for e in word.events})
    return dict(attribution=word.attribution, family=word.family, paid=word.paid,
                profile_match=word.profile_match,
                section_strings={sec: {a: word.section_tokens(a, (sec,)) for a in wordio.ALPHABETS}
                                 for sec in sections}, climb_strings=word.climbs,
                derived_sections=["cleanup", "compensation", "early_cleanup"],
                note="Centre-descents are paid branch children, not monotone register continuation; their kind is explicit.")


def p2(path, seed, control, n=10, start=0, alphabet="mid"):
    state = _state(path, controls=control in ("N1b", "N2"))
    word = state["word"]
    tokens = word.section_tokens(alphabet)
    real = measures.measure(tokens)
    statistics = ("lz76", "repair", "H1", "H2", "H3", "H4", "H5", "H6")
    values = {key: [] for key in statistics}
    diagnostics = Counter()
    for index in range(start, start + n):
        rng = random.Random(sample_seed(seed, word.attribution.get("pin_key", word.attribution["path"]), control, index))
        if control == "N1":
            generated, info = nulls.N1(word.forward, rng, alphabet), {}
        elif control == "N1b":
            generated, info = state["commuting"].sample(rng, alphabet)
        elif control == "N1c":
            generated, info = nulls.N1c(word, rng, alphabet)
        elif control == "N2":
            changed, info = state["frames"].walk(rng)
            assert changed.paid == word.paid
            generated = changed.section_tokens(alphabet)
        else:
            raise ValueError(control)
        identical = generated == tokens
        diagnostics["identical_token_samples"] += identical
        measured = real if identical else measures.measure(generated)
        for key in statistics:
            values[key].append(measured[key])
        for key, value in info.items():
            if isinstance(value, (int, float)) and key != "acceptance_rate":
                diagnostics[key] += value
    summaries = {}
    for key, xs in values.items():
        mean = sum(xs) / len(xs)
        summaries[key] = dict(mean=mean, population_sd=(sum((x - mean) ** 2 for x in xs) / len(xs)) ** .5)
    return dict(experiment="P-2", attribution=word.attribution, family=word.family,
                seed=seed, null=control, alphabet=alphabet, start=start, n=n, real=real,
                values=values, batch_summary=summaries, diagnostics=dict(diagnostics),
                status="PASS", inferential=False, q_values=None)


def task(args):
    experiment = args["experiment"]
    path = args.get("path", args.get("name"))
    if experiment == "P-1":
        return p1(path, args["seed"], controls=args.get("controls", True))
    if experiment == "P-2":
        return p2(path, args["seed"], args.get("null", args.get("control")),
                  n=args.get("n", 10), start=args.get("start", 0), alphabet=args.get("alphabet", "mid"))
    if experiment == "L-2":
        word = _state(path)["word"]
        result = word.cleanup_check(scalar_replay=args.get("scalar_replay", True))
        result.update(experiment="L-2", seed=args["seed"],
                      status="PASS" if result["literal_equality"] else "NULL")
        return result
    if experiment == "P-1-language":
        return output_language(path)
    raise ValueError(experiment)
