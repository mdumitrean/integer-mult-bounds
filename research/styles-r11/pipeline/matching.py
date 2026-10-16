"""Exact frame-bound census and Hall certificates for the frozen word set.

The BORROW census is adapted from J-dim1/code/census_r10.py (PR #2745,
Jeremy Kothe; PR #2679 auditor lineage).  Matching is classical bipartite
matching.  A certificate concerns the pinned frame lattice and does not price
simultaneous refits or establish a multiplication exponent.
"""
from __future__ import annotations

from collections import Counter, defaultdict, deque
from functools import lru_cache
from pathlib import Path
import gzip
import json
import random
import statistics
import sys


def _wordio():
    if str(Path(__file__).parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).parent))
    import wordio
    return wordio


@lru_cache(maxsize=None)
def get_bounds(path):
    """Parent-cache a pinned BORROW Bounds object; never import data as code."""
    _, boundmod, _ = _wordio().borrow_modules()
    return boundmod.Bounds(str(Path(path).resolve()))


def census(path, bounds=None):
    """Exact per-word census; FULL uses the toolkit graph and no warp segments."""
    path = Path(path)
    if bounds is None:
        with gzip.open(path, "rt") as f:
            raw = json.load(f)
    else:
        raw = bounds.Wd.w
    if "warps" not in raw:
        return _full_census(path, raw)
    b = bounds if bounds is not None else get_bounds(str(path.resolve()))
    Wd, ev = b.Wd, b.ev
    w, v = Wd.w, Wd.v
    restored = {int(q) for q in w.get("helper_final", {})}
    lenders_now = {rec[1] for rec in w["warps"]}
    touch = defaultdict(list)
    for t, (sec, e) in enumerate(ev):
        for q in e[1:2] if e[0] == "warp" else e[1:3] if e[0] == "add" else e[1:2]:
            touch[q].append((t, sec))
    wt = {e[2]: t for t, (sec, e) in enumerate(ev) if sec == "Bwarp"}
    helpers = {}
    for h in Wd.helpers:
        ts = touch.get(h, [])
        status = None
        if h in restored:
            status = "restored-cold"
        elif any(sec not in ("B", "restore", "Bwarp") for _, sec in ts):
            status = "touched-before-B"
        elif h in lenders_now:
            status = "already-a-lender"
        gs = [t for t, sec in ts if sec in ("B", "restore")]
        if status is None and not gs:
            status = "untouched"
        rec = dict(width=len(Wd.end[h]) - len(Wd.start[h]), S=len(Wd.start[h]),
                   status=status or "follower", last=ts[-1][0] if ts else -1)
        if gs:
            rec.update(first=gs[0], F1=len(Wd.gateframe[gs[0]]),
                       hi=len(b.hi[gs[0]]), lo1=len(b.lo[gs[0]]))
        helpers[h] = rec
    lend = {}
    for r in Wd.live:
        if v <= r < 2 * v or r in restored:
            continue
        ts = touch.get(r, [])
        if any(sec == "restore" for _, sec in ts):
            continue
        lastf = b.byreg.get(r, [])
        if lastf and lastf[-1][1] == "warp":
            upper = floor = len(lastf[-1][3]); kind = "warpE"
        elif lastf:
            g = lastf[-1][0]
            upper, floor, kind = len(Wd.gateframe[g]), len(b.lo[g]), "gate"
        else:
            upper = floor = len(Wd.start[r]); kind = "start"
        lend[r] = dict(last=ts[-1][0] if ts else -1, U=upper, lo=floor,
                       kind=kind, src=r < v, hosts=r in lenders_now)
    segments = []
    for op, rec in enumerate(w["warps"], 1):
        if op not in wt:
            continue
        t0, r = wt[op], rec[1]
        own = [t for t, _ in touch[r] if t < t0]
        after = [t for t, sec in touch[r] if t > t0 and sec in ("B", "restore")]
        if not after:
            raise ValueError(("hosted segment has no gate", op, r))
        own_floor = len(b.lo[own[-1]]) if own and own[-1] in b.lo else len(Wd.start[r])
        segments.append(dict(op=op, lender=r, warp_time=t0, U=len(rec[3]),
                             own_last=own[-1] if own else -1, own_lo=own_floor,
                             hosted_first=after[0], hosted_F1=len(Wd.gateframe[after[0]]),
                             hosted_hi=len(b.hi[after[0]]), hosted_last=touch[r][-1][0]))
    return _complete_census(path, "BORROW-WORD", helpers, lend, segments,
                            dict(feasible=not b.infeasible, literal_inside_bounds=not b.ctrl_bad,
                                 static_bad=b.stat_bad, mutable_gates=len(b.lo),
                                 slack_hist=dict(Counter(len(b.hi[t]) - len(b.lo[t]) for t in b.lo))))


