"""Finite guarded-order follow-up to the preserved M0 L7 patch-order audit.

The held JSON stages are data.  Their whole-section replacements are used only
to identify the pinned source states and local edits during parent preparation.
Experimental transitions below touch only declared frames, named helper/lender
uses, named warp records and their derived cleanup/report.  Every operation
checks its predicates on the actual current state before committing a successor.
Only the approved source-pinned PR2679 auditor/patch helpers are imported.
"""
from __future__ import annotations

import copy
import hashlib
import random

import growth as G
import growth_replay as R

_PREPARED = None


def _frame_actions(before, after, sections=("A","B","restore")):
    actions=[]
    for section in sections:
        if len(before[section])!=len(after[section]):
            raise ValueError("local production unexpectedly changes gate count")
        for index,(old,new) in enumerate(zip(before[section],after[section])):
            if old[:-1]!=new[:-1]:
                raise ValueError("unexplained scalar edit while extracting frame actions")
            if old[-1]!=new[-1]:
                actions.append(dict(section=section,index=index,anchor=copy.deepcopy(old[:-1]),frame=copy.deepcopy(new[-1])))
    return actions


def _rename_b(word, old, new, position):
    for gate in word["B"][position:]:
        for column in (1,2) if gate[0]=="add" else (1,):
            if gate[column]==old:
                gate[column]=new


def prepare():
    """Parent-only source loading and local-edit extraction; no audit/run here."""
    global _PREPARED
    _PREPARED={}
    for tag in ("base","extra"):
        states=R.build_stages(tag)
        operations={}
        for index,stage in enumerate(R.STAGES):
            before,after=states[index][1],states[index+1][1]
            path=G.PKG/f"inputs/{stage}_43{tag}.json"
            patch=G.read_json(path)
            op=dict(stage=stage,source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    source_path=str(path.relative_to(G.ROOT)),credit=patch.get("credit"),frames=[])
            if stage.startswith("refit"):
                op["kind"]="frame_refit"
                for section,i,frame in patch["frames"]:
                    op["frames"].append(dict(section=section,index=i,anchor=copy.deepcopy(before[section][i][:-1]),
                                              frame=copy.deepcopy(frame)))
            elif stage.startswith("alias"):
                op.update(kind="retired_lender_alias",aliases=copy.deepcopy(patch["aliases"]))
            elif stage=="hostmove2":
                op.update(kind="hostee_move",moves=copy.deepcopy(patch["moves"]))
                renamed=copy.deepcopy(before)
                for move in op["moves"]:
                    _rename_b(renamed,move["L_old"],move["L_new"],move["old_pos"])
                op["frames"]=_frame_actions(renamed,after)
                # The hostmove frame target is identified by its scalar gate
                # BEFORE the local relabeling, not by an entire source state.
                for action in op["frames"]:
                    action["before_anchor"]=copy.deepcopy(before[action["section"]][action["index"]][:-1])
            else:
                raise ValueError(stage)
            operations[stage]=op
        _PREPARED[tag]=dict(states=states,operations=operations)
    return dict(variants=list(_PREPARED),stages=list(R.STAGES),
                source_preparation_only=True,large_words_loaded_in_parent=True)


def _last_b(word,register):
    return max((i for i,g in enumerate(word["B"]) if register in R._regs(g)),default=-1)


def _first_b(word,register,start=0):
    return min((i for i in range(start,len(word["B"])) if register in R._regs(word["B"][i])),default=-1)


def _transport_guard(au,record):
    try:
        au.check_G_frames(record["G"],record["U"],record["E"],9)
        return True,None
    except (AssertionError,RuntimeError,ValueError,KeyError,IndexError) as exc:
        return False,f"{type(exc).__name__}: {exc}"[:400]


