"""Format the already recorded PLAN 3.2 language objects; run with python -I -B.

This exporter reads inert JSON only. It imports no word, frame, solver, census,
or fetched-source implementation and performs no scientific experiment. It
copies the M0 section/climb data and indexes immutable experiment receipts with
SHA256 hashes and checked RFC 6901 JSON Pointers. It never upgrades their scope.

API: export(output=None) -> the written INDEX.json path. The default output is
results/LANGUAGE. A different output must also be inside results/LANGUAGE.
Each original PINS word receives four files under its full Git blob ID:
SECTION-STRINGS.json.gz, CLIMB-STRINGS.json.gz, PARIKH-LEDGER.json, MOVE-CENSUS.json.
All prospective files must be absent before writing; existing files are never
replaced. Run only after the coordinator authorizes the M5 formatting step.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


PKG = Path(__file__).resolve().parents[1]
ROOT = PKG.parents[1]
DEST = PKG / "results/LANGUAGE"
ALPHABETS = {
    "full": ["section", "operation", "coefficient", "target_role",
             "source_role", "frame_rank", "target_paid_climb", "source_paid_climb"],
    "mid": ["section", "operation", "coefficient", "frame_rank"],
    "rank": ["section", "frame_rank"],
    "op": ["section", "operation", "coefficient"],
    "role": ["section", "operation", "coefficient", "target_role", "source_role"],
    "registers": ["section", "operation", "coefficient", "target_register",
                  "source_register", "frame_rank"],
}
RECEIPT_FAMILIES = ("P-1", "L-2", "L-6", "L-7", "S-1", "L7-GUARD-ORDER", "L-9")


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n").encode()


def _pointer_part(value):
    return str(value).replace("~", "~0").replace("/", "~1")


def _at_pointer(value, pointer):
    if pointer and not pointer.startswith("/"):
        raise ValueError("JSON Pointer must be empty or begin with /")
    for part in pointer.split("/")[1:]:
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


class Input:
    def __init__(self, path):
        self.path = Path(path).resolve()
        if not self.path.is_relative_to(PKG):
            raise ValueError("Export inputs must be inside research/styles-r11")
        self.raw = self.path.read_bytes()
        self.decoded = (gzip.decompress(self.raw)
                        if self.path.suffix == ".gz" else self.raw)
        self.data = json.loads(self.decoded)
        self.digest = _digest(self.raw)

    def ref(self, pointer=""):
        _at_pointer(self.data, pointer)  # Fail before creating dangling references.
        result = dict(path=str(self.path.relative_to(ROOT)), sha256=self.digest,
                      bytes=len(self.raw), json_pointer=pointer)
        if self.path.suffix == ".gz":
            result["uncompressed_sha256"] = _digest(self.decoded)
        if self.path.name == "RESULT.json":
            result.update(experiment=self.data["experiment"], seed=self.data["seed"],
                          recorded_status=self.data["status"],
                          preregistration_sha256=self.data["preregistration_sha256"])
        return result


def _tasks(receipt):
    for i, wrapper in enumerate(receipt.data.get("statistics", {}).get("tasks", [])):
        if wrapper.get("status") == "OK" and isinstance(wrapper.get("result"), dict):
            yield f"/statistics/tasks/{i}/result", wrapper["result"]


def _same_attribution(attr, key, pin):
    if not isinstance(attr, dict):
        return False
    return (attr.get("git_blob") == pin["git_blob"]
            and attr.get("sha256") == pin["sha256"]
            and attr.get("pin_key", key) == key)


def _pin_path(key):
    return ROOT / key if "/" in key else PKG / "data/words" / key


def _word_tasks(receipts, key, pin):
    """Match a task by recorded pin metadata, or S1's exact recorded word path."""
    expected = _pin_path(key).resolve()
    for receipt in receipts:
        enrolled = receipt.data.get("source_attribution", [])
        if not any(_same_attribution(a, key, pin) for a in enrolled):
            continue
        for pointer, result in _tasks(receipt):
            if _same_attribution(result.get("attribution"), key, pin):
                yield receipt, pointer, result
                continue
            word = result.get("statistics", {}).get("word")
            if word:
                word_path = Path(word)
                if not word_path.is_absolute():
                    word_path = ROOT / word_path
                if word_path.resolve() == expected:
                    yield receipt, pointer, result