def _full_census(path, raw):
    F, W = _wordio().toolkit()
    g = F.Graph(W.inline(raw, True), check_literal=True, cut_equality=True)
    v, n = raw["report"]["v"], g.N
    restored = {int(q) for q in raw.get("helper_final", {})}
    helpers, lend = {}, {}
    for r, chain in enumerate(g.chains):
        touches = [k for k in chain if g.nodes[k][2] in ("A", "B", "tail")]
        bg = [k for k in touches if g.nodes[k][2] == "B"]
        start, end = g.nodes[chain[0]][1], g.nodes[chain[-1]][1]
        if r >= 2 * v:
            status = ("restored-cold" if r in restored else "touched-before-B"
                      if any(g.nodes[k][2] == "A" for k in touches) else "untouched"
                      if not bg else "follower")
            rec = dict(width=len(end) - len(start), S=len(start), status=status,
                       last=touches[-1] if touches else -1)
            if bg:
                k = bg[0]
                rec.update(first=k, F1=len(g.nodes[k][1]), hi=len(g.upper[k]), lo1=len(g.lower[k]))
            helpers[r] = rec
        if v <= r < 2 * v or r in restored or any(g.nodes[k][2] == "tail" for k in touches):
            continue
        k = touches[-1] if touches else chain[0]
        lend[r] = dict(last=touches[-1] if touches else -1, U=len(g.nodes[k][1]),
                       lo=len(g.lower[k]), kind="gate" if touches else "start", src=r < v, hosts=False)
    return _complete_census(path, "FULL-WORD", helpers, lend, [],
                            dict(feasible=True, literal_inside_bounds=True, static_bad=[],
                                 mutable_gates=len(g.mutable),
                                 slack_hist=dict(Counter(len(g.upper[t]) - len(g.lower[t]) for t in g.mutable)),
                                 scope="Exact FULL frame graph; alias edges are necessary dimension/time guards only, no FULL alias constructor certified."))


def _complete_census(path, family, helpers, lend, segments, bounds_summary):
    fol = {h: r for h, r in helpers.items() if r["status"] == "follower"}
    pairs = [(h, r, "fixed" if l["U"] <= f["F1"] else "refit")
             for h, f in fol.items() for r, l in lend.items()
             if r != h and l["last"] < f["first"] and l["lo"] <= f["hi"]]
    chain = [(j, i) for i, fi in fol.items() if i in lend for j, fj in fol.items()
             if i != j and lend[i]["last"] < fj["first"] and lend[i]["lo"] <= fj["hi"]]
    return dict(word=str(path), family=family, helpers=helpers, lend=lend, segments=segments,
                pairs=pairs, chain_edges=chain, bounds=bounds_summary,
                helper_status=dict(Counter(r["status"] for r in helpers.values())))