def preconditions(au,word,operation):
    """Inspect real current bindings, times, frames and local gate anchors."""
    checks,details={},[]
    for action in operation["frames"]:
        section,index=action["section"],action["index"]
        key=f"frame:{section}:{index}"
        in_range=section in word and 0<=index<len(word[section])
        checks[key+":gate_exists"]=in_range
        checks[key+":named_scalar_gate"]=in_range and word[section][index][:-1]==action.get("before_anchor",action["anchor"])
    if operation["kind"]=="retired_lender_alias":
        registers=[r for a in operation["aliases"] for r in (a["h"],a["L"])]
        checks["disjoint_alias_registers"]=len(registers)==len(set(registers))
        for a in operation["aliases"]:
            h,lender,pos=a["h"],a["L"],a["pos"]
            prefix=f"{h}<-{lender}"
            first,last=_first_b(word,h),_last_b(word,lender)
            checks[prefix+":distinct_live_registers"]=h!=lender and h not in word["removed"] and lender not in word["removed"]
            checks[prefix+":private_follower"]=(str(h) in word["start_extra"] and str(h) not in word["helper_final"]
                and not any(h in R._regs(g) for s in ("precondition","compensation","A","cut","restore") for g in word[s]))
            checks[prefix+":follower_first_gate"]=first==pos
            checks[prefix+":retired_before_entry"]=last<pos
            checks[prefix+":free_lender"]=(not any(lender in R._regs(g) for g in word["restore"])
                and not any(rec[1]==lender and rec[0]>last for rec in word["warps"]))
            try:
                actual=R._frame_before(au,word,lender,pos)
                checks[prefix+":literal_U"]=actual==au.basis(a["U"])
                actual_dim=len(actual)
            except (AssertionError,RuntimeError,ValueError,KeyError,IndexError) as exc:
                checks[prefix+":literal_U"]=False
                actual_dim=None
                details.append(dict(guard=prefix+":literal_U",error=f"{type(exc).__name__}: {exc}"[:400]))
            checks[prefix+":equal_dimensions"]=len(au.basis(a["U"]))==len(au.basis(a["E"]))
            checks[prefix+":entrance_containment"]=(0<=pos<len(word["B"]) and
                au.contained(au.basis(a["E"]),au.basis(word["B"][pos][-1])))
            good,error=_transport_guard(au,a)
            checks[prefix+":invertible_G_maps_U_to_E"]=good
            details.append(dict(production=prefix,first_follower_B=first,last_lender_B=last,
                                declared_entry_B=pos,actual_lender_frame_dim=actual_dim,
                                required_U_dim=len(au.basis(a["U"])),required_E_dim=len(au.basis(a["E"])),
                                transport_error=error))
    elif operation["kind"]=="hostee_move":
        registers=[r for m in operation["moves"] for r in (m["L_old"],m["L_new"])]
        checks["disjoint_move_registers"]=len(registers)==len(set(registers))
        for m in operation["moves"]:
            old,new,pos,op=m["L_old"],m["L_new"],m["pos"],m["op"]
            prefix=f"{old}->{new}"
            current=word["warps"][op-1] if 0<op<=len(word["warps"]) else None
            checks[prefix+":consumed_warp_identity"]=current==m["old_record"]
            checks[prefix+":distinct_live_registers"]=old!=new and old not in word["removed"] and new not in word["removed"]
            checks[prefix+":first_hosted_gate"]=_first_b(word,old,m["old_pos"])==pos
            checks[prefix+":retired_before_entry"]=_last_b(word,new)<pos
            checks[prefix+":free_lender"]=(not any(new in R._regs(g) for g in word["restore"])
                and not any(rec[1]==new for rec in word["warps"]))
            checks[prefix+":old_lender_only_named_B_life"]=(not any(old in R._regs(g) for g in word["B"][:m["old_pos"]]+word["restore"])
                and not any(rec[1]==old for i,rec in enumerate(word["warps"],1) if i!=op))
            try:
                actual=R._frame_before(au,word,new,pos)
                checks[prefix+":literal_U"]=actual==au.basis(m["U"])
                actual_dim=len(actual)
            except (AssertionError,RuntimeError,ValueError,KeyError,IndexError) as exc:
                checks[prefix+":literal_U"]=False
                actual_dim=None
                details.append(dict(guard=prefix+":literal_U",error=f"{type(exc).__name__}: {exc}"[:400]))
            checks[prefix+":equal_dimensions"]=len(au.basis(m["U"]))==len(au.basis(m["E"]))
            good,error=_transport_guard(au,m)
            checks[prefix+":invertible_G_maps_U_to_E"]=good
            details.append(dict(production=prefix,operator_id=op,last_new_lender_B=_last_b(word,new),
                declared_entry_B=pos,actual_lender_frame_dim=actual_dim,
                required_U_dim=len(au.basis(m["U"])),required_E_dim=len(au.basis(m["E"])),transport_error=error))
    elif operation["kind"]!="frame_refit":
        raise ValueError(operation["kind"])
    return checks,details


def _propose(wp,word,operation):
    """Perform only the named local edits on a private candidate copy."""
    candidate=copy.deepcopy(word)
    if operation["kind"]=="retired_lender_alias":
        for a in operation["aliases"]:
            h,lender,pos=a["h"],a["L"],a["pos"]
            _rename_b(candidate,h,lender,pos)
            candidate["removed"].append(h)
            del candidate["start_extra"][str(h)]
            candidate["warps"].append([pos,lender,copy.deepcopy(a["G"]),copy.deepcopy(a["U"]),copy.deepcopy(a["E"])])
    elif operation["kind"]=="hostee_move":
        for m in operation["moves"]:
            _rename_b(candidate,m["L_old"],m["L_new"],m["old_pos"])
            candidate["warps"][m["op"]-1]=[m["pos"],m["L_new"],copy.deepcopy(m["G"]),copy.deepcopy(m["U"]),copy.deepcopy(m["E"])]
    for action in operation["frames"]:
        candidate[action["section"]][action["index"]][-1]=copy.deepcopy(action["frame"])
    if operation["kind"]!="frame_refit":
        forward=copy.deepcopy(candidate)
        forward["A"]=forward["A"][forward["prelude_events"]:]
        candidate["cleanup"]=wp.derive_cleanup(forward,wp.restored_of(word))
    return candidate