def _unavailable(reason):
    return dict(status="EXPLORATORY", availability="unavailable", reason=reason,
                certificate=None, phi=None)


def _word_stage(key, pin):
    if Path(key).name.startswith("retired5-"):
        return "retired5"
    return str(pin["pr"]) if pin.get("pr") is not None else None


def _ledger(common, key, pin, receipts):
    stage = _word_stage(key, pin)
    variant = "extra" if "extra" in Path(key).name else "base"
    output = dict(common, object="parikh_ledger_index", status="EXPLORATORY",
                  lineage_stage=stage, variant=variant, incident_edges=[],
                  complete_ledger_receipts=[], scalar_ledger_receipts=[],
                  guarded_order_receipts=[],
                  scope="Indexes recorded lineage deltas and their local guards. "
                        "A profile identity alone is not a guarded production proof.")
    scalar = {}
    for receipt in receipts["L-6"]:
        for pointer, result in _tasks(receipt):
            if result.get("experiment") != "L-6":
                continue
            output["scalar_ledger_receipts"].append(receipt.ref(pointer))
            for i, row in enumerate(result.get("lineage", [])):
                scalar.setdefault((row["before"], row["after"]), []).append(
                    dict(reference=receipt.ref(f"{pointer}/lineage/{i}"),
                         recorded_status=row["status"], dphi=row["dphi"],
                         exact_dkappa=row["exact_dkappa"], law_dkappa=row["law_dkappa"]))
    for receipt in receipts["L-7"]:
        for pointer, result in _tasks(receipt):
            if result.get("experiment") != "L-7":
                continue
            output["complete_ledger_receipts"].append(receipt.ref(pointer))
            guard = result["guarded_replay"]
            for i, row in enumerate(result["lineage"]):
                if stage not in (row["before"], row["after"]):
                    continue
                choices = [(j, v) for j, v in enumerate(row["variants"])
                           if v["variant"] == variant]
                if len(choices) != 1:
                    raise ValueError(f"Ambiguous L7 variant for {key}")
                j, v = choices[0]
                endpoint_pointer = f"{pointer}/lineage/{i}"
                gv = [(j, v) for j, v in enumerate(guard["variants"])
                      if v["variant"] == variant]
                if len(gv) != 1:
                    raise ValueError(f"Ambiguous L7 guards for {key}")
                gj, guarded = gv[0]
                guard_pointer = f"{pointer}/guarded_replay/variants/{gj}"
                before, after = row["before"], row["after"]
                if (before, after) in (("2679", "2745"), ("2745", "2751")):
                    guards = dict(_unavailable("The early transition has exact "
                        "profile bookkeeping but no validated decomposition into "
                        "the registered move alphabet."),
                        obligation=receipt.ref(guard_pointer + "/early_transition_obligations"))
                elif (before, after) == ("2751", "2766"):
                    guards = dict(availability="recorded_local_guard_audit",
                        reference=receipt.ref(guard_pointer + "/refit2751_to_2766"),
                        scope="Recorded exact frame refit and its stated inverse scope.")
                else:
                    names = ({"refit5", "alias5", "refit5c"} if after == "retired5"
                             else {"refit7", "hostmove2", "alias7", "refit7c"})
                    guards = dict(availability="recorded_local_guard_audits",
                        references=[receipt.ref(f"{guard_pointer}/stages/{k}")
                                    for k, s in enumerate(guarded["stages"])
                                    if s["stage"] in names],
                        scope="Named production stages; linked guards/register deltas "
                              "are retained. A complete consumed/created predicate "
                              "inventory is not inferred from those checks.")
                output["incident_edges"].append(dict(
                    before=before, after=after, seed=receipt.data["seed"],
                    complete_delta=row["complete_delta"], idle_delta=row["idle_delta"],
                    idle_status=row["idle_status"], sum_mass_neutral=row["sum_mass_neutral"],
                    local_delta_per_call=v["local_delta_per_call"],
                    exact_profile_sum=v["exact_profile_sum"],
                    registers_touched=[x["register"] for x in v["registers"]],
                    register_delta_reference=receipt.ref(f"{endpoint_pointer}/variants/{j}"),
                    guarded_productions=guards,
                    scalar_evidence=scalar.get((before, after), [])))
    if output["incident_edges"]:
        for receipt in receipts["L7-GUARD-ORDER"]:
            for pointer, result in _tasks(receipt):
                if result.get("experiment") == "L7-GUARD-ORDER":
                    output["guarded_order_receipts"].append(receipt.ref(pointer))
        output["availability"] = "recorded_incident_edges_with_stated_guard_gaps"
    else:
        output["availability"] = "unavailable_for_this_word"
        output["missing"] = _unavailable("No enrolled L7 lineage edge for this "
            "word. The linked global ledger is context, not a derivation of this word.")
    output["preconditions_consumed_created"] = _unavailable(
        "Local guard and register-change records are linked where available; "
        "a complete per-production consumed/created predicate ledger was not recorded.")
    output["new_prices_or_claims"] = False
    return output