def graph_data(c):
    helpers = {int(k): v for k, v in c["helpers"].items()}
    lend = {int(k): v for k, v in c["lend"].items()}
    lives = {f"follower:{h}": dict(first=d["first"], hi=d["hi"], width=d["width"], register=h)
             for h, d in helpers.items() if d["status"] == "follower"}
    seg_by_lender = {}
    for s in c["segments"]:
        lives[f"hosted:{s['op']}"] = dict(first=s["hosted_first"], hi=s["hosted_hi"],
                                         width=None, lender=s["lender"], register=None)
        seg_by_lender[s["lender"]] = s
    slots = {}
    for r, d in lend.items():
        s = seg_by_lender.get(r) if d.get("hosts") else None
        if s is not None:
            slots[f"segment:{r}"] = dict(last=s["own_last"], lo=s["own_lo"],
                                          occupied_by=f"hosted:{s['op']}", register=r)
        elif not d.get("hosts"):
            slots[f"free:{r}"] = dict(last=d["last"], lo=d["lo"], occupied_by=None, register=r)
    for s in c["segments"]:
        slots.setdefault(f"segment:{s['lender']}", dict(last=s["own_last"], lo=s["own_lo"],
                         occupied_by=f"hosted:{s['op']}", register=s["lender"]))
    return lives, slots


def adjacency(lives, slots, frame=True):
    return {l: [s for s, sd in slots.items() if sd["last"] < ld["first"]
                and sd["register"] != ld.get("register") and (not frame or sd["lo"] <= ld["hi"])]
            for l, ld in lives.items()}


def maximum_matching(adj):
    ml, ms = {}, {}
    def augment(l, seen):
        for s in adj[l]:
            if s in seen:
                continue
            seen.add(s)
            if s not in ms or augment(ms[s], seen):
                ml[l], ms[s] = s, l
                return True
        return False
    for l in adj:
        augment(l, set())
    return ml, ms


def certificate(adj, ml, ms):
    left = set(adj) - set(ml)
    queue, right = list(left), set()
    while queue:
        l = queue.pop()
        for s in adj[l]:
            if s in right:
                continue
            right.add(s)
            other = ms.get(s)
            if other is not None and other not in left:
                left.add(other); queue.append(other)
    cover_left = set(adj) - left
    assert len(left) - len(right) == len(adj) - len(ml)
    assert len(cover_left) + len(right) == len(ml)
    assert all(l in cover_left or s in right for l, ss in adj.items() for s in ss)
    return dict(hall_lives=sorted(left), hall_neighbours=sorted(right),
                deficiency=len(left)-len(right), vertex_cover_lives=sorted(cover_left),
                vertex_cover_slots=sorted(right), matching=sorted(ml.items()),
                verified_hall_and_koenig=True)


def augmenting_paths(adj, slots):
    """One shortest path per currently unhosted life, relative to shipped aliases."""
    ms = {s: d["occupied_by"] for s, d in slots.items() if d["occupied_by"] is not None}
    ml = {l: s for s, l in ms.items()}
    out = {}
    for root in set(adj) - set(ml):
        q = deque([(root, [root])]); seen_l, seen_s = {root}, set()
        while q:
            l, path = q.popleft()
            found = False
            for s in adj[l]:
                if s in seen_s:
                    continue
                seen_s.add(s)
                if s not in ms:
                    out[root] = path + [s]; found = True; break
                other = ms[s]
                if other not in seen_l:
                    seen_l.add(other); q.append((other, path + [s, other]))
            if found:
                break
    return out


