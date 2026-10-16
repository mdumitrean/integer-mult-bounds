"""Guarded production replay used by L-7; no experiments run on import.

The source-pinned PR2679 auditor and stage patch functions are approved baseline
tools named by RUNBOOK.md.  Later fetched PR code is never imported.  Stages are
JSON data; audit output is captured in memory so no predecessor package changes.
"""
from __future__ import annotations

from collections import Counter
import contextlib
import copy
import difflib
import gzip
import hashlib
import importlib.util
import io
import json
import random
import time

import growth as G

AUDITOR_SHA = "a38940094f7d19cd6376aafdd4734fa68eabc9aff4c98c3c4a3e9540328b1c90"
PATCH_SHA = "9b3287f189c4f29c1a8bdb1ba01fdcfe14a57d87b50fa4f2f646fb2346ab01ce"
STAGES = ("refit5", "alias5", "refit5c", "refit7", "hostmove2", "alias7", "refit7c")


def _load_tool(name, relative, digest):
    path = G.PKG / relative
    if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        raise ValueError(f"approved baseline tool digest mismatch: {relative}")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MemoryPath:
    def __init__(self, name, data=b""):
        self.name, self.data = name, data
    def read_bytes(self):
        return self.data
    def write_text(self, text):
        self.data = text.encode()


def _audit(au, word, label):
    data = json.dumps(word, separators=(",", ":")).encode()
    inp = MemoryPath(label + ".json.gz", gzip.compress(data, mtime=0))
    out = MemoryPath(label + ".audit.json")
    log = io.StringIO()
    start = time.monotonic()
    try:
        with contextlib.redirect_stdout(log):
            report = au.run_borrow(inp, out, None, None, word, data, start)
        return dict(status="PASS", audit=report, wall_seconds=time.monotonic() - start)
    except (AssertionError, RuntimeError, ValueError, KeyError, IndexError) as exc:
        return dict(status="REJECT", reason=f"{type(exc).__name__}: {exc}"[:500],
                    last_log_lines=log.getvalue().splitlines()[-3:], wall_seconds=time.monotonic() - start)


def _regs(gate):
    return gate[1:3] if gate[0] == "add" else gate[1:2]


def _refit(word, patch):
    result = copy.deepcopy(word)
    for section, index, frame in patch["frames"]:
        result[section][index][-1] = copy.deepcopy(frame)
    result["report"]["local_profile"] = copy.deepcopy(patch["local_profile"])
    return result


def _apply(wp, word, stage, patch):
    return _refit(word, patch) if stage.startswith("refit") else wp.apply_lowfour(word, patch)


def build_stages(tag="base"):
    """Return pinned stage payloads for parent-owned exact-census preparation.

    This only applies declared JSON patches. Guard tests and auditor execution
    remain separate in ``audit``; rebuilding is not presented as a certificate.
    """
    wp = _load_tool("styles_r11_pr2679_stage_patches", "vendor/word_patch_pr2679.py", PATCH_SHA)
    states = [("2751", G.read_json(G.resolve_word("2751", tag)[0]))]
    for stage in STAGES:
        patch = G.read_json(G.PKG / f"inputs/{stage}_43{tag}.json")
        states.append((stage, _apply(wp, states[-1][1], stage, patch)))
    return states


def _frame_before(au, w, register, position):
    current = au.basis([w["ports"][register]]) if register < 112 else au.basis(w["start_extra"].get(str(register), []))
    for e in w["A"]:
        if e[0] == "warp":
            if e[1] == register:
                current = au.basis(e[4])
        elif register in _regs(e):
            current = au.basis(e[-1])
    bypos = {}
    for rec in w["warps"]:
        bypos.setdefault(rec[0], []).append(rec)
    for p in range(position):
        for rec in bypos.get(p, []):
            if rec[1] == register:
                if current != au.basis(rec[3]):
                    raise ValueError("pre-existing warp frame mismatch")
                current = au.basis(rec[4])
        e = w["B"][p]
        if register in _regs(e):
            current = au.basis(e[-1])
    return current


