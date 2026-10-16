"""Pre-registered L-3 workers; this module does not launch experiments.

The A/B lag census extends planning/A-lsys-word/lineage_checks.py.  Primary
statistics pool counts of equal-token pairs within A and B separately, never
across the boundary.  The 864-cell lag family is distinct from the 540-cell
compression screen.  Template instructions are inert JSON data and receive a
descriptive census, not independent inferential status for their derived text.
"""
from __future__ import annotations

from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measures
import wordio
import word_tasks

PERIODS = (9, 8, 22, 112, 73, 480, 666, 1332)
SECTIONS = ("A", "B")
_TEMPLATE = None


def _labels(tokens):
    ids = {}
    return np.fromiter((ids.setdefault(token, len(ids)) for token in tokens),
                       dtype=np.int32, count=len(tokens))


def lag_census(tokens, periods=PERIODS, autocorrelation=True):
    """Equality counts and centered one-hot autocorrelation at fixed lags.

    Center each categorical indicator using the entire section's frequencies.
    Divide its summed lag covariance by (n-lag)*sum_a p_a(1-p_a).  Finite
    endpoint composition can affect this descriptive autocorrelation; the raw
    equality count is the registered permutation statistic.
    """
    labels = _labels(tokens)
    n = len(labels)
    if n:
        frequencies = np.bincount(labels) / n
        probabilities = frequencies[labels]
        baseline = float(np.dot(frequencies, frequencies))
    else:
        probabilities, baseline = np.array([], dtype=float), None
    rows = {}
    for lag in periods:
        pairs = max(0, n - lag)
        if not pairs:
            rows[str(lag)] = dict(pairs=0, matches=0, lag_match=None,
                                  centered_sum=None, covariance_normalizer=None,
                                  autocorrelation=None)
            continue
        matches = int(np.count_nonzero(labels[:-lag] == labels[lag:]))
        centered = (matches - float(probabilities[:-lag].sum())
                    - float(probabilities[lag:].sum()) + pairs * baseline)
        normalizer = pairs * (1.0 - baseline)
        rows[str(lag)] = dict(pairs=pairs, matches=matches,
                              lag_match=matches / pairs,
                              centered_sum=centered if autocorrelation else None,
                              covariance_normalizer=normalizer if autocorrelation else None,
                              autocorrelation=(centered / normalizer
                                               if autocorrelation and normalizer > 0 else None))
    return dict(length=n, alphabet=int(labels.max()) + 1 if n else 0,
                independent_unigram_match=baseline, lags=rows)


def ab_census(events, alphabet, periods=PERIODS, autocorrelation=True):
    sections = {section: [] for section in SECTIONS}
    for event in events:
        if event.section in sections:
            sections[event.section].append(event.project(alphabet))
    per_section = {section: lag_census(tokens, periods, autocorrelation)
                   for section, tokens in sections.items()}
    pooled = {}
    for lag in periods:
        rows = [per_section[section]["lags"][str(lag)] for section in SECTIONS]
        pairs, matches = sum(r["pairs"] for r in rows), sum(r["matches"] for r in rows)
        centered = sum(r["centered_sum"] or 0.0 for r in rows)
        normalizer = sum(r["covariance_normalizer"] or 0.0 for r in rows)
        pooled[str(lag)] = dict(pairs=pairs, matches=matches,
                                lag_match=matches / pairs if pairs else None,
                                autocorrelation=(centered / normalizer
                                                 if autocorrelation and normalizer > 0 else None))
    return dict(sections=per_section, pooled=pooled)


def _shuffled_events(events, rng):
    blocks = []
    for event in events:
        if not blocks or blocks[-1][0].section != event.section:
            blocks.append([])
        blocks[-1].append(event)
    out = []
    for block in blocks:
        shuffled = block[:]
        rng.shuffle(shuffled)
        out.extend(shuffled)
    return out