def atlas(c, seed, n_permutations=2000):
    """Certificates and histogram-preserving floor/time permutations."""
    lives, slots = graph_data(c)
    adj = adjacency(lives, slots)
    ml, ms = maximum_matching(adj)
    cert = certificate(adj, ml, ms)
    occupied = [(s, d["occupied_by"]) for s, d in slots.items() if d["occupied_by"] is not None]
    realised_ok = all(l in adj and s in adj[l] for s, l in occupied)
    paths = augmenting_paths(adj, slots)
    rng = random.Random(seed)
    lk, sk = list(lives), list(slots)
    floors, times = [slots[s]["lo"] for s in sk], [lives[l]["first"] for l in lk]
    null = []
    # Null statistic: number unhostable; exact certificate is not a p-value claim.
    for _ in range(n_permutations):
        rng.shuffle(floors); rng.shuffle(times)
        nadj = {l: [s for j, s in enumerate(sk)
                    if slots[s]["last"] < times[i] and floors[j] <= lives[l]["hi"]
                    and slots[s]["register"] != lives[l].get("register")]
                for i, l in enumerate(lk)}
        nml, _ = maximum_matching(nadj)
        null.append(len(lives) - len(nml))
    value = cert["deficiency"]
    ordered = sorted(null)
    ns = dict(n=n_permutations, mean=statistics.fmean(null) if null else None,
              sd=statistics.pstdev(null) if null else None,
              empirical_p=(1+sum(x >= value for x in null))/(1+len(null)),
              empirical_lower_p=(1+sum(x <= value for x in null))/(1+len(null)),
              central_99_interval=[ordered[int(.005*(len(ordered)-1))], ordered[int(.995*(len(ordered)-1))]] if null else None)
    near = {l: [s for s, d in slots.items() if d["last"] < lives[l]["first"]
                 and d["lo"]-lives[l]["hi"] == 1 and d["register"] != lives[l].get("register")]
            for l in lives}
    tm, _ = maximum_matching(adjacency(lives, slots, frame=False))
    return dict(word=c["word"], family=c["family"], n_lives=len(lives), n_slots=len(slots),
                lives=lives, slots=slots, bounds=c["bounds"], max_matching=len(ml),
                time_only_max_matching=len(tm), current_aliases=len(occupied),source_alias_segments=len(c["segments"]),
                current_alias_edges_verified=realised_ok, certificate=cert,
                augmenting_paths=paths, statement="explicit augmenting path" if paths else "no augmenting path",
                near_miss_floor_gap_one=near, degree_hist=dict(Counter(map(len, adj.values()))),
                null_summary=ns, seed=seed, n_permutations=n_permutations,
                exact_certificate_pass=realised_ok and cert["verified_hall_and_koenig"],
                scope="Pinned individual floor/time compatibility; simultaneous edge refit pricing remains a census target.")


_CENSUSES=[]


def prepare(paths):
    """Parent-load and construct every exact census before forking workers."""
    global _CENSUSES
    _CENSUSES=[census(path) for path in paths]
    return [dict(index=i,word=c["word"],family=c["family"]) for i,c in enumerate(_CENSUSES)]


def task(arg):
    """pool.py worker: {index,seed,n_permutations=2000}."""
    value=atlas(_CENSUSES[arg["index"]],arg["seed"],arg.get("n_permutations",2000))
    # The exact atlas is a certificate. Universal realised-move replay requires
    # the separate lineage witnesses; current alias-edge parity is insufficient.
    return dict(status="EXPLORATORY",statistics=value,n_permutations=value["n_permutations"],
                null_summary=value["null_summary"],decision="Exact matching/Hall certificate verified; realised lineage move replay is evaluated by the coordinator.")