def _guards(au, wp, before, after, stage, patch):
    """Check production-specific predicates in addition to the global auditor."""
    checks = {}
    if stage.startswith("refit"):
        checks["only_frames_and_profile"] = all(before.get(k) == after.get(k) for k in set(before) | set(after)
            if k not in {"A", "B", "restore", "report"}) and all(
            len(before[s]) == len(after[s]) and all(a[:-1] == b[:-1] for a, b in zip(before[s], after[s]))
            for s in ("A", "B", "restore"))
        actual = {(s, i) for s in ("A", "B", "restore") for i, (a, b) in enumerate(zip(before[s], after[s])) if a != b}
        checks["declared_frames_exact"] = actual == {(s, i) for s, i, _ in patch["frames"]}
        return checks
    checks["declared_scalar_gate_edits"] = wp.kernel_gate_edit(before["B"], after["B"]) == patch["declared_gate_edit"]
    unchanged = ("A", "restore", "helper_final", "compensation", "initial_corrections", "precondition", "cut",
                 "target_levels", "centers", "center_frames", "ports", "prelude_events")
    checks["unrelated_fields_unchanged"] = all(before[k] == after[k] for k in unchanged)
    if stage.startswith("alias"):
        aliases = patch["aliases"]
        new_helpers = [a["h"] for a in aliases]
        checks["removed_exact_helpers"] = after["removed"] == before["removed"] + new_helpers
        checks["entrance_removed_exact_helpers"] = after["start_extra"] == {
            k: value for k, value in before["start_extra"].items() if int(k) not in new_helpers}
        checks["new_warps_exact"] = after["warps"] == before["warps"] + [
            [a["pos"], a["L"], a["G"], a["U"], a["E"]] for a in aliases]
        expected_b = copy.deepcopy(before["B"])
        for a in aliases:
            h, lender, pos = a["h"], a["L"], a["pos"]
            first = min((p for p, e in enumerate(before["B"]) if h in _regs(e)), default=-1)
            last = max((p for p, e in enumerate(before["B"]) if lender in _regs(e)), default=-1)
            checks[f"{h}<-{lender}:retired_before_entry"] = last < pos == first
            checks[f"{h}<-{lender}:free_lender"] = not any(lender in _regs(e) for e in before["restore"]) and not any(
                rec[1] == lender and rec[0] > last for rec in before["warps"])
            checks[f"{h}<-{lender}:private_follower"] = str(h) in before["start_extra"] and str(h) not in before["helper_final"] and not any(
                h in _regs(e) for sec in ("precondition", "compensation", "A", "cut") for e in before[sec])
            checks[f"{h}<-{lender}:literal_U"] = _frame_before(au, before, lender, pos) == au.basis(a["U"])
            checks[f"{h}<-{lender}:equal_dimensions"] = len(au.basis(a["U"])) == len(au.basis(a["E"]))
            checks[f"{h}<-{lender}:entrance_containment"] = au.contained(au.basis(a["E"]), au.basis(before["B"][pos][-1]))
            try:
                au.check_G_frames(a["G"], a["U"], a["E"], 9)
                checks[f"{h}<-{lender}:invertible_G_maps_U_to_E"] = True
            except (RuntimeError, AssertionError, ValueError):
                checks[f"{h}<-{lender}:invertible_G_maps_U_to_E"] = False
            for e in expected_b[pos:]:
                for j in (1, 2) if e[0] == "add" else (1,):
                    if e[j] == h:
                        e[j] = lender
        checks["exact_follower_relabelling"] = expected_b == after["B"]
    elif stage == "hostmove2":
        checks["inventory_unchanged"] = before["removed"] == after["removed"] and before["start_extra"] == after["start_extra"]
        expected_b = copy.deepcopy(before["B"])
        expected_warps = copy.deepcopy(before["warps"])
        for move in patch["moves"]:
            old = move["old_record"]
            new_lender, pos = move["L_new"], move["pos"]
            old_lender = old[1]
            op = before["warps"].index(old)
            last = max((p for p, e in enumerate(before["B"]) if new_lender in _regs(e)), default=-1)
            checks[f"{old_lender}->{new_lender}:retired_before_entry"] = last < pos
            checks[f"{old_lender}->{new_lender}:free_lender"] = not any(new_lender in _regs(e) for e in before["restore"]) and not any(
                rec[1] == new_lender for rec in before["warps"])
            checks[f"{old_lender}->{new_lender}:literal_U"] = _frame_before(au, before, new_lender, pos) == au.basis(move["U"])
            try:
                au.check_G_frames(move["G"], move["U"], move["E"], 9)
                checks[f"{old_lender}->{new_lender}:invertible_G_maps_U_to_E"] = True
            except (RuntimeError, AssertionError, ValueError):
                checks[f"{old_lender}->{new_lender}:invertible_G_maps_U_to_E"] = False
            expected_warps[op] = [pos, new_lender, move["G"], move["U"], move["E"]]
            for e in expected_b[pos:]:
                for j in (1, 2) if e[0] == "add" else (1,):
                    if e[j] == old_lender:
                        e[j] = new_lender
            checks[f"{old_lender}->{new_lender}:old_lender_released"] = not any(old_lender in _regs(e) for e in after["B"] + after["restore"])
        checks["exact_hostee_scalar_relabelling"] = len(expected_b) == len(after["B"]) and all(
            a[:-1] == b[:-1] for a, b in zip(expected_b, after["B"]))
        checks["warp_indices_preserved"] = expected_warps == after["warps"]
    else:
        raise ValueError(stage)
    return checks