def _move_census(common, key, pin, receipts):
    atlases = []
    for receipt, pointer, result in _word_tasks(receipts["S-1"], key, pin):
        statistics = result["statistics"]
        atlas_pointer = pointer + "/statistics"
        atlases.append(dict(reference=receipt.ref(atlas_pointer),
            seed=receipt.data["seed"], task_status=result["status"],
            exact_certificate_pass=statistics["exact_certificate_pass"],
            current_alias_edges_verified=statistics["current_alias_edges_verified"],
            statement=statistics["statement"], scope=statistics["scope"],
            lives=receipt.ref(atlas_pointer + "/lives"),
            slots=receipt.ref(atlas_pointer + "/slots"),
            hall_koenig_certificate=receipt.ref(atlas_pointer + "/certificate"),
            frame_bounds=receipt.ref(atlas_pointer + "/bounds"),
            near_miss_floor_gap_one=receipt.ref(atlas_pointer + "/near_miss_floor_gap_one"),
            hostee_path_witnesses=receipt.ref(atlas_pointer + "/augmenting_paths")))
    if len({a["seed"] for a in atlases}) < 2:
        raise ValueError(f"Missing two recorded S1 atlas runs for {key}")
    saturation = []
    for receipt in receipts["L-9"]:
        for pointer, result in _tasks(receipt):
            if result.get("experiment") != "L-9":
                continue
            if any(_same_attribution(a, key, pin) for a in result.get("attribution", [])):
                saturation.append(dict(reference=receipt.ref(pointer),
                    direct_alias_pairs=receipt.ref(pointer + "/direct_alias_pairs"),
                    hostee_augmenting_paths=receipt.ref(pointer + "/hostee_augmenting_paths"),
                    bounds=receipt.ref(pointer + "/bounds"),
                    refit_optimum_control=receipt.ref(pointer + "/refit_optimum_control"),
                    phi_scope=result["phi_scope"], unresolved=result["unresolved"],
                    null_protocol=result["null_protocol"], status=result["status"]))
    return dict(common, object="move_census_index", status="EXPLORATORY",
        availability="recorded_scoped_atlas", atlas_runs=atlases,
        saturation_runs=saturation,
        alias_guards=dict(availability="recorded_floor_time_graph_and_witnesses",
            scope="The S1 lives/slots and Hall/Koenig certificate concern exact "
                  "individual time/dimension compatibility. They do not certify "
                  "simultaneous constructive refits or all lineage productions."),
        refittable_frame_slack=dict(availability="recorded_bounds_and_slack_histogram",
            scope="S1 stores propagated floor/ceiling feasibility and a slack "
                  "histogram. Full per-gate constructive moves and their Phi gains "
                  "are not supplied by this index."),
        hostee_paths=dict(availability="recorded_path_witnesses",
            scope="S1 stores one shortest augmenting path per unmatched follower, "
                  "not all paths. When this exact word has an L9 receipt, that "
                  "separate index contains the registered length-three path census. "
                  "A necessary-guard path is not a priced constructive production."),
        saturation_scope=("L9 receipt applies only to the exact attributed word."
            if saturation else "No completed L9 task attributed to this exact word; "
            "no saturation claim is transferred from another word or variant."),
        restorable_width_cuts=_unavailable("No recorded constructive cut census for this word."),
        constructive_phi=_unavailable("Necessary guards and graph paths alone do "
            "not determine a constructive local-plus-idle Phi delta."),
        kernel_identity_classes=_unavailable("No recorded constructive kernel-identity census."),
        new_census_runs=0, new_prices_or_claims=False)