def lineage_witnesses():
    """Verify every seven-stage new alias and both recorded augmenting paths.

    Approved pinned patch code builds in-memory word states.  Bounds reads them
    through a gzip BytesIO stream; no stage data is imported or executed.  The
    complete local auditor/production checks are independently provided by L-7.
    """
    import io
    import growth_replay as replay
    import growth as growth
    _, boundmod, _ = _wordio().borrow_modules()
    out=[]
    for tag in ("base","extra"):
        states=replay.build_stages(tag)
        byname=dict(states)
        censuses={}
        for label in ("refit5","refit7","hostmove2"):
            raw=byname[label]
            data=gzip.compress(json.dumps(raw,separators=(",",":")).encode(),mtime=0)
            b=boundmod.Bounds(io.BytesIO(data))
            censuses[label]=census(f"derived:{tag}:{label}",bounds=b)
        cases=[]
        for prior,stage in (("refit5","alias5"),("hostmove2","alias7")):
            lives,slots=graph_data(censuses[prior]);adj=adjacency(lives,slots)
            patch=growth.read_json(growth.PKG/f"inputs/{stage}_43{tag}.json")
            for a in patch["aliases"]:
                l=f"follower:{a['h']}";s=f"free:{a['L']}"
                ok=l in adj and s in adj[l]
                cases.append(dict(stage=stage,life=l,slot=s,edge_verified=ok,
                                  floor=slots.get(s,{}).get("lo"),ceiling=lives.get(l,{}).get("hi"),
                                  last=slots.get(s,{}).get("last"),first=lives.get(l,{}).get("first")))
        lives,slots=graph_data(censuses["refit7"]);adj=adjacency(lives,slots)
        moves=growth.read_json(growth.PKG/f"inputs/hostmove2_43{tag}.json")["moves"]
        aliases=growth.read_json(growth.PKG/f"inputs/alias7_43{tag}.json")["aliases"]
        paths=[]
        for move in moves:
            old=move["old_record"];op=byname["refit7"]["warps"].index(old)+1
            alias=next(a for a in aliases if a["L"]==old[1])
            path=[f"follower:{alias['h']}",f"segment:{old[1]}",f"hosted:{op}",f"free:{move['L_new']}"]
            ok=path[1] in adj.get(path[0],[]) and slots[path[1]]["occupied_by"]==path[2] and path[3] in adj.get(path[2],[])
            paths.append(dict(path=path,verified=ok,first_edge_gap=slots[path[1]]["lo"]-lives[path[0]]["hi"],
                              second_edge_gap=slots[path[3]]["lo"]-lives[path[2]]["hi"]))
        out.append(dict(variant=tag,aliases=cases,augmenting_paths=paths,
                        all_verified=all(x["edge_verified"] for x in cases) and all(x["verified"] for x in paths)))
    earlier=[]
    for tag in ("base","extra"):
        for before,after in (("2679","2745"),("2745","2751")):
            a=growth.read_json(growth.resolve_word(before,tag)[0])
            b=growth.read_json(growth.resolve_word(after,tag)[0])
            same=a["warps"]==b["warps"] and a["removed"]==b["removed"]
            earlier.append(dict(variant=tag,before=before,after=after,alias_records_unchanged=same,
                before_warps=len(a["warps"]),after_warps=len(b["warps"]),
                removed_helpers_added=sorted(set(b["removed"])-set(a["removed"])),
                scope="Changed warp/removed payloads require their own matching transition witnesses; current endpoint aliases alone do not prove that transition."))
    return dict(variants=out,all_verified=all(x["all_verified"] for x in out),earlier_transitions=earlier,
                scope="All new aliases and hostee moves of the pinned #2751→#2802 seven-stage replay; earlier held lineage alias differences need independent provenance.")


def lineage_task(arg):
    value=lineage_witnesses()
    value["seed"]=arg["seed"]
    return value


def _unwrap_pool(output):
    if output.get("status") == "OK":
        return output.get("result"), None
    if output.get("status") in ("ERROR", "TIMEOUT"):
        return None, output["status"]
    return output, None