def _canonical(word, label, assert_profile=True):
    from wordio import WordData
    return WordData(word, {"source": label, "author": "Marius-Paul Dumitrean; pinned #2802 stage records"},
                    assert_profile=assert_profile)


def _fresh_profile(word):
    # For an order control, the report is recalculated to stop a stale report
    # from becoming the only reason the auditor rejects an invalid stage.
    w = copy.deepcopy(word)
    try:
        c = _canonical(w, "order-control", assert_profile=False)
        w["report"]["local_profile"] = {str(r): count for r, count in c.paid.items()}
        w["report"]["width_inventory"] = {str(r): count for r, count in Counter(
            len(c.end[r]) - len(c.start[r]) for r in c.helpers).items()}
        return w, None
    except (AssertionError, RuntimeError, ValueError, KeyError, IndexError) as exc:
        return w, f"{type(exc).__name__}: {exc}"[:500]


def _early_obligation(wp, before, after, before_name, after_name):
    """Expose the exact unmet derivation obligation, not a missing-data claim.

    Both endpoints, every changed scalar gate and the held source recipes are
    available.  Valid endpoint free-algebra replay is not by itself a sequence
    of the plan's bounded productions with their guards.
    """
    sections, touched = {}, set()
    for section in ("precondition", "compensation", "A", "cut", "B", "restore", "cleanup"):
        old, new = before[section], after[section]
        if old == new:
            continue
        a = [json.dumps(g, separators=(",", ":")) for g in old]
        b = [json.dumps(g, separators=(",", ":")) for g in new]
        blocks = []
        for op, i, j, k, l in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op == "equal":
                continue
            blocks.append(dict(operation=op, before_indices=[i,j], after_indices=[k,l],
                               before_gates=old[i:j], after_gates=new[k:l]))
            for gate in old[i:j] + new[k:l]:
                touched.update(_regs(gate))
        sections[section] = dict(before_count=len(old), after_count=len(new),
            scalar_gate_edits=wp.kernel_gate_edit(old,new), full_gate_change_blocks=blocks)
    mappings = {}
    for field in ("start_extra", "helper_final", "target_levels"):
        a, b = before.get(field,{}), after.get(field,{})
        changed = {key:dict(before=a.get(key),after=b.get(key)) for key in sorted(set(a)|set(b),key=int)
                   if a.get(key) != b.get(key)}
        if changed:
            mappings[field] = changed
            if field != "target_levels":
                touched.update(map(int,changed))
    warps = []
    for index in range(max(len(before["warps"]),len(after["warps"]))):
        a = before["warps"][index] if index < len(before["warps"]) else None
        b = after["warps"][index] if index < len(after["warps"]) else None
        if a != b:
            warps.append(dict(operator_id=index+1,before=a,after=b))
            touched.update(rec[1] for rec in (a,b) if rec is not None)
    scalar_sections = [section for section,record in sections.items() if record["scalar_gate_edits"]]
    removed = dict(newly_removed=sorted(set(after["removed"])-set(before["removed"])),
                   restored_to_live=sorted(set(before["removed"])-set(after["removed"])))
    source = ("eight-source partner reassignment with lifted-target compensation and reused pre-life hostings"
              if before_name=="2679" else
              "twelve-source recovery: source-restoration gates, four additional helper removals, lifted-target residual compensation and reused pre-life hostings")
    return dict(before=before_name,after=after_name,status="EXPLORATORY",
        obligation="validation needed: explicit sequence of registered productions, intermediate words and consumed/created guards",
        source_data_available=True, source_recipe=source,
        sections=sections,mapping_changes=mappings,removed_role_changes=removed,
        warp_changes=warps,touched_registers=sorted(touched),
        initial_corrections_changed=before["initial_corrections"]!=after["initial_corrections"],
        prelude_events_before=before["prelude_events"],prelude_events_after=after["prelude_events"],
        single_production_obstructions={
            "frame_refit":dict(scalar_gate_sections_changed=scalar_sections,
                               explanation="A refit preserves scalar gates and only changes frames at fixed endpoints."),
            "retired_lender_alias_or_hostee_move":dict(
                unrelated_sections_changed=[s for s in scalar_sections if s not in ("B","cleanup")],
                explanation="The implemented guarded B-stage alias/hostee productions preserve A/precondition/compensation/cut/restore; these early compound rewrites also change source restoration and lifted-target compensation."),
            "helper_deletion":dict(newly_removed=removed["newly_removed"],
                explanation="An endpoint kernel identity does not isolate a per-helper deletion or provide its intermediate word and guard. Compound decomposition is still unknown.")},
        conclusion="No impossibility of a compound derivation is claimed. Calling the entire kernel rewrite a helper deletion would not supply the registered bounded production evidence.")


