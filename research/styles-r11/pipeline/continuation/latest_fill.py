"""Pinned PR2917 inert-data adapter and registered C2 same-call exchanges.

The allocation uses 74 replicas while its inherited owner template and PLAN
describe 37.  The adapter checks the literal two-copy interleaving against
PLAN.order and binds the doubled live stock to CLAIM and the physical invoice.
It derives (start, stop] owner windows from the unchanged controller events and
the actual 666-call order.  No factor is chosen from a reported exponent.

Only the trusted r11 word, Bounds and fill implementations are imported.
Fetched .py/.sh data are authenticated as bytes and never imported or executed.
prepare() loads heavy objects once in the parent; only pool.py launches tasks.
The same-call census below is adapted from frozen continuation/fill_search.py;
its exact spread criterion, tie break and controls are unchanged.  This is an
existing finite allocation technique, with no sandpile-group claim.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
from pathlib import Path
import gzip
import hashlib
import json
import math
import os
import random
import sys
import time

PIPELINE = Path(__file__).resolve().parent.parent
RR = PIPELINE.parent
HEAD = "224bd5e56041c40078ff6b5fa7393733a215de5c"
MANIFEST_SHA = "2efa79d1a44d46ca51b9d35a1392fec87514776585f66d372e20d7ccbbcee764"
PINS_SHA = "4d62f7caf94a102ebb83feb3beca6ebeb1ab9637901ff51cc84e5beeb15d2a65"
DIRECTORY = RR / "data/continuation-01/pr2917"
WORD_FILES = {"gauge44": "data/WORD-base.json.gz", "extra": "data/WORD-extra.json.gz"}
TRUSTED = {"fill.py": "9ca05b47016ddbbb4a6713c981932d63a6eaecdd27f3604fcfb66877f239fc4a",
           "wordio.py": "a9c254acdc04c3302ed0a31d9e0da39a8e3348aa20d189798e86539464fd81d4"}
_STATE = None


def _need(ok, message):
    if not ok:
        raise ValueError(message)


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _modules():
    _need(not sys.flags.optimize, "enabled assertions required")
    for filename, digest in TRUSTED.items():
        _need(_sha(PIPELINE / filename) == digest, "trusted source drift: " + filename)
    if str(PIPELINE) not in sys.path:
        sys.path.insert(0, str(PIPELINE))
    import fill
    import wordio
    return fill, wordio


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def _profile(value):
    result = {}
    for rank, count in value.items():
        r = int(rank)
        _need(str(r) == str(rank) and 0 < r < 73, "canonical positive rank below dimension")
        _need(type(count) is int and count >= 0, "nonnegative integer multiplicity")
        if count:
            result[r] = count
    return dict(sorted(result.items()))


def _artifact(path, raw):
    path = Path(path)
    if path.exists():
        _need(path.read_bytes() == raw, "refuse to replace a different candidate artifact")
    else:
        path.write_bytes(raw)
    return dict(path=str(path.relative_to(RR)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def _checkpoint(directory, value):
    temporary = directory / "CHECKPOINT.tmp.json"
    temporary.write_bytes(_json_bytes(value))
    os.replace(temporary, directory / "CHECKPOINT.json")


def _manifest():
    _need(_sha(DIRECTORY / "MANIFEST.json") == MANIFEST_SHA, "frozen PR2917 manifest hash")
    _need(_sha(RR / "data/words/PINS.json") == PINS_SHA, "inherited attribution hash")
    manifest = json.loads((DIRECTORY / "MANIFEST.json").read_bytes())
    _need(manifest["pr"] == 2917 and manifest["commit"] == HEAD, "registered source head")
    _need(manifest["author"] == "Mason Hale (mason-hale)"
          and manifest["package"] == "research/paired-helper-extension", "source author/package")
    files = {pin["relative_path"]: pin for pin in manifest["files"]}
    _need(len(files) == len(manifest["files"]) == 62, "unique complete acquired source manifest")
    return manifest, files


def provenance():
    """JSON-safe attribution; records.py also retains the original 21 pins."""
    manifest, files = _manifest()
    attrs = []
    for relative in WORD_FILES.values():
        pin = deepcopy(files[relative])
        pin.update(format="BORROW-WORD", pin_key=pin["path"],
                   lineage_attribution="Retain package CREDITS.md/SOURCES.json and every original data/words/PINS.json credit.")
        attrs.append(pin)
    return dict(source_attribution=attrs, source_files=deepcopy(manifest["files"]),
                manifests=[dict(path=str((DIRECTORY / "MANIFEST.json").relative_to(RR)),
                                sha256=MANIFEST_SHA, commit=HEAD, pr=2917,
                                author="Mason Hale (mason-hale)")],
                inherited_pins=dict(path="data/words/PINS.json", sha256=PINS_SHA))


def _load_record():
    fill, wordio = _modules()
    manifest, files = _manifest()
    data = {}
    for relative, pin in files.items():
        path = (RR / pin["local_path"]).resolve()
        _need(path.is_relative_to((DIRECTORY / "package").resolve()), "inert source path confinement")
        raw = path.read_bytes()
        _need(pin["commit"] == HEAD and pin["pr"] == 2917
              and pin["author_login"] == "mason-hale", "source pin identity: " + relative)
        _need(len(raw) == pin["bytes"] and hashlib.sha256(raw).hexdigest() == pin["sha256"],
              "source byte/hash binding: " + relative)
        _need(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() == pin["git_blob"],
              "source Git blob binding: " + relative)
        if relative.endswith((".json", ".json.gz")):
            data[relative] = json.loads(gzip.decompress(raw) if relative.endswith(".gz") else raw)
        # Other files, including renamed executable text, are only hashed.
    for pinfile in ("PINS.json", "ALLOCATION-PINS.json"):
        for relative, digest in data[pinfile].items():
            _need(relative in files and files[relative]["sha256"] == digest,
                  "package internal source pin: " + relative)
    plan, template = data["allocation/vendor/PLAN.json.gz"], data["allocation/vendor/TEMPLATE.json.gz"]
    claim = data["CLAIM.json"]
    literal = data["allocation/FILL.json.gz"]
    order = [tuple(x) for x in data["allocation/ORDER.json"]]
    _need((plan["M"], plan["K"], plan["L"], plan["T"], plan["live"], plan["deficit"])
          == (73, 4, 9, 37, 33152, 11840), "pinned half-template geometry")
    _need((claim["replicas"], claim["calls"], claim["live_families"], claim["helpers"])
          == (74, 666, 66304, 408), "explicit current source geometry")
    lift, remainder = divmod(claim["replicas"], plan["T"])
    _need(lift == 2 and remainder == 0, "explicit integral two-copy lift")
    lifted_order = [call for stage, replica in plan["order"]
                    for call in ((stage, replica), (stage, replica + plan["T"]))]
    _need(order == lifted_order, "actual order equals the literal two-copy interleaving")
    _need(len(order) == len(set(order)) == claim["calls"], "unique complete current call order")
    _need(set(order) == {(s, r) for s in range(plan["L"]) for r in range(claim["replicas"])},
          "all current replica stages covered")
    _need(template["m"] == plan["M"] and template["replica_lift"]["replicas"] == plan["T"]
          and template["replica_lift"]["data_stock"] == plan["live"], "half-template stock binding")
    _need(claim["live_families"] == lift * plan["live"]
          == 2 * plan["K"] * 112 * claim["replicas"], "independent current live-family geometry")
    mass = lift * (plan["M"] * plan["live"] - plan["deficit"])
    _need(mass == (plan["M"] - 1) * claim["live_families"] + 64 * len(order) == 4816512,
          "two-copy and independent coverage rank-mass identities")
    dispatch_rows = data["allocation/DISPATCH.json"]
    dispatch = {(s, r): pid for s, r, pid in dispatch_rows}
    providers = data["allocation/PROVIDERS.json"]
    _need(len(dispatch_rows) == len(dispatch) == len(order) and set(dispatch) == set(order),
          "unique complete dispatch")
    _need(literal["columns"] == fill.COLUMNS, "literal fill columns")
    for s, r, pid in literal["dispatch_overrides"]:
        _need((s, r) in dispatch and pid in providers, "dispatch override binding")
        dispatch[s, r] = pid
    _need(set(providers) == set(WORD_FILES) and set(dispatch.values()) == set(providers), "exact provider coverage")
    words, bounds = {}, {}
    _, boundmod, _ = wordio.borrow_modules()
    for pid, relative in WORD_FILES.items():
        path = RR / files[relative]["local_path"]
        pin = deepcopy(files[relative])
        pin.update(format="BORROW-WORD", pin_key=pin["path"])
        words[pid] = wordio.WordData(data[relative], pin, path)
        bounds[pid] = boundmod.Bounds(str(path))
    widths = [tuple(len(words[dispatch[c]].end[h]) - len(words[dispatch[c]].start[h])
                    for h in words[dispatch[c]].helpers) for c in order]
    profiles = [dict(words[dispatch[c]].paid) for c in order]
    effective_plan = dict(M=plan["M"], K=plan["K"], L=plan["L"], T=claim["replicas"],
                          live=claim["live_families"], deficit=lift * plan["deficit"],
                          order=data["allocation/ORDER.json"], pairs=plan["pairs"], sides=plan["sides"])
    derivation = dict(source_plan="allocation/vendor/PLAN.json.gz", source_template="allocation/vendor/TEMPLATE.json.gz",
                      geometry_claim="CLAIM.json", literal_order="allocation/ORDER.json",
                      source_replicas=plan["T"], actual_replicas=claim["replicas"], lift_factor=lift,
                      exact_order_rule="Replace each (s,r) in the T37 PLAN.order by (s,r),(s,r+37), in that order.",
                      source_live=plan["live"], actual_live=claim["live_families"],
                      source_deficit=plan["deficit"], effective_single_sided_deficit=lift * plan["deficit"],
                      expected_mass=mass, mass_formula="2*(73*33152-11840) = 72*66304+64*666 = 4816512",
                      window_rule="Trusted fill.windows replays unchanged per-replica events over the actual 666-call order; start < t <= stop.",
                      inherited_template_bank_stock_excluded_from_live_denominator=True,
                      inherited_template_native_programs_not_replayed=True,
                      derived_without_claimed_exponent=True)
    source = provenance()
    model = fill.FillModel(name="continuation-pr2917", rows=[tuple(x) for x in literal["rows"]],
                          order=order, widths=widths, local_profiles=profiles,
                          win=fill.windows(template, order),
                          family={int(c): 2 * p + plan["sides"][c] for c, p in plan["pairs"].items()},
                          expected_profile=_profile(data["allocation/PROFILE.json"]), expected_mass=mass,
                          sources=source["source_files"], attributions=source["source_attribution"],
                          source_notes=dict(adapter_derivation=derivation,
                                            profile_source="Canonical pinned words plus literal owner idle remainders"), ports=112)
    return dict(pr="2917", directory=DIRECTORY, manifest=manifest, file_pins=files, data=data, model=model,
                words=words, word_files=dict(WORD_FILES), bounds=bounds, dispatch=dispatch, providers=providers,
                dimension=plan["M"], wires=claim["live_families"], effective_plan=effective_plan,
                adapter_derivation=derivation, prepare_error=None)


def prepare(pr=2917):
    """Load heavy words, template, fill and row lookup arrays once in parent."""
    global _STATE
    _need(str(pr) == "2917", "C2 is registered only on PR2917")
    if _STATE is None:
        record = _load_record()
        model = record["model"]
        used = Counter()
        row_widths, row_bins = [], []
        bycall = [[] for _ in range(model.calls)]
        for index, row in enumerate(model.rows):
            _need(len(row) == 6 and all(type(x) is int for x in row), "integer literal row")
            t, h, owner, child, port, offset = row
            _need(0 <= t < model.calls and 0 <= h < len(model.widths[t]), "literal row role bounds")
            width, key = model.widths[t][h], (owner, child, port)
            row_widths.append(width)
            row_bins.append(key)
            bycall[t].append(index)
            used[key] += width
        row_caps = tuple(model.win[owner, child][0] for owner, child, port in row_bins)
        residuals = tuple(cap - used[key] for cap, key in zip(row_caps, row_bins))
        _STATE = dict(pr="2917", record=record, model=model, row_widths=tuple(row_widths), row_bins=tuple(row_bins),
                      row_caps=row_caps, row_residuals=residuals, bycall=tuple(tuple(x) for x in bycall),
                      source=provenance(), expected_pairs=sum(math.comb(len(x), 2) for x in bycall))
    return dict(pr="2917", calls=_STATE["model"].calls, roles=len(_STATE["model"].rows),
                expected_pairs=_STATE["expected_pairs"], parent_load_once=True,
                adapter_derivation=deepcopy(_STATE["record"]["adapter_derivation"]), **_STATE["source"])


def get_record():
    """Return the in-memory record to admission without loading it again."""
    return _state()["record"]


def _validate_binding(record):
    """Checks run in the registered worker, before the baseline positive control."""
    _, wordio = _modules()
    data, model = record["data"], record["model"]
    plan, template = data["allocation/vendor/PLAN.json.gz"], data["allocation/vendor/TEMPLATE.json.gz"]
    claim, invoice, owner = data["CLAIM.json"], data["evidence/PHYSICAL-INVOICE.json"], data["evidence/EXACT-OWNER-MOMENT.json"]
    _need((model.calls, len(model.rows), set(map(len, model.widths))) == (666, 271728, {408}), "current role geometry")
    _need(_profile(claim["profile"]) == _profile(owner["profile"]) == model.expected_profile, "source complete profile binding")
    _need((owner["calls"], owner["roles"], owner["replicas"], owner["live"], owner["rank_mass"])
          == (666, 271728, 74, 66304, model.expected_mass), "source owner geometry and mass")
    _need((invoice["live"], invoice["physical"], invoice["helpers"], invoice["centres"], invoice["private_zero_buffers"])
          == (66304, 66804, 408, 8, 82), "actual physical invoice geometry")
    _need(invoice["physical_stock_identity"] == dict(data_and_owner_families=66304, local_helpers=408,
          private_centres=8, private_zero_buffers=82, coefficient_work=2), "explicit physical stock components")
    _need(sum(invoice["physical_stock_identity"].values()) == claim["physical_families"] == owner["physical"], "physical stock total")
    _need(invoice["provider_counts"] == dict(Counter(record["dispatch"].values())), "invoice dispatch count")
    children, zero_children, seen, positive_ranks = {}, set(), set(), {}
    rank_scale = (plan["M"] - 1) // plan["L"]
    _need(rank_scale == 8, "exact rank increment per controller level")
    zero_sweeps = []
    for event in template["execution_schedule"]:
        if event["kind"] != "idle_cover_sweep":
            continue
        start, stop = event["from_level"], event["to_level"]
        _need(type(start) is int and type(stop) is int and -1 <= start <= stop < plan["L"], "monotone idle levels")
        _need(len(event["child_indices"]) == 2, "two physical sides per sweep")
        if start == stop:
            zero_sweeps.append(dict(pair=event["pair"], children=event["child_indices"], from_level=start, to_level=stop, rank_increment=0))
        for side, child in enumerate(event["child_indices"]):
            _need(child not in seen, "unique child creation")
            seen.add(child)
            if start == stop:
                zero_children.add(child)
            else:
                children[child] = (event["pair"], side)
                positive_ranks[child] = rank_scale * (stop - start)
    declared = {x["child"] for x in template["idle_children"]}
    _need(set(children).isdisjoint(zero_children) and set(children) | zero_children == seen, "complete disjoint child partition")
    _need(set(children) == declared == set(map(int, plan["pairs"])) == set(map(int, plan["sides"])), "positive child coverage")
    _need(zero_children == {18, 19} and not zero_children.intersection(declared), "only exact zero children excluded")
    _need(all(c not in zero_children for _, c in model.win) and all(r[3] not in zero_children for r in model.rows), "zero children absent from windows/roles")
    bins = {(x["child"], x["port"]): x for x in template["idle_children"]}
    _need(len(bins) == len(template["idle_children"]) == len(children) * 112, "all source idle ports")
    _need(len(model.win) == len(children) * claim["replicas"], "all lifted owner windows")
    for child, (pair, side) in children.items():
        _need((plan["pairs"][str(child)], plan["sides"][str(child)]) == (pair, side), "controller physical family")
        for port in range(112):
            b = bins[child, port]
            _need((b["rank"], b["replicas"]) == (positive_ranks[child], plan["T"]), "half-template idle rank/replicas")
        _need(all(model.win[r, child][0] == positive_ranks[child] for r in range(claim["replicas"])), "lifted bin capacity binding")
    _, boundmod, _ = wordio.borrow_modules()
    checks, aggregate = [], Counter()
    for pid, word in record["words"].items():
        b = record["bounds"][pid]
        widths = tuple(len(word.end[h]) - len(word.start[h]) for h in word.helpers)
        _need((word.v, word.h, len(widths)) == (112, 9, 408) and all(w > 0 for w in widths), "canonical word role geometry")
        _need(word.profile_match and dict(b.Wd.paid) == word.paid and b.Wd.helpers == word.helpers, "independent canonical profile/helper parity")
        _need(tuple(record["providers"][pid]["widths"]) == widths
              and _profile(record["providers"][pid]["actual_paid_profile"]) == word.paid, "canonical provider inventory and profile")
        _need(not b.stat_bad and not b.infeasible and not b.ctrl_bad, "exact Bounds feasibility/static pins")
        _need(set(b.lo) == set(b.hi) == set(b.Wd.gateframe), "exact framed gate coverage")
        for t in b.lo:
            _need(boundmod.contained(b.lo[t], b.Wd.gateframe[t]) and boundmod.contained(b.Wd.gateframe[t], b.hi[t]), "literal frame within exact Bounds")
        checks.append(dict(provider=pid, ordered_widths_verified=True, helpers=len(widths),
                           canonical_profile=word.paid, inventory=dict(Counter(widths)), exact_bounds_verified=True))
    for paid in model.local_profiles:
        aggregate.update(paid)
    _need(dict(aggregate) == _profile(invoice["selected_local_paid_profile"]), "invoice aggregate local bill")
    return dict(status="PASS", word_checks=checks, adapter_derivation=record["adapter_derivation"],
                positive_child_ranks=positive_ranks, zero_increment_sweeps=zero_sweeps,
                complete_profile_source_binding=True, actual_physical_families=66804,
                scope="Canonical frames/Bounds, invoice data binding and literal owner geometry; native programs and outer release not replayed.")

def _state():
    _need(_STATE is not None, "prepare() must run in the parent before pool launch")
    return _STATE


def _exchange(ra, rb, ca, cb, a, b):
    d = a - b
    na, nb = ra + d, rb - d
    feasible = 0 <= na <= ca and 0 <= nb <= cb
    half_square_gain = d * (ra - rb + d)
    return feasible and half_square_gain > 0, na, nb, 2 * half_square_gain


def _controls(model):
    fill, _ = _modules()
    binding = _validate_binding(_state()["record"])
    baseline = fill.audit(model)
    rows = list(model.rows)
    first = 0
    t, h, owner, child, port, offset = rows[first]
    cap = model.win[owner, child][0]
    residual = _state()["row_residuals"][first]
    self_improves = _exchange(residual, residual,
                              cap, cap, model.widths[t][h], model.widths[t][h])[0]
    _need(not self_improves, "self exchange must not be improving")
    bad = list(rows)
    bad[first] = (t, h, owner, child, port, cap)
    errors = {}
    try:
        fill.audit(model, bad, require_profile=False)
    except ValueError as exc:
        errors["overcapacity"] = str(exc)
    _need(errors.get("overcapacity") == "offset capacity", "overcapacity control rejected for expected reason")
    same = next(i for i in range(first + 1, len(rows)) if rows[i][0] == t)
    bad = list(rows)
    other = list(bad[same])
    other[2:5] = [owner, child, port]
    bad[same] = tuple(other)
    try:
        fill.audit(model, bad, require_profile=False)
    except ValueError as exc:
        errors["duplicate_family"] = str(exc)
    _need(errors.get("duplicate_family") == "same-call family collision", "family control rejected for expected reason")
    return dict(status="PASS", schema_binding=binding, unchanged_literal_baseline=baseline,
                no_op_improving=False, rejected_mutants=errors)


def c2_task(seed, output_dir, max_seconds=180):
    """Exhaust the registered same-call pair family; preserve selected data."""
    state = _state()
    fill, _ = _modules()
    model = state["model"]
    directory = Path(output_dir)
    if not directory.is_absolute():
        directory = RR / directory
    directory = directory.resolve()
    _need(directory.is_relative_to(RR.resolve()), "candidate output must stay inside research/styles-r11")
    directory.mkdir(parents=True, exist_ok=True)
    _need(0 < max_seconds <= 540, "internal guard must leave time under the 600-second pool timeout")
    started = time.process_time()
    controls = _controls(model)
    row_widths, caps, residuals = state["row_widths"], state["row_caps"], state["row_residuals"]
    rng = random.Random(int(seed))
    calls = list(range(model.calls))
    rng.shuffle(calls)
    counts = Counter()
    signatures = Counter()
    best, best_key, best_score = None, None, None
    completed_calls = []
    complete = True
    for t in calls:
        if time.process_time() - started > max_seconds:
            complete = False
            break
        indices = list(state["bycall"][t])
        rng.shuffle(indices)
        for position, i in enumerate(indices):
            a, ra, ca = row_widths[i], residuals[i], caps[i]
            hi = model.rows[i][1]
            for j in indices[position + 1:]:
                counts["all_pairs"] += 1
                b = row_widths[j]
                if a == b:
                    counts["equal_width_pairs"] += 1
                    continue
                counts["unequal_width_pairs"] += 1
                rb, cb = residuals[j], caps[j]
                d = a - b
                na, nb = ra + d, rb - d
                if na < 0 or na > ca or nb < 0 or nb > cb:
                    counts["infeasible_capacity_pairs"] += 1
                    continue
                counts["feasible_unequal_pairs"] += 1
                half_gain = d * (ra - rb + d)
                if half_gain <= 0:
                    counts["nonimproving_feasible_pairs"] += 1
                    continue
                counts["strictly_improving_pairs"] += 1
                signature = (min(ra, rb), max(ra, rb), min(na, nb), max(na, nb))
                signatures[signature] += 1
                hj = model.rows[j][1]
                key = (t, min(hi, hj), max(hi, hj))
                score = 2 * half_gain
                if best is None or score > best_score or (score == best_score and key < best_key):
                    best, best_key, best_score = (i, j), key, score
        completed_calls.append(t)
        if len(completed_calls) % 16 == 0 or len(completed_calls) == model.calls:
            _checkpoint(directory, dict(seed=int(seed), complete=False,
                         completed_calls=sorted(completed_calls), counts=dict(counts),
                         selected_pair=best_key, selected_square_gain=best_score,
                         elapsed_cpu_seconds=time.process_time() - started))
    complete = complete and len(completed_calls) == model.calls
    if complete:
        _need(counts["all_pairs"] == state["expected_pairs"] == 55296648,
              "complete registered 666 by choose(408,2) pair coverage")
    result = dict(seed=int(seed), baseline_pr=2917, status="EXPLORATORY" if not complete else "NULL",
                  complete=complete, expected_pairs=state["expected_pairs"], counts=dict(counts),
                  completed_calls=sorted(completed_calls), controls=controls, solver_calls=0,
                  selection="Largest integer increase in sum of squared residuals, then lexicographically smallest (call,helper,helper); no root-based selection.",
                  null_scope="Only exhaustive same-call two-role exchanges on the pinned #2917 fill.",
                  candidate=None, residual_signatures=[dict(before=list(k[:2]), after=list(k[2:]), count=n)
                                                     for k, n in sorted(signatures.items())],
                  scope="Constructive fill gain only. Complete native/supplier/outer admission remains mandatory.",
                  **state["source"])
    if best is not None:
        i, j = best
        # Canonical helper order makes the selected witness seed-independent.
        if model.rows[i][1] > model.rows[j][1]:
            i, j = j, i
        old_i, old_j = model.rows[i], model.rows[j]
        _need(old_i[0] == old_j[0], "same-call witness")
        bare = [list(row[:5]) for row in model.rows]
        bare[i][2:5], bare[j][2:5] = bare[j][2:5], bare[i][2:5]
        changed = fill.compact_rows(model, bare)
        audited = fill.audit(model, changed, require_profile=False)
        before = controls["unchanged_literal_baseline"]["profile"]
        after = audited["profile"]
        delta = {r: after.get(r, 0) - before.get(r, 0) for r in sorted(set(before) | set(after))
                 if after.get(r, 0) != before.get(r, 0)}
        ra, rb = residuals[i], residuals[j]
        good, na, nb, square_gain = _exchange(ra, rb, caps[i], caps[j], row_widths[i], row_widths[j])
        expected_delta = Counter(r for r in (na, nb) if r)
        expected_delta.subtract(r for r in (ra, rb) if r)
        expected_delta = {r: n for r, n in expected_delta.items() if n}
        _need(good and square_gain == best_score and delta == expected_delta, "selected exact residual/profile delta")
        _need(sum(r * n for r, n in delta.items()) == 0, "exact conserved rank mass")
        _need(sum(before.values()) >= 1 and all(0 < r < 73 for r in before)
              and sum(after.values()) >= 1 and all(0 < r < 73 for r in after),
              "strictly increasing complete-profile moments")
        _need(sum(r * n for r, n in before.items()) < 73 * 66304
              and sum(before.values()) > 66304 and sum(after.values()) > 66304,
              "baseline and candidate profile roots in (0,1)")
        fill_data = dict(columns=fill.COLUMNS,
                         dispatch_overrides=state["record"]["data"]["allocation/FILL.json.gz"]["dispatch_overrides"],
                         rows=changed)
        fill_ref = _artifact(directory / "FILL.json.gz", gzip.compress(_json_bytes(fill_data), compresslevel=6, mtime=0))
        profile_ref = _artifact(directory / "PROFILE.json", _json_bytes(after))
        call = model.order[old_i[0]]
        provider = state["record"]["dispatch"][call]
        helpers = state["record"]["words"][provider].helpers
        result["candidate"] = dict(fill_artifact=fill_ref, profile_artifact=profile_ref,
                                    pair=list(best_key), provider=provider,
                                    helper_registers=[helpers[old_i[1]], helpers[old_j[1]]],
                                    row_indices=[i, j], old_rows=[list(old_i), list(old_j)],
                                    new_rows=[list(changed[i]), list(changed[j])],
                                    widths=[row_widths[i], row_widths[j]], capacities=[caps[i], caps[j]],
                                    residuals_before=[ra, rb], residuals_after=[na, nb],
                                    square_gain=square_gain, complete_profile_delta=delta,
                                    baseline_profile=before, complete_profile=after, literal_audit=audited,
                                    exact_strict_moment_decrease=True,
                                    proof="Same local profile and residual mass; feasible two-bin strict majorization. Strict concavity gives lower complete moment for every 0<kappa<1, and both complete moments strictly increase in kappa.",
                                    admission_status="PENDING separate native/supplier/outer and explicit rational separator validation")
        if complete:
            result["status"] = "PASS"
    result["cpu_seconds"] = time.process_time() - started
    _checkpoint(directory, dict(seed=int(seed), complete=complete, status=result["status"],
                 completed_calls=sorted(completed_calls), counts=dict(counts),
                 selected_pair=best_key, selected_square_gain=best_score,
                 elapsed_cpu_seconds=result["cpu_seconds"],
                 candidate_artifact=result["candidate"]["fill_artifact"] if result["candidate"] else None))
    return result