def transition(au,wp,word,operation,label):
    checks,details=preconditions(au,word,operation)
    record=dict(stage=operation["stage"],production=operation["kind"],guards=checks,guard_details=details,
                source_path=operation["source_path"],source_sha256=operation["source_sha256"],source_credit=operation["credit"],
                local_frame_targets=operation["frames"],full_section_overwrite=False)
    if not all(checks.values()):
        record.update(status="GUARD_REJECT",failed_guards=[k for k,v in checks.items() if not v],committed=False)
        return None,record
    candidate=_propose(wp,word,operation)
    candidate,failure=R._fresh_profile(candidate)
    record["guards"]["proposed_assignment_exact_frame_chains"]=failure is None
    if failure is not None:
        record.update(status="GUARD_REJECT",failed_guards=["proposed_assignment_exact_frame_chains"],
                      frame_guard_reason=failure,committed=False)
        return None,record
    # Canonical extraction checks the candidate's monotone chains, cuts and
    # literal warp source frames before any state transition is committed.
    # The independent free-algebra auditor is the final admission guard.
    audit=R._audit(au,candidate,label)
    record["auditor"]=audit
    if audit["status"]!="PASS":
        record.update(status="AUDITOR_REJECT",failed_guards=["independent_free_algebra_admission"],committed=False)
        return None,record
    before_c,after_c=R._canonical(word,label+"-before"),R._canonical(candidate,label+"-after")
    registers,change=G.register_ledger(before_c,after_c)
    record.update(status="PASS",failed_guards=[],committed=True,registers=registers,local_delta=change)
    return candidate,record


def _sequence(au,wp,initial,names,operations,label):
    current=copy.deepcopy(initial)
    records=[]
    for index,name in enumerate(names):
        successor,record=transition(au,wp,current,operations[name],f"{label}-{index}-{name}")
        records.append(record)
        if successor is None:
            return None,records
        current=successor
    return current,records


def audit(seed):
    if _PREPARED is None:
        raise RuntimeError("growth_order.prepare must load source words/operations in parent before launch")
    au=R._load_tool("styles_r11_guard_order_auditor","vendor/audit_local_pr2679.py",R.AUDITOR_SHA)
    wp=R._load_tool("styles_r11_guard_order_patches","vendor/word_patch_pr2679.py",R.PATCH_SHA)
    rng=random.Random(seed)
    variants=[]
    for tag,prepared in _PREPARED.items():
        states,operations=prepared["states"],prepared["operations"]
        current=copy.deepcopy(states[0][1]);original=[]
        for index,name in enumerate(R.STAGES):
            current,record=transition(au,wp,current,operations[name],f"{tag}-original-{name}")
            record["pinned_successor_payload_equal"]=current==states[index+1][1] if current is not None else False
            original.append(record)
            if current is None:
                break
        original_ok=len(original)==len(R.STAGES) and all(r["status"]=="PASS" and r["pinned_successor_payload_equal"] for r in original)
        indices=list(range(len(R.STAGES)-1));rng.shuffle(indices)
        pairs=[]
        for index in indices:
            left,right=R.STAGES[index:index+2]
            final,records=_sequence(au,wp,states[index][1],(right,left),operations,f"{tag}-swap-{right}-{left}")
            if final is None:
                category="inadmissible_swapped_named_sequence"
            elif final==states[index+2][1]:
                category="both_orders_admissible_and_same_payload"
            else:
                category="both_orders_admissible_but_different_payload"
            pairs.append(dict(original=[left,right],swapped=[right,left],prefixes=records,classification=category,
                first_rejected_prefix=next((i for i,r in enumerate(records) if not r["committed"]),None),
                unexecuted_suffix=[left] if len(records)==1 and final is None else [],
                same_payload_after_two=final==states[index+2][1] if final is not None else None,
                scope="finite named local operations at this pinned prefix; no claim about all productions in the class"))
        pairs.sort(key=lambda row:R.STAGES.index(row["original"][0]))
        variants.append(dict(variant=tag,original_order=original,original_local_rebuild_verified=original_ok,adjacent_pairs=pairs))
    good=all(v["original_local_rebuild_verified"] for v in variants)
    unexplained=[dict(variant=v["variant"],pair=p["original"],prefix=r["stage"])
        for v in variants for p in v["adjacent_pairs"] for r in p["prefixes"] if r["status"]=="AUDITOR_REJECT"]
    return dict(experiment="L7-GUARD-ORDER",seed=seed,n_permutations=0,
        status="PASS" if good and not unexplained else "EXPLORATORY",
        decision="all original named local productions reconstructed; each swapped sequence classified by actual prefix guards"
            if good and not unexplained else "a local reconstruction or omitted guard still needs validation",
        variants=variants,unexplained_auditor_rejections=unexplained,
        fixed_family="six adjacent pairs x two variants; second seed changes evaluation order only",
        no_global_kappa_comparison=True,early_lineage_obligations_unchanged=True,
        original_M0_receipt_preserved=True,source_attribution=G.sources(),
        scope="Named-operation admissibility/commutation audit. Invalid orders stop before commitment; whole-section patch inequality is not used as primitive evidence. Distinct admissible outcomes mean different derived words, not an order effect in a fixed sum of Parikh deltas.")


def task(spec):
    return audit(int(spec["seed"]))