def lag_batch(args):
    """Pool task: one word/null batch, six alphabets and eight fixed lags."""
    path, seed, control = args["path"], args["seed"], args["null"]
    if control not in ("N1", "N1b"):
        raise ValueError("L3 lag family admits only N1 and N1b")
    state = word_tasks._state(path, controls=control == "N1b")
    word = state["word"]
    alphabets = tuple(args.get("alphabets", wordio.ALPHABETS))
    if alphabets != wordio.ALPHABETS:
        raise ValueError("The registered L3 family uses all six fixed alphabets")
    real = {a: ab_census(word.forward, a) for a in alphabets}
    if any(real[a]["pooled"][str(lag)]["pairs"] == 0 for a in alphabets for lag in PERIODS):
        raise ValueError("Registered lag has no within-section pairs")
    values = {a: {str(lag): [] for lag in PERIODS} for a in alphabets}
    diagnostics = Counter()
    key = word.attribution.get("pin_key", word.attribution["path"])
    start, n = args.get("start", 0), args.get("n", 10)
    for index in range(start, start + n):
        rng = random.Random(word_tasks.sample_seed(seed, key, "L3:" + control, index))
        if control == "N1":
            events, info = _shuffled_events(word.forward, rng), {}
        else:
            events, info = state["commuting"].sample_events(rng)
        for alphabet in alphabets:
            result = ab_census(events, alphabet, autocorrelation=False)
            for lag in PERIODS:
                row = result["pooled"][str(lag)]
                assert row["pairs"] == real[alphabet]["pooled"][str(lag)]["pairs"]
                values[alphabet][str(lag)].append(row["lag_match"])
        for name, value in info.items():
            if isinstance(value, (int, float)) and name != "acceptance_rate":
                diagnostics[name] += value
    return dict(experiment="L-3", family="L3-864-LAG", status="PASS",
                attribution=word.attribution, word_family=word.family, seed=seed,
                null=control, start=start, n=n, alphabets=list(alphabets),
                periods=list(PERIODS), real=real, values=values,
                diagnostics=dict(diagnostics),
                statistic="sum of within-A/B equal-token pairs divided by sum of valid within-section pairs",
                scope="A/B only; no cut, cleanup, compensation or cross-section pairs",
                decision_scope="Successful batch execution; scientific decision requires complete family aggregation and second seed.")


def _freeze(value):
    """Injective typed JSON serialization as a hashable instruction token."""
    if isinstance(value, list):
        return "list", tuple(_freeze(x) for x in value)
    if isinstance(value, dict):
        return "dict", tuple((k, _freeze(v)) for k, v in sorted(value.items()))
    return type(value).__name__, value


def _opcode(record):
    if not isinstance(record, list) or not record or not isinstance(record[0], str):
        raise ValueError("Malformed GLOBAL-TEMPLATE local instruction")
    kind = record[0]
    if kind == "scalar":
        if len(record) < 2 or not isinstance(record[1], list) or not record[1]:
            raise ValueError("Malformed scalar template instruction")
        return kind, record[1][0]
    return kind,


def prepare_template(path=None, raw=None):
    """Parent-only cache preparation; performs no period measurements."""
    global _TEMPLATE
    path = Path(path or wordio.ROOT / "research/t74-joint-twelve-retired7/inputs/GLOBAL-TEMPLATE.json.gz").resolve()
    if _TEMPLATE is not None:
        if _TEMPLATE["path"] != str(path):
            raise ValueError("A different template is already prepared")
        return _TEMPLATE["source"]
    data = path.read_bytes()
    template = raw if raw is not None else json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)
    programs = template.get("local_programs")
    if not isinstance(programs, dict) or set(programs) != {"forward", "backward"}:
        raise ValueError("Unexpected template local_programs schema")
    with wordio.PINS_PATH.open() as stream:
        pins = json.load(stream)["files"]
    pin_key = "research/t74-joint-twelve-retired7/inputs/WORD-base.json.gz"
    lineage = dict(pins[pin_key], pin_key=pin_key)
    source = dict(path=str(path.relative_to(wordio.ROOT)), sha256=hashlib.sha256(data).hexdigest(),
                  git_blob=hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                  source_attribution=[lineage],
                  program_schema="local_programs.{forward,backward}: ordered tagged JSON instruction lists")
    _TEMPLATE = dict(path=str(path), raw=template, programs=programs, source=source)
    return source


def template_census(args):
    """Descriptive program census; fetched data are never imported or executed."""
    if _TEMPLATE is None:
        raise RuntimeError("Call prepare_template once in the parent before launching workers")
    result = {}
    for orientation, program in _TEMPLATE["programs"].items():
        literal = [_freeze(record) for record in program]
        opcode = [_opcode(record) for record in program]
        result[orientation] = dict(
            instructions=len(program),
            instruction_kind_counts=dict(Counter(record[0] for record in program)),
            literal=lag_census(literal), opcode=lag_census(opcode),
            literal_periodogram=measures.categorical_periodogram(literal, PERIODS),
            opcode_periodogram=measures.categorical_periodogram(opcode, PERIODS))
    return dict(experiment="L-3", family="L3-TEMPLATE-DESCRIPTIVE", seed=args["seed"],
                status="EXPLORATORY", n_permutations=0, source=_TEMPLATE["source"],
                programs=result, periods=list(PERIODS),
                note="Literal includes all tagged instructions, including derived phases; opcode retains only tag and scalar operation. Both are descriptive. Backward is not an independent construction replicate; no p or q is assigned.")


def task(args):
    if args.get("experiment") in ("L3-TEMPLATE", "L-3-TEMPLATE"):
        return template_census(args)
    return lag_batch(args)
