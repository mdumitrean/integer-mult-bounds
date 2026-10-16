"""M1 string screen, exact shared grammar, and leakage-free climb prediction.

This module provides workers only: callers must preregister and use pool.py.
The shared RePair grammar is a finite straight-line grammar. An exact expansion
of the observed words does not establish a parametric D0L construction family.
L4 features omit paid-climb fields from first/last motifs to prevent label leakage.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import json
import random
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import measures
import nulls
import wordio
import word_tasks

DEFAULT_STATISTICS = ("lz76", "repair", "H6", "maximal_repeat_mass", "period_peak")
_WORDS = {}
_CLIMB_ROWS = {}


def prepare(paths, controls=True):
    word_tasks.prepare(paths, controls=controls)
    for path in paths:
        word = word_tasks._state(path, controls=controls)["word"]
        key = word.attribution.get("pin_key", word.attribution["path"])
        _WORDS[key] = word
        _CLIMB_ROWS[key] = climb_rows(word)
    return {key: dict(path=word.path, family=word.family, attribution=word.attribution)
            for key, word in _WORDS.items()}


def _words(paths=None):
    if paths is None:
        return list(_WORDS.values())
    result = []
    for path in paths:
        if path in _WORDS:
            result.append(_WORDS[path])
        else:
            result.append(word_tasks._state(path)["word"])
    return result


def _shuffle_events(events, rng):
    blocks = []
    for event in events:
        if not blocks or blocks[-1][0].section != event.section:
            blocks.append([])
        blocks[-1].append(event)
    output = []
    for block in blocks:
        shuffled = block[:]
        rng.shuffle(shuffled)
        output.extend(shuffled)
    return output


def screen_batch(args):
    """One shared permutation yields all alphabet/statistic cells without reruns."""
    path, seed, control = args["path"], args["seed"], args["null"]
    state = word_tasks._state(path, controls=control in ("N1b", "N2"))
    word = state["word"]
    alphabets = tuple(args.get("alphabets", wordio.ALPHABETS))
    statistics = tuple(args.get("statistics", DEFAULT_STATISTICS))
    real = {alphabet: measures.measure(word.section_tokens(alphabet), statistics)
            for alphabet in alphabets}
    values = {a: {s: [] for s in statistics} for a in alphabets}
    diagnostics = Counter()
    start, n = args.get("start", 0), args.get("n", 10)
    key = word.attribution.get("pin_key", word.attribution["path"])
    for index in range(start, start + n):
        rng = random.Random(word_tasks.sample_seed(seed, key, "M1:" + control, index))
        changed = None
        info = {}
        if control == "N1":
            events = _shuffle_events(word.forward, rng)
        elif control == "N1b":
            events, info = state["commuting"].sample_events(rng)
        elif control == "N2":
            changed, info = state["frames"].walk(rng)
            events = changed.forward
            assert changed.paid == word.paid
        else:
            raise ValueError(control)
        for alphabet in alphabets:
            tokens = [e.project(alphabet) for e in events]
            result = measures.measure(tokens, statistics)
            for statistic in statistics:
                values[alphabet][statistic].append(result[statistic])
        for k, value in info.items():
            if isinstance(value, (int, float)) and k != "acceptance_rate": diagnostics[k] += value
    result = dict(experiment="M1-SCREEN", attribution=word.attribution, family=word.family,
                  seed=seed, null=control, start=start, n=n, statistics=list(statistics),
                  alphabets=list(alphabets), real=real, values=values,
                  diagnostics=dict(diagnostics), status="PASS")
    if args.get("observed_census", False):
        result["observed_census"] = {a: measures.measure(word.section_tokens(a), statistics,
                                                        include_census=True) for a in alphabets}
    return result


def renamed_skeleton(word):
    """A/B gates: first-occurrence register and warp renaming, exact coefficient.

    Frames contribute their ranks. The projection retains complete register
    equality relationships across the whole A+B word, not independent per-block
    resets. Replaying it is exact in this declared skeleton alphabet only.
    """
    renamed, operators, tokens = {}, {}, []
    for event in word.forward:
        if event.section not in ("A", "B"):
            continue
        rr = []
        for register in event.registers:
            if register not in renamed: renamed[register] = len(renamed)
            rr.append(renamed[register])
        operator = None
        if event.gate[0] == "warp":
            op = event.gate[2]
            if abs(op) not in operators: operators[abs(op)] = len(operators) + 1
            operator = operators[abs(op)] * (1 if op > 0 else -1)
        t = event.token
        tokens.append((event.section, t[1], t[2], t[3], t[4], t[5], tuple(rr), operator))
    return tokens


def shared_grammar(words, max_rules=201):
    """Joint deterministic RePair; stop at 201 suffices to falsify <=200 rules.

    Terminals are nonnegative integer IDs, binary nonterminals negative IDs.
    The same pair has the same rule in every word. Exact expansion is checked
    independently of compression and residual-literal/axiom diagnostics.
    """
    names = [w.attribution.get("pin_key", w.attribution["path"]) for w in words]
    token_streams = [renamed_skeleton(w) for w in words]
    terminal_ids, terminals = {}, []
    originals = []
    for tokens in token_streams:
        seq = []
        for token in tokens:
            if token not in terminal_ids:
                terminal_ids[token] = len(terminals)
                terminals.append(token)
            seq.append(terminal_ids[token])
        originals.append(seq)
    sequences = [seq[:] for seq in originals]
    rules = {}
    stopped_at_cap = False
    while True:
        counts = Counter()
        for sequence in sequences:
            counts.update(zip(sequence, sequence[1:]))
        if not counts or max(counts.values()) < 2:
            break
        if len(rules) >= max_rules:
            stopped_at_cap = True
            break
        pair, count = min(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        symbol = -(len(rules) + 1)
        replacements, next_sequences = 0, []
        for sequence in sequences:
            out, i = [], 0
            while i < len(sequence):
                if i + 1 < len(sequence) and (sequence[i], sequence[i + 1]) == pair:
                    out.append(symbol)
                    replacements += 1
                    i += 2
                else:
                    out.append(sequence[i])
                    i += 1
            next_sequences.append(out)
        if replacements < 2:
            # The pair counter permits overlapping occurrences; if its only
            # replacements collapse to one, it does not define a compression rule.
            break
        rules[symbol] = pair
        sequences = next_sequences
    def expand(seq):
        out, stack = [], list(reversed(seq))
        while stack:
            symbol = stack.pop()
            if symbol >= 0:
                out.append(symbol)
            else:
                left, right = rules[symbol]
                stack.extend((right, left))
        return out
    def used_rules(seq):
        result, stack = set(), list(seq)
        while stack:
            symbol = stack.pop()
            if symbol < 0 and symbol not in result:
                result.add(symbol)
                stack.extend(rules[symbol])
        return result
    per_word, usage = {}, []
    for name, original, axiom in zip(names, originals, sequences):
        used = used_rules(axiom)
        usage.append(used)
        exact = expand(axiom) == original
        assert exact
        per_word[name] = dict(exact_replay=exact, skeleton_gates=len(original), axiom_length=len(axiom),
                             residual_literal_count=sum(x >= 0 for x in axiom), used_rule_count=len(used),
                             axiom=axiom)
    overlaps = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            union = usage[i] | usage[j]
            overlaps.append(dict(words=[names[i], names[j]],
                                 jaccard=len(usage[i] & usage[j]) / len(union) if union else 1.0))
    primary = (len(words) >= 3 and len(rules) <= 200 and
               all(row["jaccard"] >= .9 for row in overlaps))
    # Diagnostics impose no additional pass threshold. A finite straight-line
    # grammar can store its outputs in the axioms; exact expansion alone does not
    # establish a position-independent parametric construction.
    anti_memorization = dict(
        axiom_lengths={name: row["axiom_length"] for name, row in per_word.items()},
        residual_literal_counts={name: row["residual_literal_count"] for name, row in per_word.items()},
        decision_threshold=None,
        proof_obligation="Give parameterized axioms and productions independent of the stored output words.")
    return dict(experiment="L-1", primary_numeric_bar=primary,
                anti_memorization_check=anti_memorization,
                status="PASS" if primary else "NULL",
                shared_rule_count=len(rules), stopped_at_rule_cap=stopped_at_cap,
                max_rules_evaluated=max_rules, per_word=per_word,
                cross_word_rule_overlap=overlaps,
                rules={str(k): list(v) for k, v in rules.items()}, terminals=terminals,
                source_attribution=[w.attribution for w in words],
                scope="finite straight-line grammar of rank-annotated globally register-renamed skeletons",
                missing_pattern_obligations=["parameterized construction independent of stored outputs",
                                             "matched-null margins", "N4 constructor control", "held-out test",
                                             "profile non-circularity"],
                note="Exact expansion of a stored axiom is bookkeeping; it is not a parametric D0L proof.")


def climb_rows(word):
    key = word.attribution.get("pin_key", word.attribution["path"])
    pr = word.attribution.get("pr")
    group = str(pr) if pr is not None else ("retired5" if "retired5" in key else key)
    result = []
    for register, row in word.climbs.items():
        # first/last motifs are (op,coef,roles,frame_rank,dt,ds). Drop dt/ds.
        first = tuple(row["first_motif"][:5]) if row["first_motif"] is not None else ()
        last = tuple(row["last_motif"][:5]) if row["last_motif"] is not None else ()
        features = row["role"], row["entrance_dim"], row["width"], first, last
        label = tuple(jump["rank"] for jump in row["jumps"])
        result.append(dict(word=key, group=group, family=word.family, register=register,
                           role=row["role"], features=features, label=label))
    return result


def _choose(counter):
    candidates = [(count, label) for label, count in counter.items() if count > 0]
    return min(candidates, key=lambda x: (-x[0], x[1]))[1] if candidates else ()


def lookup_accuracy(rows_by_word, grouped=False, override=None):
    """Train only on other word files (or other PR groups), deterministic ties."""
    total_feature, total_role = defaultdict(Counter), defaultdict(Counter)
    held_feature, held_role = defaultdict(lambda: defaultdict(Counter)), defaultdict(lambda: defaultdict(Counter))
    labelled = {}
    for name, rows in rows_by_word.items():
        labels = override[name] if override is not None else [row["label"] for row in rows]
        labelled[name] = labels
        for row, label in zip(rows, labels):
            fold = row["group"] if grouped else name
            total_feature[row["features"]][label] += 1
            total_role[row["role"]][label] += 1
            held_feature[fold][row["features"]][label] += 1
            held_role[fold][row["role"]][label] += 1
    per_word = {}
    predicted = {}
    for name, rows in rows_by_word.items():
        fold = rows[0]["group"] if grouped else name
        feature_models, role_models = {}, {}
        correct, unknown = 0, 0
        for row, true in zip(rows, labelled[name]):
            feature, role = row["features"], row["role"]
            if feature not in feature_models:
                trained = total_feature[feature] - held_feature[fold][feature]
                feature_models[feature] = _choose(trained) if trained else None
            prediction = feature_models[feature]
            if prediction is None:
                unknown += 1
                if role not in role_models:
                    role_models[role] = _choose(total_role[role] - held_role[fold][role])
                prediction = role_models[role]
            correct += prediction == true
            predicted[name, row["register"]] = prediction
        per_word[name] = dict(correct=correct, total=len(rows), accuracy=correct / len(rows),
                              unseen_feature_rows=unknown, fold=fold)
    return dict(per_word=per_word,
                accuracy=sum(row["correct"] for row in per_word.values()) / sum(row["total"] for row in per_word.values()),
                minimum_word_accuracy=min(row["accuracy"] for row in per_word.values()),
                fold_unit="PR_group" if grouped else "word_file")


def climb_prediction_batch(args):
    words = _words(args.get("paths"))
    rows = {w.attribution.get("pin_key", w.attribution["path"]): climb_rows(w) for w in words}
    if len(rows) < 5:
        raise ValueError("L4 requires at least five words")
    real = lookup_accuracy(rows, grouped=False)
    grouped_real = lookup_accuracy(rows, grouped=True)
    values = {name: [] for name in rows}
    grouped_values = {name: [] for name in rows}
    seed, start, n = args["seed"], args.get("start", 0), args.get("n", 10)
    for index in range(start, start + n):
        rng = random.Random(word_tasks.sample_seed(seed, "L4", "role_permutation", index))
        labels = {}
        for name, word_rows in rows.items():
            by_role = defaultdict(list)
            for i, row in enumerate(word_rows): by_role[row["role"]].append(i)
            permutation = [row["label"] for row in word_rows]
            for positions in by_role.values():
                source = [permutation[i] for i in positions]
                rng.shuffle(source)
                for i, label in zip(positions, source): permutation[i] = label
            labels[name] = permutation
        normal = lookup_accuracy(rows, override=labels)
        grouped = lookup_accuracy(rows, grouped=True, override=labels)
        for name in rows:
            values[name].append(normal["per_word"][name]["accuracy"])
            grouped_values[name].append(grouped["per_word"][name]["accuracy"])
    return dict(experiment="L-4", seed=seed, start=start, n=n, real=real,
                leave_one_PR_out=grouped_real, null_values=values, grouped_null_values=grouped_values,
                source_attribution=[w.attribution for w in words], status="PASS",
                features="role,entrance_dim,width,first/last(op,coef,roles,frame_rank); paid dt/ds excluded",
                null="independent per-word label permutation among registers with the same role; refit all folds",
                note="No held-out PR is read here. M4 is required before a pattern designation.")


def auc(labels, scores):
    """Mann-Whitney AUC with half credit for score ties."""
    positives = sum(labels)
    negatives = len(labels) - positives
    if not positives or not negatives:
        return None
    ordered = sorted(zip(scores, labels))
    rank_sum, index = 0.0, 0
    while index < len(ordered):
        end = index + 1
        while end < len(ordered) and ordered[end][0] == ordered[index][0]: end += 1
        rank_sum += ((index + 1 + end) / 2) * sum(label for _, label in ordered[index:end])
        index = end
    return (rank_sum - positives * (positives + 1) / 2) / (positives * negatives)


def exact_guard_baseline(atlases, source_attribution):
    """L5 baseline on exact atlas labels; deterministic labels leave zero headroom.

    This does not assign FAIL labels to the other 190 of 192 candidate paths.
    A ranking claim needs real path outcomes or a separately specified rule.
    """
    import matching
    evidence = []
    for atlas in atlases:
        lives, slots = atlas["lives"], atlas["slots"]
        adj = matching.adjacency(lives, slots)
        labels, scores = [], []
        for life, ld in lives.items():
            for slot, sd in slots.items():
                if sd["register"] == ld.get("register"):
                    continue
                guard = sd["last"] < ld["first"] and sd["lo"] <= ld["hi"]
                labels.append(slot in adj[life])
                scores.append(int(guard))
        value = auc(labels, scores)
        assert value in (None, 1.0)
        evidence.append(dict(word=atlas["word"], pairs=len(labels), positives=sum(labels),
                             exact_guard_auc=value, maximum_possible_auc_increment=0.0,
                             note="Atlas label is the exact guard by construction; this is a circularity audit."))
    return dict(experiment="L-5", status="EXPLORATORY", source_attribution=source_attribution,
                baseline=evidence, realised_move_ranking=None,
                missing_proof_obligation="Distinct outcomes and a registered motif scorer for the 192-path ranking",
                note="Unselected paths are not negative labels. No motif can improve AUC beyond a deterministic exact label rule.")


def task(args):
    kind = args["experiment"]
    if kind in ("M1-SCREEN", "screen"):
        return screen_batch(args)
    if kind == "L-1":
        result = shared_grammar(_words(args.get("paths")), args.get("max_rules", 201))
        result["seed"] = args["seed"]
        return result
    if kind == "L-4":
        return climb_prediction_batch(args)
    if kind == "L-5":
        return exact_guard_baseline(args["atlases"], args["source_attribution"])
    raise ValueError(kind)