def audit(seed, n_permutations=2000):
    if n_permutations < 2000:
        raise ValueError("L-7 requires at least 2000 register controls")
    au = _load_tool("styles_r11_pr2679_auditor", "vendor/audit_local_pr2679.py", AUDITOR_SHA)
    wp = _load_tool("styles_r11_pr2679_patches", "vendor/word_patch_pr2679.py", PATCH_SHA)
    rng = random.Random(seed)
    variants = []
    for tag in ("base", "extra"):
        initial = G.read_json(G.resolve_word("2751", tag)[0])
        expected = G.read_json(G.resolve_word("2802", tag)[0])
        endpoint_audits = {name: _audit(au, G.read_json(G.resolve_word(name, tag)[0]), f"{tag}-endpoint-{name}")
                           for name in G.LINEAGE}
        early_words = {name:G.read_json(G.resolve_word(name,tag)[0]) for name in ("2679","2745","2751")}
        early_obligations = [_early_obligation(wp,early_words[a],early_words[b],a,b)
                             for a,b in (("2679","2745"),("2745","2751"))]
        refit2766 = G.read_json(G.resolve_word("2766", tag)[0])
        direct_patch = {"frames": [[section, i, b[-1]] for section in ("A", "B", "restore")
                                   for i, (a, b) in enumerate(zip(initial[section], refit2766[section])) if a != b],
                        "local_profile": refit2766["report"]["local_profile"]}
        direct_guards = _guards(au, wp, initial, refit2766, "refit2766", direct_patch)
        stage_data = {stage: G.read_json(G.PKG / f"inputs/{stage}_43{tag}.json") for stage in STAGES}
        states = [initial]
        rows = []
        for stage in STAGES:
            before = states[-1]
            after = _apply(wp, before, stage, stage_data[stage])
            guards = _guards(au, wp, before, after, stage, stage_data[stage])
            report = _audit(au, after, f"{tag}-{stage}")
            before_c, after_c = _canonical(before, stage + "-before"), _canonical(after, stage + "-after")
            registers, local = G.register_ledger(before_c, after_c)
            rows.append(dict(stage=stage, production="frame_refit" if stage.startswith("refit") else
                "retired_lender_alias" if stage.startswith("alias") else "hostee_move",
                guards=guards, all_guards_pass=all(guards.values()), auditor=report,
                registers=registers, local_delta_per_call=local,
                patch_sha256=hashlib.sha256((G.PKG / f"inputs/{stage}_43{tag}.json").read_bytes()).hexdigest(),
                source_credit=stage_data[stage].get("credit")))
            states.append(after)
        swaps = []
        # These are actual word-state permutations, rather than merely sums of
        # commuting profile deltas. Both the first and second swapped states
        # face the pinned auditor, including the first invalid prefix.
        for i in range(len(STAGES) - 1):
            left, right = STAGES[i:i+2]
            before = states[i]
            first = _apply(wp, before, right, stage_data[right])
            first, canonical_failure = _fresh_profile(first)
            first_audit = _audit(au, first, f"{tag}-swap-{right}-first")
            second = _apply(wp, first, left, stage_data[left])
            second, second_failure = _fresh_profile(second)
            second_audit = _audit(au, second, f"{tag}-swap-{right}-{left}")
            swaps.append(dict(original=[left, right], swapped=[right, left],
                first_audit=first_audit, second_audit=second_audit,
                first_canonical_failure=canonical_failure, second_canonical_failure=second_failure,
                same_state_after_two=second == states[i + 2],
                noncommuting_witness=first_audit["status"] == "REJECT" or second_audit["status"] == "REJECT"
                                    or second != states[i + 2]))
        a, b = _canonical(initial, "2751"), _canonical(expected, "2802")
        getstrings = lambda c: {r: tuple(j["rank"] for j in c.climbs.get(r, {}).get("jumps", [])) for r in range(c.n)}
        sa, sb = getstrings(a), getstrings(b)
        helper_ids = list(range(2 * a.v, a.n))
        accepted = 0
        changed_counts = []
        for _ in range(n_permutations):
            shuffled = helper_ids[:]
            rng.shuffle(shuffled)
            renamed = {**sb, **{dst: sb[src] for dst, src in zip(helper_ids, shuffled)}}
            accepted += renamed == sb
            changed_counts.append(sum(sa[r] != renamed[r] for r in sa))
        permutation = helper_ids[:]
        rng.shuffle(permutation)
        ren = dict(zip(helper_ids, permutation))
        coherent_ok = all((sa[r] != sb[r]) == ({ren.get(k, k): v for k, v in sa.items()}[ren.get(r, r)] !=
            {ren.get(k, k): v for k, v in sb.items()}[ren.get(r, r)]) for r in sa)
        variants.append(dict(variant=tag, stages=rows, exact_final_payload_match=states[-1] == expected,
            endpoint_audits=endpoint_audits,
            early_transition_obligations=early_obligations,
            refit2751_to_2766=dict(frames=direct_patch["frames"],guards=direct_guards,
                exact_payload_rebuild=_refit(initial,direct_patch)==refit2766,
                auditor=endpoint_audits["2766"],
                inverse_scope="inverse refit returns to separately audited #2751; followed by refit5, alias5, refit5c to #retired5"),
            intermediate_retired5_payload_match=states[3] == G.read_json(G.resolve_word("retired5", tag)[0]),
            adjacent_order_audits=swaps,
            register_control={"protocol": "independent destination-helper relabelling against fixed source-pinned production sequence",
                "scope": "rejects that named sequence, not every possible derivation", "n": n_permutations,
                "matched_pinned_effect": accepted, "empirical_p": (1 + accepted) / (1 + n_permutations),
                "changed_register_count": G._summary(changed_counts), "coherent_relabelling_preserves_effect": coherent_ok}))
    known_pass = all(v["exact_final_payload_match"] and v["intermediate_retired5_payload_match"] and
                     all(s["all_guards_pass"] and s["auditor"]["status"] == "PASS" for s in v["stages"]) for v in variants)
    return dict(status="EXPLORATORY", all_lineage_guards_proven=False, recorded_stage_guards_pass=known_pass,
        auditor_sha256=AUDITOR_SHA, patch_tool_sha256=PATCH_SHA, variants=variants,
        unresolved=["2679 -> 2745: held source pins identify changed alias8/prelife/refit563/alias1 stages and fill, but source-partner reassignment has not been decomposed into the registered move alphabet",
                    "2745 -> 2751: source joint_engine explains twelve-source recovery, but no validated decomposition into the registered move alphabet"],
        validation_not_missing_data=True,
        scope="Actual auditor verifies pinned feasible stages and swapped intermediate states; early endpoint identities and exact touched gate lists do not certify a decomposition into the registered move alphabet.")