def _verify_atlas_payload(value):
    """Recheck a serialized matching/cover certificate without trusting flags."""
    errors=[]
    lives,slots=value["lives"],value["slots"]
    adj=adjacency(lives,slots)
    cert=value["certificate"]
    matching=dict(cert["matching"])
    hall=set(cert["hall_lives"]);neighbours=set(cert["hall_neighbours"])
    actual_neighbours={s for l in hall for s in adj.get(l,[])}
    cover_l=set(cert["vertex_cover_lives"]);cover_s=set(cert["vertex_cover_slots"])
    if not hall<=set(lives) or neighbours!=actual_neighbours:
        errors.append("Hall set/neighbourhood mismatch")
    if len(set(matching.values()))!=len(matching) or any(s not in adj.get(l,[]) for l,s in matching.items()):
        errors.append("matching is not a one-to-one edge subset")
    if cover_l!=set(lives)-hall or cover_s!=neighbours:
        errors.append("Koenig cover/alternating sets differ")
    if any(l not in cover_l and s not in cover_s for l,ss in adj.items() for s in ss):
        errors.append("vertex cover misses an edge")
    if len(cover_l)+len(cover_s)!=len(matching):
        errors.append("matching and cover sizes differ")
    if cert["deficiency"]!=len(lives)-len(matching) or cert["deficiency"]!=len(hall)-len(neighbours):
        errors.append("Hall deficiency equality fails")
    occupied={s:d["occupied_by"] for s,d in slots.items() if d["occupied_by"] is not None}
    alias_ok=(len(set(occupied.values()))==len(occupied) and len(occupied)==value.get("source_alias_segments",len(occupied))
              and all(s in adj.get(l,[]) for s,l in occupied.items()))
    paths=value["augmenting_paths"]
    for origin,path in paths.items():
        if not path or path[0]!=origin or len(path)%2!=0 or path[-1] in occupied:
            errors.append("augmenting path endpoint/shape invalid");continue
        if any(path[j+1] not in adj.get(path[j],[]) for j in range(0,len(path),2)):
            errors.append("augmenting path contains a non-edge")
        if any(occupied.get(path[j])!=path[j+1] for j in range(1,len(path)-1,2)):
            errors.append("augmenting path fails matched alternation")
    if bool(paths)!=(len(matching)>len(occupied)):
        errors.append("current matching/no-augmenting-path claim inconsistent with maximum matching")
    if value.get("statement")!=("explicit augmenting path" if paths else "no augmenting path"):
        errors.append("per-word statement does not match path evidence")
    bounds=value.get("bounds",{})
    if not bounds.get("feasible") or not bounds.get("literal_inside_bounds") or bounds.get("static_bad"):
        errors.append("exact frame-bound prerequisites do not pass")
    return dict(word=value["word"],family=value["family"],certificate_verified=not errors,
                alias_edges_verified=alias_ok,errors=errors,
                current_aliases=len(occupied),maximum_matching=len(matching),
                statement=value.get("statement"),n_null=value.get("null_summary",{}).get("n",0))