def _load_receipts(registry):
    rows = {r["id"]: r for r in registry.data["experiments"]}
    found = {}
    for family in RECEIPT_FAMILIES:
        row = rows.get(family, {})
        files = row.get("result_files", [])
        found[family] = [Input(PKG / name) for name in files]
        for receipt in found[family]:
            if receipt.data.get("experiment") != family:
                raise ValueError("Registry receipt experiment mismatch")
        if family in ("P-1", "L-2", "L-6", "L-7", "S-1"):
            if len({r.data["seed"] for r in found[family]}) < 2:
                raise ValueError(f"Missing two registered receipts for {family}")
    return found


def export(output=None):
    """Write four immutable objects per original pinned word and a hashed index."""
    output = DEST if output is None else Path(output)
    output = output.resolve()
    if not output.is_relative_to(DEST.resolve()):
        raise ValueError("Output must be results/LANGUAGE or a directory below it")
    pins = Input(PKG / "data/words/PINS.json")
    registry = Input(PKG / "EXPERIMENTS.json")
    receipts = _load_receipts(registry)
    exporter = Path(__file__).read_bytes()
    common_provenance = dict(pins=pins.ref(), registry_snapshot_sha256=registry.digest,
        exporter=dict(path=str(Path(__file__).resolve().relative_to(ROOT)),
                      sha256=_digest(exporter)),
        input_policy="Inert JSON reads only; no source words or fetched code executed.")
    files, index_words, input_manifest = {}, [], {}
    all_inputs = [pins, registry] + [r for family in receipts.values() for r in family]
    for item in all_inputs:
        input_manifest[str(item.path.relative_to(ROOT))] = item.ref()
    seen_blobs = set()
    for key, pin in sorted(pins.data["files"].items()):
        blob = pin["git_blob"]
        if blob in seen_blobs:
            raise ValueError("Duplicate PINS blob would alias output paths")
        seen_blobs.add(blob)
        language = Input(PKG / "results/M0/language" / (blob[:12] + ".json.gz"))
        data = language.data
        attr = data["attribution"]
        if not _same_attribution(attr, key, pin) or any(attr.get(k) != v for k, v in pin.items()):
            raise ValueError(f"M0 language attribution differs from PINS: {key}")
        if data["profile_match"] is not True or data["paid"] != pin["local_profile"]:
            raise ValueError(f"M0 recorded profile parity unavailable: {key}")
        for section, alphabets in data["section_strings"].items():
            if set(alphabets) != set(ALPHABETS):
                raise ValueError(f"Missing stored alphabet in {key}/{section}")
        if not {"A", "cut", "B", "precondition", "cleanup"} <= set(data["section_strings"]):
            raise ValueError(f"Missing mandatory stored section: {key}")
        input_manifest[str(language.path.relative_to(ROOT))] = language.ref()
        common = dict(schema_version=1, artifact_status="EXPORTED_EXISTING_EVIDENCE",
            attribution=attr, pin_key=key,
            pins_entry=pins.ref("/files/" + _pointer_part(key)),
            provenance=common_provenance, language_source=language.ref(),
            family=data["family"], no_new_experiment=True)
        cleanup = [dict(reference=r.ref(p), recorded_status=t["status"],
                        family=t["family"], exact=t["exact"],
                        literal_equality=t["literal_equality"],
                        production=t["production"], cleanup_gates=t["cleanup_gates"],
                        recorded_gates=t.get("recorded_gates"),
                        first_mismatch=t.get("first_mismatch"),
                        endpoint_checks=t.get("endpoint_checks"),
                        evidence_scope=(
                            "FULL-WORD literal production comparison plus separately "
                            "recorded forward/dual arithmetic endpoint replay."
                            if "endpoint_checks" in t else
                            "BORROW-WORD exact literal derived-production equality; "
                            "this L2 task does not report a separate endpoint replay."))
                   for r, p, t in _word_tasks(receipts["L-2"], key, pin)]
        if len({x["reference"]["seed"] for x in cleanup}) < 2:
            raise ValueError(f"Missing two cleanup controls for {key}")
        parity = [r.ref(p) for r, p, _ in _word_tasks(receipts["P-1"], key, pin)]
        if len({r["seed"] for r in parity}) < 2:
            raise ValueError(f"Missing two canonical parity receipts for {key}")
        sections = dict(common, object="section_strings", alphabets=ALPHABETS,
            forward_order=["A", "cut", "B"], forward_includes_warps=True,
            derived_sections_are_independent_screen_text=False,
            section_strings=data["section_strings"],
            derived_sections=data["derived_sections"],
            derived_control_receipts=cleanup,
            recorded_profile_match=data["profile_match"], parity_receipts=parity,
            compensation_stream=(dict(availability="recorded")
                if "compensation" in data["section_strings"] else
                _unavailable("The M0 FULL-WORD language artifact has no separate "
                    "compensation token stream; the linked L2 record retains its "
                    "arithmetic/control result. No missing stream is fabricated.")),
            convention="Coefficients are exact signed reduced rationals. B warps "
                "are WARP letters, including terminal B warps. Cleanup and "
                "compensation are derived controls, never independent screen text.")
        climbs = dict(common, object="climb_strings",
            climb_strings=data["climb_strings"],
            paid_rank_strings={r: [j["rank"] for j in item["jumps"]]
                               for r, item in data["climb_strings"].items()},
            paid_profile=data["paid"], report_local_profile=pin["local_profile"],
            recorded_profile_match=data["profile_match"], parity_receipts=parity,
            note=data["note"],
            convention="Paid rank strings preserve stored jump order and include "
                "explicit centre-descent branch children where recorded. They "
                "are not asserted to be monotone register continuations; jump "
                "kinds, roles, entrance dimensions, widths and endpoint motifs "
                "remain in the complete climb_strings records.")
        values = {"SECTION-STRINGS.json.gz": sections,
                  "CLIMB-STRINGS.json.gz": climbs,
                  "PARIKH-LEDGER.json": _ledger(common, key, pin, receipts),
                  "MOVE-CENSUS.json": _move_census(common, key, pin, receipts)}
        outputs = {}
        for name, value in values.items():
            raw = _json_bytes(value)
            encoded = gzip.compress(raw, mtime=0) if name.endswith(".gz") else raw
            path = output / blob / name
            files[path] = encoded
            outputs[name] = dict(path=str(path.relative_to(ROOT)), sha256=_digest(encoded),
                                 bytes=len(encoded), uncompressed_sha256=_digest(raw))
        index_words.append(dict(pin_key=key, attribution=attr, files=outputs))
    index = dict(schema_version=1, object="language_export_index", no_new_experiment=True,
        word_count=len(index_words), files_per_word=4, provenance=common_provenance,
        reference_convention="All paths are relative to the repository root. JSON "
            "Pointers follow RFC 6901 and are checked against the hashed input bytes.",
        inputs=input_manifest, words=index_words,
        registry_snapshot=registry.data,
        receipt_selection="Only result_files named by this registry snapshot; no "
            "glob-based latest-run selection or skipped-family execution.",
        scientific_scope="Formatting and indexing only. Missing guarded productions, "
            "constructive Phi, cuts and non-lineage derivations remain explicitly "
            "EXPLORATORY/unavailable. No census target is priced or claimed here.")
    files[output / "INDEX.json"] = _json_bytes(index)
    # Validate every input and construct every output before any filesystem write.
    existing = [str(path) for path in files if path.exists()]
    if existing:
        raise FileExistsError("Immutable export already exists: " + existing[0])
    if any(not path.resolve().is_relative_to(DEST.resolve()) for path in files):
        raise ValueError("An output path escapes results/LANGUAGE")
    for path, raw in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(raw)
    return output / "INDEX.json"


def main():
    if not sys.flags.isolated:
        raise SystemExit("Run this trusted exporter with python -I -B")
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEST)
    args = parser.parse_args()
    print(export(args.output))


if __name__ == "__main__":
    main()
