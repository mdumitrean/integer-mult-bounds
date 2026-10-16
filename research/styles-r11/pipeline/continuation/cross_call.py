"""Exact, sharded C3 cross-call two-role exchange census.

Canonical index = 408*call+helper. Unequal pairs are owned by their higher-width
role; equal-width pairs are counted analytically at their earlier call. Exact
bit masks apply capacity/spread, two windows and simultaneous family guards.
Popcounts partition every conceptual pair without sampling. Same physical
bins are excluded; same-family/different-bin pairs are retained explicitly.

The source parent loads all indexes once. Workers only run through pool.py.
No fetched code, solver, automatic experiment, or sandpile structure is used.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import gzip
import hashlib
import json
import random
import sys
import time

HERE = Path(__file__).resolve().parent
RR = HERE.parent.parent
LATEST_SHA = "16ae9a6e4d451525bb6b2e5ad19c62adce2d93c620d5beaa332fd2512a199461"
CALLS, HELPERS, BLOCK_SIZE = 666, 408, 8
DOMAIN = 36862620480
_INDEX = None


def need(ok, message):
    if not ok:
        raise ValueError(message)


def _modules():
    need(hashlib.sha256((HERE / "latest_fill.py").read_bytes()).hexdigest() == LATEST_SHA,
         "frozen C2 adapter changed")
    if str(HERE) not in sys.path:
        sys.path.insert(0, str(HERE))
    import latest_fill
    fill, _ = latest_fill._modules()
    return fill, latest_fill


def _mask(indices):
    result = 0
    for index in indices:
        result |= 1 << index
    return result


def _set(storage, index):
    storage[index >> 3] |= 1 << (index & 7)


def block_specs():
    return [dict(block=b, calls=list(range(start, min(start + BLOCK_SIZE, CALLS))))
            for b, start in enumerate(range(0, CALLS, BLOCK_SIZE))]


def prepare(pr=2917):
    """Build immutable bit indexes once in the parent, after source freeze."""
    global _INDEX
    fill, latest = _modules()
    prepared = latest.prepare(pr=pr)
    if _INDEX is not None:
        return dict(prepared=prepared, index=_INDEX["summary"])
    record = latest.get_record()
    model = record["model"]
    need(model.calls == CALLS and set(map(len, model.widths)) == {HELPERS}, "fixed registered role geometry")
    n = CALLS * HELPERS
    need(len(model.rows) == n, "complete role inventory")
    byindex, original_indices = [None] * n, [None] * n
    family_rows, bin_rows, family_calls = defaultdict(list), defaultdict(list), defaultdict(set)
    used_families = [set() for _ in range(CALLS)]
    used_cells, percall_widths, all_widths = Counter(), [Counter() for _ in range(CALLS)], Counter()
    widths, families, bins, windows = [None] * n, [None] * n, [None] * n, [None] * n
    for original, row in enumerate(model.rows):
        t, h, owner, child, port, offset = row
        i = HELPERS * t + h
        need(0 <= i < n and byindex[i] is None and 0 <= h < HELPERS, "unique canonical role index")
        byindex[i], original_indices[i] = row, original
        width, key = model.widths[t][h], (owner, child, port)
        family = owner * 896 + model.family[child] * 112 + port
        need(0 <= family < record["wires"] and family not in used_families[t], "baseline physical family injectivity")
        used_families[t].add(family)
        widths[i], families[i], bins[i], windows[i] = width, family, key, model.win[owner, child]
        family_rows[family].append(i)
        bin_rows[key].append(i)
        family_calls[family].add(t)
        used_cells[key] += width
        percall_widths[t][width] += 1
        all_widths[width] += 1
    need(all(x is not None for x in byindex), "all canonical roles present")
    residuals = tuple(windows[i][0] - used_cells[bins[i]] for i in range(n))
    need(all(0 <= residuals[i] <= windows[i][0] for i in range(n)), "baseline capacity for residual indexes")
    byte_count = (n + 7) // 8
    starts = [bytearray(byte_count) for _ in range(CALLS + 1)]
    stops = [bytearray(byte_count) for _ in range(CALLS + 1)]
    group_bytes = {}
    for i, (cap, start, stop) in enumerate(windows):
        need(-1 <= start < stop < CALLS, "nonempty bounded owner interval")
        _set(starts[start + 1], i)
        _set(stops[stop + 1], i)
        key = widths[i], residuals[i]
        if key not in group_bytes:
            group_bytes[key] = bytearray(byte_count)
        _set(group_bytes[key], i)
    window_masks = []
    active = 0
    for t in range(CALLS):
        active = (active & ~int.from_bytes(stops[t], "little")) | int.from_bytes(starts[t], "little")
        window_masks.append(active)
    del starts, stops
    groups = {key: int.from_bytes(value, "little") for key, value in group_bytes.items()}
    del group_bytes
    need(sum(value.bit_count() for value in groups.values()) == n, "width/residual group partition")
    call_masks = tuple(((1 << HELPERS) - 1) << (t * HELPERS) for t in range(CALLS))
    blocked_incoming = []
    for t in range(CALLS):
        bits = bytearray(byte_count)
        for family in used_families[t]:
            for i in family_rows[family]:
                _set(bits, i)
        blocked_incoming.append(int.from_bytes(bits, "little"))
    range_masks = {}
    for cap, start, stop in set(windows):
        range_masks[start, stop] = ((1 << ((stop - start) * HELPERS)) - 1) << ((start + 1) * HELPERS)
    geometry_masks, score_masks = {}, {}
    for a, ra, ca in {(widths[i], residuals[i], windows[i][0]) for i in range(n)}:
        byscore = defaultdict(int)
        geometry = 0
        for (b, rb), mask in groups.items():
            d = a - b
            if d > 0 and d <= rb < ra + d and ra + d <= ca:
                score = 2 * d * (ra - rb + d)
                byscore[score] |= mask
                geometry |= mask
        key = a, ra, ca
        geometry_masks[key] = geometry
        score_masks[key] = tuple(sorted(byscore.items(), reverse=True))
    suffix, later_equal, lower_cross = Counter(), [None] * CALLS, [None] * CALLS
    for t in reversed(range(CALLS)):
        later_equal[t] = dict(suffix)
        suffix.update(percall_widths[t])
        lower_cross[t] = {a: sum(count - percall_widths[t][b] for b, count in all_widths.items() if b < a)
                          for a in all_widths}
    equal_total = sum(count * later_equal[t].get(a, 0) for t, counts in enumerate(percall_widths) for a, count in counts.items())
    unequal_total = sum(count * lower_cross[t][a] for t, counts in enumerate(percall_widths) for a, count in counts.items())
    need(equal_total + unequal_total == DOMAIN == CALLS * (CALLS - 1) // 2 * HELPERS ** 2, "analytic complete cross-call pair count")
    index_bytes = sum(sys.getsizeof(x) for seq in (window_masks, blocked_incoming, call_masks) for x in seq)
    index_bytes += sum(sys.getsizeof(x) for mapping in (groups, range_masks, geometry_masks) for x in mapping.values())
    index_bytes += sum(sys.getsizeof(mask) for values in score_masks.values() for _, mask in values)
    summary = dict(roles=n, calls=CALLS, blocks=len(block_specs()), calls_per_block=BLOCK_SIZE,
                   conceptual_cross_call_pairs=DOMAIN, equal_width_pairs=equal_total, unequal_width_pairs=unequal_total,
                   excluded_same_call_pairs=CALLS * HELPERS * (HELPERS - 1) // 2,
                   canonical_index="408*call+helper", bitset_storage_bytes=index_bytes,
                   analytic_pair_ownership="Unequal widths owned by higher width; equal widths owned by earlier call.",
                   parent_load_once=True)
    _INDEX = dict(record=record, model=model, rows=tuple(byindex), original_indices=tuple(original_indices),
                  widths=tuple(widths), families=tuple(families), bins=tuple(bins), windows=tuple(windows),
                  residuals=residuals, family_rows=dict(family_rows), bin_rows=dict(bin_rows),
                  family_calls={f: tuple(sorted(ts)) for f, ts in family_calls.items()},
                  used_families=tuple(frozenset(fs) for fs in used_families), call_masks=call_masks,
                  window_masks=tuple(window_masks), blocked_incoming=tuple(blocked_incoming),
                  range_masks=range_masks, geometry_masks=geometry_masks, score_masks=score_masks,
                  later_equal=tuple(later_equal), lower_cross=tuple(lower_cross), summary=summary)
    return dict(prepared=prepared, index=summary)


def _index():
    need(_INDEX is not None, "prepare must run once in the parent before pool launch")
    return _INDEX


def provenance():
    return _modules()[1].provenance()


def _role_masks(i):
    """Disjoint pair categories plus the exact accepting target bit mask."""
    x = _index()
    t, a, ra, ca = i // HELPERS, x["widths"][i], x["residuals"][i], x["windows"][i][0]
    same_bin_lower = [j for j in x["bin_rows"][x["bins"][i]] if x["widths"][j] < a and j // HELPERS != t]
    counts = dict(equal_width=x["later_equal"][t].get(a, 0), same_bin_unequal=len(same_bin_lower),
                  capacity_or_nonpositive_spread=0, window_rejection=0, family_rejection=0, strict_improvement=0)
    unequal = x["lower_cross"][t][a]
    spread = x["geometry_masks"][a, ra, ca] & ~x["call_masks"][t] & ~_mask(same_bin_lower)
    nspread = spread.bit_count()
    counts["capacity_or_nonpositive_spread"] = unequal - len(same_bin_lower) - nspread
    if not spread:
        return counts, 0
    _, start, stop = x["windows"][i]
    both_windows = spread & x["window_masks"][t] & x["range_masks"][start, stop]
    nwindow = both_windows.bit_count()
    counts["window_rejection"] = nspread - nwindow
    if not both_windows:
        return counts, 0
    family = x["families"][i]
    blocked_calls = 0
    for call in x["family_calls"][family]:
        blocked_calls |= x["call_masks"][call]
    same_family = _mask(x["family_rows"][family])
    # Different families: each incoming family was absent from the destination
    # call. Same family: removing the old role frees exactly that family.
    allowed_families = (~x["blocked_incoming"][t] & ~blocked_calls) | same_family
    accepted = both_windows & allowed_families
    counts["strict_improvement"] = accepted.bit_count()
    counts["family_rejection"] = nwindow - counts["strict_improvement"]
    need(all(n >= 0 for n in counts.values()) and sum(counts.values()) == counts["equal_width"] + unequal,
         "per-source exact category partition")
    return counts, accepted


def _direct_pair(i, j):
    x = _index()
    ta, tb = i // HELPERS, j // HELPERS
    a, b = x["widths"][i], x["widths"][j]
    if ta == tb or a == b or x["bins"][i] == x["bins"][j]:
        return False, None
    if a < b:
        i, j, ta, tb, a, b = j, i, tb, ta, b, a
    ra, rb = x["residuals"][i], x["residuals"][j]
    ca, sa, ea = x["windows"][i]
    cb, sb, eb = x["windows"][j]
    d = a - b
    if not (0 <= ra + d <= ca and 0 <= rb - d <= cb and d * (ra - rb + d) > 0):
        return False, None
    if not (sa < tb <= ea and sb < ta <= eb):
        return False, None
    fa, fb = x["families"][i], x["families"][j]
    if fb in x["used_families"][ta] - {fa} or fa in x["used_families"][tb] - {fb}:
        return False, None
    return True, 2 * d * (ra - rb + d)


def _indexed_pair(i, j):
    x = _index()
    if x["widths"][i] == x["widths"][j]:
        return False
    if x["widths"][i] < x["widths"][j]:
        i, j = j, i
    return bool(_role_masks(i)[1] & (1 << j))


def controls_task(seed):
    started = time.process_time()
    fill, latest = _modules()
    x, model = _index(), _index()["model"]
    baseline = latest._controls(model)
    need(not _direct_pair(0, 0)[0] and not _indexed_pair(0, 0), "self exchange control")
    equal = next(j for j in range(HELPERS, CALLS * HELPERS) if x["widths"][j] == x["widths"][0])
    need(not _direct_pair(0, equal)[0] and not _indexed_pair(0, equal), "equal-width exchange control")
    bad = list(model.rows)
    t, h, owner, child, port, offset = bad[0]
    other = next((o, c) for (o, c), (cap, start, stop) in sorted(model.win.items()) if not start < t <= stop)
    bad[0] = (t, h, other[0], other[1], port, offset)
    error = None
    try:
        fill.audit(model, bad, require_profile=False)
    except ValueError as exc:
        error = str(exc)
    need(error == "literal call window", "invalid window mutant rejected for exact expected reason")
    rng, samples = random.Random(int(seed)), []
    for _ in range(128):
        ta, tb = rng.sample(range(CALLS), 2)
        i, j = ta * HELPERS + rng.randrange(HELPERS), tb * HELPERS + rng.randrange(HELPERS)
        direct, score = _direct_pair(i, j)
        indexed = _indexed_pair(i, j)
        need(direct == indexed, "indexed/direct guard parity")
        samples.append(dict(pair=[i, j], direct=direct, indexed=indexed, score=score))
    return dict(status="PASS", seed=int(seed), baseline=baseline, invalid_window_error=error,
                direct_pair_controls=samples, direct_pair_count=128, self_equal_controls=True,
                cpu_seconds=time.process_time() - started, **provenance())


def c3_block_task(seed, block, max_seconds=240):
    x = _index()
    need(type(block) is int and 0 <= block < len(block_specs()), "registered block id")
    need(0 < max_seconds <= 240, "registered internal CPU guard")
    started = time.process_time()
    calls = block_specs()[block]["calls"]
    indices = [i for t in calls for i in range(t * HELPERS, (t + 1) * HELPERS)]
    random.Random((int(seed) << 20) + block).shuffle(indices)
    counts, completed, best = Counter(), 0, None
    for i in indices:
        if completed % 32 == 0 and time.process_time() - started > max_seconds:
            break
        categories, accepted = _role_masks(i)
        counts.update(categories)
        completed += 1
        if not accepted:
            continue
        key = x["widths"][i], x["residuals"][i], x["windows"][i][0]
        for score, score_mask in x["score_masks"][key]:
            hits = accepted & score_mask
            if hits:
                j = (hits & -hits).bit_length() - 1
                pair = sorted((i, j))
                candidate = dict(pair=pair, square_gain=score,
                                 canonical_pair=[[p // HELPERS, p % HELPERS] for p in pair])
                if best is None or score > best["square_gain"] or (score == best["square_gain"] and pair < best["pair"]):
                    best = candidate
                break
    complete = completed == len(indices)
    return dict(status="COMPLETE" if complete else "EXPLORATORY", seed=int(seed), block=block,
                source_calls=calls, source_roles_expected=len(indices), source_roles_processed=completed,
                complete=complete, counts=dict(counts), best=best,
                cpu_seconds=time.process_time() - started, solver_calls=0,
                scientific_decision=None, scope="Disjoint exact C3 census shard; scientific verdict requires all shards and controls.")


def finish_task(seed, block_results, output_dir, controls_result):
    fill, latest = _modules()
    x, started = _index(), time.process_time()
    directory = Path(output_dir)
    if not directory.is_absolute():
        directory = RR / directory
    directory = directory.resolve()
    need(directory.is_relative_to(RR.resolve()), "output confinement")
    directory.mkdir(parents=True, exist_ok=True)
    need(controls_result["status"] == "PASS" and controls_result["seed"] == int(seed), "passed matching-seed controls")
    need(len(block_results) == len(block_specs()), "all registered shards collected")
    byblock = {r["block"]: r for r in block_results}
    need(len(byblock) == len(block_specs()) and set(byblock) == set(range(len(block_specs()))), "unique complete shard ids")
    counts, coverage, processed, best = Counter(), [], 0, None
    for spec in block_specs():
        row = byblock[spec["block"]]
        need(row["seed"] == int(seed) and row["complete"] and row["status"] == "COMPLETE", "complete matching-seed shard")
        need(row["source_calls"] == spec["calls"]
              and row["source_roles_processed"] == row["source_roles_expected"] == len(spec["calls"]) * HELPERS,
              "exact shard role/call coverage")
        coverage.extend(row["source_calls"])
        processed += row["source_roles_processed"]
        counts.update(row["counts"])
        candidate = row["best"]
        if candidate and (best is None or candidate["square_gain"] > best["square_gain"]
                          or (candidate["square_gain"] == best["square_gain"] and candidate["pair"] < best["pair"])):
            best = candidate
    need(coverage == list(range(CALLS)) and processed == CALLS * HELPERS, "whole source-role coverage")
    need(sum(counts.values()) == DOMAIN and counts["equal_width"] == x["summary"]["equal_width_pairs"], "whole conceptual-domain category partition")
    need((best is None) == (counts["strict_improvement"] == 0), "candidate/count agreement")
    out = dict(status="NULL" if best is None else "PASS", seed=int(seed), baseline_pr=2917,
               complete=True, source_roles=processed, source_calls=len(coverage), shards=len(byblock),
               conceptual_pairs=DOMAIN, excluded_same_call_pairs=x["summary"]["excluded_same_call_pairs"],
               counts=dict(counts), controls=controls_result, candidate=None, solver_calls=0,
               null_scope="Only exhaustive cross-call two-role bin exchanges on this pinned PR2917 fill.",
               selection="Maximum integer squared residual gain, then lexical sorted ((call,helper),(call,helper)); no root scoring.",
               scope="Constructive complete-profile fill gain only; complete changed-obligation admission remains mandatory.",
               **provenance())
    if best is not None:
        i, j = best["pair"]
        direct, score = _direct_pair(i, j)
        need(direct and _indexed_pair(i, j) and score == best["square_gain"], "selected witness direct/index parity")
        model = x["model"]
        oi, oj = x["original_indices"][i], x["original_indices"][j]
        old_i, old_j = model.rows[oi], model.rows[oj]
        bare = [list(row[:5]) for row in model.rows]
        bare[oi][2:5], bare[oj][2:5] = bare[oj][2:5], bare[oi][2:5]
        changed = fill.compact_rows(model, bare)
        audited = fill.audit(model, changed, require_profile=False)
        before = controls_result["baseline"]["unchanged_literal_baseline"]["profile"]
        # Inputs may cross the JSON boundary before this reducer pool.
        before = {int(r): n for r, n in before.items()}
        after = audited["profile"]
        delta = {r: after.get(r, 0) - before.get(r, 0) for r in sorted(set(before) | set(after))
                 if after.get(r, 0) != before.get(r, 0)}
        ra, rb, a, b = x["residuals"][i], x["residuals"][j], x["widths"][i], x["widths"][j]
        na, nb = ra + a - b, rb + b - a
        expected = Counter(r for r in (na, nb) if r)
        expected.subtract(r for r in (ra, rb) if r)
        need(delta == {r: n for r, n in expected.items() if n}, "complete profile equals exact two-bin delta")
        need(sum(r * n for r, n in delta.items()) == 0
              and na * na + nb * nb - ra * ra - rb * rb == score > 0, "mass conservation and strict spread")
        idle_before = controls_result["baseline"]["unchanged_literal_baseline"]["idle"]
        need(sum(audited["idle"].values()) <= sum(idle_before.values()) and max(audited["idle"]) <= 48,
             "nonincreasing positive idle-child count and maximum rank48")
        need(all(0 < r < 73 for r in before) and all(0 < r < 73 for r in after)
              and sum(r * n for r, n in before.items()) < 73 * 66304
              and sum(before.values()) > 66304 and sum(after.values()) > 66304, "both complete moment roots in (0,1)")
        literal = dict(columns=fill.COLUMNS,
                       dispatch_overrides=x["record"]["data"]["allocation/FILL.json.gz"]["dispatch_overrides"], rows=changed)
        fill_ref = latest._artifact(directory / "FILL.json.gz", gzip.compress(latest._json_bytes(literal), compresslevel=6, mtime=0))
        profile_ref = latest._artifact(directory / "PROFILE.json", latest._json_bytes(after))
        out["candidate"] = dict(fill_artifact=fill_ref, profile_artifact=profile_ref, pair=best["canonical_pair"],
                                 canonical_indices=[i, j], row_indices=[oi, oj], old_rows=[list(old_i), list(old_j)],
                                 new_rows=[list(changed[oi]), list(changed[oj])], widths=[a, b],
                                 capacities=[x["windows"][i][0], x["windows"][j][0]],
                                 residuals_before=[ra, rb], residuals_after=[na, nb], square_gain=score,
                                 complete_profile_delta=delta, baseline_profile=before, complete_profile=after,
                                 literal_audit=audited, indexed_direct_witness_control=True,
                                 exact_strict_moment_decrease=True, positive_idle_child_count_nonincreasing=True,
                                 maximum_idle_rank=48, physical_family_sets_may_change=True,
                                 proof="Fixed local bill; two-bin strict majorization preserves mass and lowers every p-power moment for0<p<1. Both full moments strictly increase in kappa and their roots lie in(0,1).",
                                 admission_status="PENDING complete changed-obligation and explicit rational separator validation")
    out["cpu_seconds"] = time.process_time() - started
    return out