def summarize_s1(atlas_outputs,lineage_output,l7_payload,seed,expected_words=None):
    """Conservative per-seed S-1 aggregation; call R.confirm on both summaries.

    atlas_outputs are the pool envelopes for one seed. lineage_output is that
    seed's lineage_task envelope. l7_payload is the bare growth.task L-7 result
    (the RESULT.json path is statistics.tasks[i].result). No global L-7 PASS is
    assumed: the relevant staged auditor/guard receipts are inspected directly.
    """
    technical=[];checks=[];missing=[]
    expected_words=list(expected_words) if expected_words is not None else [c["word"] for c in _CENSUSES]
    for output in atlas_outputs:
        payload,error=_unwrap_pool(output)
        if error:
            technical.append(error);continue
        value=payload.get("statistics",payload)
        if value.get("seed")!=seed:
            technical.append("ERROR");missing.append("atlas seed differs from requested seed");continue
        try:
            checks.append(_verify_atlas_payload(value))
        except (KeyError,TypeError,ValueError) as exc:
            technical.append("ERROR");missing.append("malformed atlas certificate: "+str(exc))
    observed=[c["word"] for c in checks]
    if len(observed)!=len(set(observed)):
        technical.append("ERROR");missing.append("duplicate atlas words")
    if expected_words and set(observed)!=set(expected_words):
        missing.append("not every registered word has an atlas certificate")
    if any(c["n_null"]!=2000 for c in checks):
        technical.append("TIMEOUT");missing.append("registered 2000 floor/time controls incomplete")
    if any(not c["certificate_verified"] for c in checks):
        technical.append("ERROR")
    lineage,error=_unwrap_pool(lineage_output)
    if error:
        technical.append(error);lineage={}
    lineage=lineage or {}
    if lineage.get("seed")!=seed:
        missing.append("lineage witness missing or seed mismatch")
    variants={v.get("variant"):v for v in lineage.get("variants",[])}
    if set(variants)!={"base","extra"}:
        missing.append("both lineage variants required")
    witness_complete=bool(variants) and all(len(v.get("aliases",[]))==7 and len(v.get("augmenting_paths",[]))==2
                                           for v in variants.values())
    if not witness_complete:
        missing.append("seven alias and two hostee-path witnesses required per variant")
    witness_ok=witness_complete and all(v.get("all_verified",False) for v in variants.values())
    replay=(l7_payload or {}).get("guarded_replay",{})
    replay_variants={v.get("variant"):v for v in replay.get("variants",[])}
    required_stages={"refit5","alias5","refit5c","refit7","hostmove2","alias7","refit7c"}
    stage_audits=True
    if set(replay_variants)!={"base","extra"}:
        stage_audits=False;missing.append("L-7 recorded guard/auditor variants missing")
    for tag,v in replay_variants.items():
        stages={s.get("stage"):s for s in v.get("stages",[])}
        ok=set(stages)==required_stages and v.get("exact_final_payload_match",False) and v.get("intermediate_retired5_payload_match",False)
        ok=ok and all(s.get("all_guards_pass",False) and s.get("auditor",{}).get("status")=="PASS"
                     and s.get("guards") and all(s["guards"].values()) for s in stages.values())
        refit=v.get("refit2751_to_2766",{})
        ok=ok and refit.get("exact_payload_rebuild",False) and refit.get("auditor",{}).get("status")=="PASS" and bool(refit.get("guards")) and all(refit.get("guards",{}).values())
        ok=ok and all(a.get("status")=="PASS" for a in v.get("endpoint_audits",{}).values()) and len(v.get("endpoint_audits",{}))==6
        if not ok:
            stage_audits=False;missing.append("L-7 relevant feasible-stage evidence incomplete: "+str(tag))
    prior=lineage.get("earlier_transitions",[])
    earlier_complete=len(prior)==4 and all(x.get("alias_records_unchanged",False) for x in prior)
    if not earlier_complete:
        missing.append("earlier held alias/hostee changes are not covered by the staged #2751-to-#2802 replay")
    if "ERROR" in technical:
        status="ERROR";decision="A technical or exact-certificate consistency check failed."
    elif "TIMEOUT" in technical:
        status="TIMEOUT";decision="A registered atlas/control/witness task did not complete."
    elif any(not c["alias_edges_verified"] for c in checks) or (witness_complete and not witness_ok and stage_audits):
        status="NULL";decision="An auditor-valid observed alias/hostee move fails the registered exact compatibility model."
    elif missing or not stage_audits or not witness_ok:
        status="EXPLORATORY";decision="Atlas certificates available, but universal realised-lineage proof obligations remain."
    else:
        status="PASS";decision="Every registered atlas certificate and observed alias/hostee transition is verified for this seed; confirmation requires the other seed."
    return dict(status=status,seed=seed,n_permutations=2000,decision=decision,
                word_checks=checks,lineage_witnesses_verified=witness_ok,
                relevant_l7_guard_audits_verified=stage_audits,earlier_alias_transition_coverage=earlier_complete,
                unresolved=missing,technical_statuses=technical,
                scope="Exact matching/alias certificate only; five-criterion pattern status is not inferred.",
                confirmation_required=True)
