"""Literal owner-fill audits, conditional flow nulls and capacity certificates.

Window reconstruction and bit-mask checks are adapted from #2751/#2802's
independent_owners.py (Tekalign, Apache-2.0), retaining the exact (start,stop]
convention.  #1672 OWNERS is normalized as data and its inherited provider
profile is kept distinct from the held-word overlay.  Flow relaxations use
integer cells; they do not prove indivisible-width packing or moment bounds.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import gzip
import hashlib
import json
import math
import random
import statistics
import time


COLUMNS = ["time", "helper", "owner_replica", "child", "port", "offset"]


def _load(path):
    with gzip.open(path, "rt") if str(path).endswith(".gz") else open(path) as f:
        return json.load(f)


def _need(ok, label):
    if not ok:
        raise ValueError(label)


def windows(template, order):
    """(replica,child) -> (capacity,start,stop), with start < t <= stop."""
    ranks = {c["child"]: c["rank"] for c in template["idle_children"]}
    pairs = {e["stage"]: e["pair"] for e in template["recipe"] if e["kind"] == "local"}
    blocks, stage = {}, None
    for event in template["execution_schedule"]:
        if event["kind"] in ("bank_padding_cover_sweep", "translate_every_live_family"):
            continue
        if event["kind"] == "local_cover_sweep":
            stage = event["stage"]; blocks[stage] = []
        _need(stage is not None, "event before first call")
        blocks[stage].append(event)
    replicas = 1 + max(r for _, r in order)
    progression, last, result = [0] * replicas, {}, {}
    for t, (stage, replica) in enumerate(order):
        _need(0 <= replica < replicas and stage == progression[replica], "order chronology")
        progression[replica] += 1
        for j, event in enumerate(blocks[stage]):
            kind = event["kind"]
            if kind == "local_cover_sweep":
                _need(j == 0, "local call position")
                last[replica, pairs[stage]] = t
            elif kind == "bridge":
                last[replica, event["src"]] = last[replica, event["dst"]] = t
            elif kind == "idle_cover_sweep":
                _need(j > 0, "idle position")
                start = last.get((replica, event["pair"]), -1)
                for child in event["child_indices"]:
                    if child in ranks:
                        result[replica, child] = (ranks[child], start, t)
    _need(progression == [len(blocks)] * replicas, "complete replica progression")
    return result


@dataclass
class FillModel:
    name: str
    rows: list
    order: list
    widths: list
    local_profiles: list
    win: dict
    family: dict
    expected_profile: dict
    expected_mass: int
    sources: list
    attributions: list
    overlay_local_profiles: list | None = None
    source_notes: dict | None = None
    ports: int = 112

    @property
    def calls(self):
        return len(self.order)

    def family_id(self, o, c, p):
        return (o, self.family[c], p)

    @property
    def all_bins(self):
        return [(o, c, p) for o, c in self.win for p in range(self.ports)]


def _sources(paths):
    return [dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]


@lru_cache(maxsize=None)
def load_fill(repo_root, name):
    """Load large data once in the parent; workers inherit the cached model."""
    repo_root, name = Path(repo_root), str(name)
    rr = repo_root / "research/styles-r11"
    pkg = repo_root / "research/t74-joint-twelve-retired7"
    pins = _load(rr / "data/words/PINS.json")["files"]
    if name in ("2802", "2751"):
        inp = pkg / "inputs"
        names = ["PLAN.json.gz", "GLOBAL-TEMPLATE.json.gz", "ORDER.json", "DISPATCH.json.gz",
                 "PROVIDERS.json" if name == "2802" else "PROVIDERS2751.json",
                 "FILL.json.gz" if name == "2802" else "FILL2751.json.gz"]
        paths = [inp / p for p in names]
        plan, template, order, dispatch0, providers, fill = map(_load, paths)
        expected_path = pkg / "PROFILE.json" if name == "2802" else pkg / "evidence/PR2751-CLAIM.json"
        expected = _load(expected_path)
        if name == "2751": expected = expected["profile"]
        paths.append(expected_path)
        _need(fill["columns"] == COLUMNS, "role columns")
        dispatch = {(s, r): pid for s, r, pid in dispatch0}
        for s, r, pid in fill["dispatch_overrides"]:
            _need((s, r) in dispatch and pid in providers, "dispatch override")
            dispatch[s, r] = pid
        _need(set(dispatch) == set(map(tuple, order)), "dispatch coverage")
        widths = [tuple(providers[dispatch[tuple(call)]]["widths"]) for call in order]
        profiles = [{int(r): n for r, n in providers[dispatch[tuple(call)]]["actual_paid_profile"].items()} for call in order]
        rows = [tuple(row) for row in fill["rows"]]
        word_prefix = "WORD" if name == "2802" else "WORD2751"
        attrs = [dict(pins[f"research/t74-joint-twelve-retired7/inputs/{word_prefix}-{f}.json.gz"])
                 for f in ("base", "extra")]
        word_paths={pid:inp/f"{word_prefix}-{tag}.json.gz" for pid,tag in (("gauge44","base"),("extra","extra"))}
        held_words={pid:_load(path) for pid,path in word_paths.items()}
        provider_profile_equal={}
        for pid,w in held_words.items():
            v=w["report"]["v"];removed=set(w.get("removed",[]))
            held_widths=tuple(len(w.get("helper_final",{}).get(str(h),list(range(w["report"]["h"]))))
                              -len(w.get("start_extra",{}).get(str(h),[]))
                              for h in range(2*v,2*v+w["report"]["R"]) if h not in removed)
            _need(held_widths==tuple(providers[pid]["widths"]),"held-word/provider exact width parity")
            provider_profile_equal[pid]=({int(r):n for r,n in w["report"]["local_profile"].items()}
                                         =={int(r):n for r,n in providers[pid]["actual_paid_profile"].items()})
        overlay=None if all(provider_profile_equal.values()) else [
            {int(r):n for r,n in held_words[dispatch[tuple(call)]]["report"]["local_profile"].items()} for call in order]
        notes=dict(provider_profile_source="pinned package providers",pinned_word_provider_profile_parity=provider_profile_equal,
                   pinned_word_provider_width_parity=True)
        paths.extend(word_paths.values())
        expected_mass = 73 * plan["live"] * 2 - plan["deficit"] * 2
    elif name == "1672":
        paths = [rr / f"data/fills/1672-{p}" for p in ("PLAN.json", "GLOBAL-TEMPLATE.json.gz", "OWNERS.json.gz", "PROFILE.json")]
        plan, template, owners, expected = map(_load, paths)
        order = plan["order"]
        bytime = {x["time"]: x for x in plan["per_call_widths"]}
        _need(set(bytime) == set(range(len(order))), "per-call widths coverage")
        widths = [tuple(bytime[t]["widths"]) for t in range(len(order))]
        pc = {x["time"]: x for x in plan["provider_calls"]}
        _need(set(pc) == set(range(len(order))), "provider calls coverage")
        profiles = [{int(r): n for r, n in plan["provider_registry"][pc[t]["provider"]]["actual_paid_profile"].items()}
                    for t in range(len(order))]
        rows = []
        for d in owners:
            t, h = d["time"], d["helper"]
            _need((d["stage"], d["replica"]) == tuple(order[t]), "owner call coordinates")
            _need(d["width"] == widths[t][h], "owner stored width")
            family = d["owner_replica"] * 896 + (2 * plan["pairs"][str(d["child"])] + plan["sides"][str(d["child"])]) * 112 + d["port"]
            _need(d["family"] == family, "owner family coordinates")
            rows.append(tuple(d[k] for k in COLUMNS))
        raw = {f: _load(rr / f"data/words/1672-{f}-word-566-554.json.gz") for f in ("gauge44", "extra")}
        attrs = [dict(pins[f"1672-{f}-word-566-554.json.gz"]) for f in ("gauge44", "extra")]
        overlay = [{int(r): n for r, n in raw[pc[t]["provider"]]["report"]["local_profile"].items()}
                   for t in range(len(order))]
        # Widths are derived from the held words, not just inventory histograms.
        for t in range(len(order)):
            w = raw[pc[t]["provider"]]; v = w["report"]["v"]
            held_widths = tuple(len(w.get("helper_final", {}).get(str(h), list(range(w["report"]["h"]))))
                                - len(w.get("start_extra", {}).get(str(h), []))
                                for h in range(2*v, 2*v+w["report"]["R"]))
            _need(held_widths == widths[t], "held #1672 word widths differ from inherited owner widths")
        notes = dict(provider_profile_source="inherited PLAN.provider_registry", held_word_profile_differs=overlay != profiles,
                     overlay_policy="Literal inherited fill is checked against supplied PROFILE; held #1672 word local profiles are separately substituted at identical exact helper widths.")
        expected_mass = 73 * plan["live"] - plan["deficit"]
    else:
        raise ValueError(("unknown held fill", name))
    fam = {int(c): 2 * p + plan["sides"][c] for c, p in plan["pairs"].items()}
    return FillModel(name=name, rows=rows, order=order, widths=widths, local_profiles=profiles,
                     win=windows(template, order), family=fam,
                     expected_profile={int(r): n for r, n in expected.items()}, expected_mass=expected_mass,
                     sources=_sources(paths), attributions=attrs, overlay_local_profiles=overlay, source_notes=notes)


def _profile(local_profiles, idle):
    profile = Counter(idle)
    for local in local_profiles:
        profile.update(local)
    return dict(sorted(profile.items()))


def kappa_float(profile):
    """Diagnostic root at double precision; final endpoint uses root.py."""
    items = [(c * r / 73, math.log(73 / r)) for r, c in profile.items()]
    lo, hi = 0.0, 0.01
    _need(sum(a for a, _ in items) < 66304, "positive root bracket lower")
    _need(sum(a*math.exp(hi*b) for a, b in items) > 66304, "root bracket upper")
    for _ in range(60):
        mid = (lo+hi)/2
        if math.fsum(a*math.exp(mid*b) for a, b in items) < 66304:
            lo=mid
        else:
            hi=mid
    return (lo+hi)/2


def audit(model, rows=None, require_profile=True):
    rows = model.rows if rows is None else rows
    calls, win = model.calls, model.win
    _need(len(set(map(tuple, model.order))) == calls, "call coverage")
    _need(len(rows) == sum(map(len, model.widths)), "role count")
    helper_bits, families, masks = [0]*calls, [set() for _ in range(calls)], {}
    roles_per_bin = Counter()
    for row in rows:
        _need(len(row) == 6 and all(type(x) is int for x in row), "integer role shape")
        t,h,o,c,p,offset = row
        _need(0<=t<calls and 0<=h<len(model.widths[t]) and 0<=p<model.ports, "role bounds")
        _need((o,c) in win, "known owner window")
        cap,start,stop=win[o,c]
        _need(start<t<=stop, "literal call window")
        bit=1<<h
        _need(not helper_bits[t]&bit, "duplicate helper")
        helper_bits[t]|=bit
        fam=model.family_id(o,c,p)
        _need(fam not in families[t], "same-call family collision")
        families[t].add(fam)
        width=model.widths[t][h]
        _need(0<=offset and offset+width<=cap, "offset capacity")
        mask=((1<<width)-1)<<offset; key=(o,c,p)
        _need(not masks.get(key,0)&mask, "overlapping bin cells")
        masks[key]=masks.get(key,0)|mask
        roles_per_bin[key]+=1
    _need(helper_bits == [(1<<len(ws))-1 for ws in model.widths], "complete helper inventory")
    idle, occupancy, bycap=Counter(), {}, defaultdict(Counter)
    empty_or_full=total_cells=used_cells=0
    for (o,c),(cap,start,stop) in win.items():
        for p in range(model.ports):
            mask=masks.get((o,c,p),0); used=mask.bit_count()
            _need(mask==(1<<used)-1,"compact bin prefix")
            if used<cap: idle[cap-used]+=1
            bycap[cap][used]+=1
            empty_or_full+=used in (0,cap)
            total_cells+=cap;used_cells+=used
    prof=_profile(model.local_profiles,idle)
    primary_idle={1:17316,3:6594,5:9878,32:1,48:26558}
    if require_profile and model.name=="2802":
        _need(dict(idle)==primary_idle,"P-3 registered #2802 idle equality")
    _need(sum(r*n for r,n in prof.items())==model.expected_mass,"rank mass")
    if require_profile:
        _need(prof==model.expected_profile,"literal full-profile parity")
    serial={f"{o},{c}":[cap,list(range(start+1,stop+1))] for (o,c),(cap,start,stop) in win.items()}
    out=dict(fill=model.name,roles=len(rows),calls=calls,helpers_per_call=sorted(set(map(len,model.widths))),
             windows=len(win),bins=len(win)*model.ports,idle=dict(sorted(idle.items())),profile=prof,
             rank_mass=model.expected_mass,total_cells=total_cells,used_cells=used_cells,
             idle_cells=sum(r*n for r,n in idle.items()),clumping=empty_or_full/(len(win)*model.ports),
             occupancy_by_capacity={c:dict(sorted(x.items())) for c,x in bycap.items()},
             roles_per_occupied_bin=dict(Counter(roles_per_bin.values())),
             window_sha256=hashlib.sha256(json.dumps(serial,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
             kappa_diagnostic=kappa_float(prof),all_literal_rules_verified=True,
             sources=model.sources,attributions=model.attributions,source_notes=model.source_notes)
    if model.overlay_local_profiles is not None:
        overlay=_profile(model.overlay_local_profiles,idle)
        _need(sum(r*n for r,n in overlay.items())==model.expected_mass,"overlay mass")
        out["held_word_overlay"] = dict(profile=overlay,kappa_diagnostic=kappa_float(overlay),
                                          width_parity=True,source="held #1672 words")
    return out


def compact_rows(model, rows_without_offsets):
    offsets=Counter();out=[]
    for t,h,o,c,p in rows_without_offsets:
        key=o,c,p; off=offsets[key]
        offsets[key]+=model.widths[t][h]
        out.append((t,h,o,c,p,off))
    return out


def random_flow_fill(model, seed, group_size=8):
    """N3 conditional same-width-slot null, one pass over randomized widths.

    Occupancy and idle are conditioned on the literal fill, so neither can be
    tested by this null.  Each call group is solved by an integer max-flow; the
    original assignment is always a feasible witness.  Not a uniform sampler.
    """
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import maximum_flow
    rng=random.Random(seed)
    rows=[list(r) for r in model.rows]
    original=[tuple(r[:5]) for r in rows]
    bywidth=defaultdict(list)
    families=[set() for _ in range(model.calls)]
    for i,(t,h,o,c,p,_) in enumerate(rows):
        bywidth[model.widths[t][h]].append(i)
        families[t].add(model.family_id(o,c,p))
    widths=list(bywidth);rng.shuffle(widths)
    nflows=flow_nodes_max=flow_edges_max=0
    for width in widths:
        times=list(range(model.calls));rng.shuffle(times)
        idx_by_time=defaultdict(list)
        for i in bywidth[width]:idx_by_time[rows[i][0]].append(i)
        for st in range(0,len(times),group_size):
            group=times[st:st+group_size]
            slots=[i for t in group for i in idx_by_time[t]]
            if not slots:continue
            for i in slots:
                t,h,o,c,p,_=rows[i];families[t].remove(model.family_id(o,c,p))
            rng.shuffle(slots)
            calls=[t for t in group if idx_by_time[t]];rng.shuffle(calls)
            node=1;cn={t:node+j for j,t in enumerate(calls)};node+=len(calls)
            sn={i:node+j for j,i in enumerate(slots)};node+=len(slots)
            cf={};edges=[]
            for t in calls:
                edges.append((0,cn[t],len(idx_by_time[t])))
                cand=list(slots);rng.shuffle(cand)
                for i in cand:
                    _,_,o,c,p,_=rows[i];fam=model.family_id(o,c,p)
                    cap,start,stop=model.win[o,c]
                    if not start<t<=stop or fam in families[t]:continue
                    key=t,fam
                    if key not in cf:
                        cf[key]=node;node+=1;edges.append((cn[t],cf[key],1))
                    edges.append((cf[key],sn[i],1))
            sink=node
            edges.extend((sn[i],sink,1) for i in slots)
            aa,bb,cc=zip(*edges)
            graph=csr_matrix((np.asarray(cc,dtype=np.int64),(aa,bb)),shape=(sink+1,sink+1))
            result=maximum_flow(graph,0,sink)
            _need(result.flow_value==len(slots),"conditional flow did not recover feasible witness")
            flow=result.flow.tocsr(); assignments={}
            slot_for_node={n:i for i,n in sn.items()}
            for (t,fam),n in cf.items():
                for k in range(flow.indptr[n],flow.indptr[n+1]):
                    if flow.data[k]>0 and flow.indices[k] in slot_for_node:
                        assignments[slot_for_node[flow.indices[k]]]=t
            _need(len(assignments)==len(slots),"flow assignment coverage")
            hs={t:[rows[i][1] for i in idx_by_time[t]] for t in calls}
            for x in hs.values():rng.shuffle(x)
            # Slots retain their literal bin and offset. Role labels/time change.
            for i in slots:
                t=assignments[i];rows[i][0]=t;rows[i][1]=hs[t].pop()
                _,_,o,c,p,_=rows[i];families[t].add(model.family_id(o,c,p))
            nflows+=1;flow_nodes_max=max(flow_nodes_max,sink+1);flow_edges_max=max(flow_edges_max,len(edges))
    result_rows=[tuple(r) for r in rows]
    verified=audit(model,result_rows)
    return dict(protocol="N3 conditional equal-width literal slots, random call groups, integer max-flow; fixed occupancy",
                seed=seed,group_size=group_size,passes=1,flow_solves=nflows,
                max_flow_nodes=flow_nodes_max,max_flow_edges=flow_edges_max,
                changed_role_rows=sum(tuple(r[:5])!=old for r,old in zip(rows,original)),
                idle_is_conditioned=True,all_literal_rules_verified=verified["all_literal_rules_verified"],
                idle=verified["idle"],row_sha256=hashlib.sha256(json.dumps(result_rows,separators=(",",":")).encode()).hexdigest())


def interval_slacks(model, window_values=None):
    """Enumerate every nonempty contiguous call interval exactly in O(T^2+W)."""
    import numpy as np
    vals=list(model.win.values()) if window_values is None else window_values
    n=model.calls
    bystop=np.zeros(n,dtype=np.int64);bystart=np.zeros(n+1,dtype=np.int64)
    total=0
    for cap,start,stop in vals:
        if stop<=start:continue
        c=cap*model.ports;total+=c;bystop[stop]+=c;bystart[start+1]+=c
    stop_less=np.r_[0,np.cumsum(bystop)[:-1]]
    start_ge=np.cumsum(bystart[::-1])[::-1][1:]
    demand=np.array([sum(x) for x in model.widths],dtype=np.int64)
    prefix=np.r_[0,np.cumsum(demand)]
    minimum=None;certs=[];zeros=negatives=0
    for a in range(n):
        b=np.arange(a,n)
        capacity=total-stop_less[a]-start_ge[b]
        demands=prefix[b+1]-prefix[a]
        slack=capacity-demands
        local=int(slack.min())
        if minimum is None or local<minimum:
            minimum=local;certs=[]
        if local==minimum:
            for j in np.flatnonzero(slack==local)[:24-len(certs)]:
                certs.append(dict(start=a,stop=int(b[j]),demand=int(demands[j]),
                                  neighbourhood_capacity=int(capacity[j]),slack=local))
        zeros+=int(np.count_nonzero(slack==0));negatives+=int(np.count_nonzero(slack<0))
    return dict(n_intervals=n*(n+1)//2,minimum_slack=minimum,minimum_certificates=certs,
                binding_intervals=zeros,violating_intervals=negatives)


def capacity_flow(model, window_values=None, include_certificate=True):
    """Integer divisible-cell calls→eligible windows transportation relaxation."""
    import numpy as np
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import maximum_flow, breadth_first_order
    vals=list(model.win.values()) if window_values is None else list(window_values)
    n,m=model.calls,len(vals);sink=1+n+m
    demand=np.asarray([sum(x) for x in model.widths],dtype=np.int64)
    caps=np.asarray([c*model.ports for c,_,_ in vals],dtype=np.int64)
    starts=np.asarray([s for _,s,_ in vals]);stops=np.asarray([s for _,_,s in vals])
    tt=np.arange(n)[:,None]
    ci,wi=np.nonzero((starts[None,:]<tt)&(tt<=stops[None,:]))
    supply=int(demand.sum())
    aa=np.concatenate([np.zeros(n,dtype=int),1+ci,1+n+np.arange(m)])
    bb=np.concatenate([1+np.arange(n),1+n+wi,np.full(m,sink,dtype=int)])
    cc=np.concatenate([demand,np.full(len(ci),supply+1,dtype=np.int64),caps])
    graph=csr_matrix((cc,(aa,bb)),shape=(sink+1,sink+1))
    solved=maximum_flow(graph,0,sink)
    out=dict(flow_value=int(solved.flow_value),demand=supply,capacity=int(caps.sum()),
             feasible=int(solved.flow_value)==supply,missing_cells=supply-int(solved.flow_value),
             nodes=sink+1,edges=len(cc),scope="divisible-cell capacity relaxation; family and indivisible-width constraints dropped")
    if include_certificate:
        residual=(graph-solved.flow).tocsr();residual.data=(residual.data>0).astype(np.int8);residual.eliminate_zeros()
        reached=set(map(int,breadth_first_order(residual,0,directed=True,return_predecessors=False)))
        cs=[t for t in range(n) if 1+t in reached]
        ws=[j for j in range(m) if 1+n+j in reached]
        cut=sum(int(c) for a,b,c in zip(aa,bb,cc) if int(a) in reached and int(b) not in reached)
        _need(cut==int(solved.flow_value),"mincut capacity mismatch")
        out["mincut"]=dict(capacity=cut,source_side_calls=cs,source_side_window_indices=ws,
                            call_demand=sum(int(demand[t]) for t in cs),window_capacity=sum(int(caps[j]) for j in ws),
                            verified=True)
    return out


def jitter_windows(model, rng):
    vals=[];n=model.calls
    for cap,start,stop in model.win.values():
        s=max(-1,min(n-2,start+rng.choice((-1,0,1))))
        e=max(0,min(n-1,stop+rng.choice((-1,0,1))))
        if e<=s:
            e=min(n-1,s+1)
        vals.append((cap,s,e))
    return vals


def flow_map(model, seed, n_jitter=2000, budget_seconds=300):
    """S-6 exact real flow/intervals, same relaxation for endpoint-jitter controls."""
    start=time.monotonic();cpu_start=time.process_time();rng=random.Random(seed)
    real=capacity_flow(model)
    intervals=interval_slacks(model)
    deficits=[];min_slacks=[];timeouts=False
    for _ in range(n_jitter):
        if time.process_time()-cpu_start>=budget_seconds:
            timeouts=True;break
        vals=jitter_windows(model,rng)
        result=capacity_flow(model,vals,include_certificate=False)
        deficits.append(result["missing_cells"])
        # The exact all-interval statistic is part of the same pre-registered null.
        min_slacks.append(interval_slacks(model,vals)["minimum_slack"])
    null=dict(n=len(deficits),planned=n_jitter,mean=statistics.fmean(min_slacks) if min_slacks else None,
              sd=statistics.pstdev(min_slacks) if min_slacks else None,
              empirical_p=((1+sum(x<=intervals["minimum_slack"] for x in min_slacks))/(1+len(min_slacks))) if len(min_slacks)==n_jitter else None,
              infeasible_flows=sum(x>0 for x in deficits),missing_cells_hist=dict(Counter(deficits)))
    if min_slacks:
        ordered=sorted(min_slacks)
        null["central_99_interval"]=[ordered[int(.005*(len(ordered)-1))],ordered[int(.995*(len(ordered)-1))]]
    if timeouts:
        status,decision="TIMEOUT","The registered 2000 jitter controls did not complete inside the CPU budget; no significance claim."
    elif intervals["binding_intervals"]==0:
        status,decision="NULL","No contiguous call interval has slack zero in the registered capacity relaxation, so the primary binding-interval bar fails."
    else:
        status,decision="EXPLORATORY","Binding intervals exist, but the separate forced-rank-1 and matching recorded-promotion witness obligations remain unproved."
    return dict(fill=model.name,seed=seed,real=real,intervals=intervals,null_summary=null,
                status=status,decision=decision,promotion_evidence=promotion_evidence(),
                width_increase_rank1_prediction_supported=False,
                seconds=time.monotonic()-start,cpu_seconds=time.process_time()-cpu_start,attributions=model.attributions,sources=model.sources)


_MODELS=[]


def prepare(repo_root=None, names=("2802","2751","1672")):
    """Parent-only data preparation. Return indexes; do not invoke a pool here."""
    global _MODELS
    repo_root=Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    _MODELS=[load_fill(str(repo_root),str(n)) for n in names]
    return [dict(index=i,name=m.name,rows=len(m.rows),windows=len(m.win)) for i,m in enumerate(_MODELS)]


def task(arg):
    """pool.py worker: {experiment,index,seed,n_permutations?,budget_seconds?}."""
    experiment=arg["experiment"];model=_MODELS[arg.get("index",0)];seed=arg["seed"]
    if experiment=="P3-CEILING":
        import growth_m3
        return growth_m3.pattern_ceiling(model)
    if experiment=="P-3":
        value=audit(model)
        value["N3"]=random_flow_fill(model,seed)
        return dict(status="PASS",statistics=value,decision="Exact literal rules and inherited profile parity; overlay metadata explicitly separate.",n_permutations=0)
    if experiment=="S-6":
        value=flow_map(model,seed,arg.get("n_permutations",2000),arg.get("budget_seconds",300))
        return dict(status=value["status"],statistics=value,decision=value["decision"],
                    n_permutations=value["null_summary"]["n"],null_summary=value["null_summary"])
    raise ValueError(experiment)


def promotion_evidence(repo_root=None):
    """Compare the held losses honestly with the narrower S-6 prediction."""
    root=Path(repo_root) if repo_root is not None else Path(__file__).resolve().parents[3]
    path=root/"research/t74-r10-hosting-leads/J-dim1/out/RELAX-host.json"
    values=_load(path)
    examples={key:dict(recorded_delta_kappa=value["value"],idle_rank1=value["idle"].get("1",0),
                        idle_rank1_change_vs_2802=value["idle"].get("1",0)-17316)
              for key,value in values.items()}
    return dict(source=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                examples=examples,attribution="Marius-Paul Dumitrean r10 J-dim1; pinned PR2745 hosting pattern relaxation",
                comparison="These are whole-call (4,8)->9 hosting relaxations, not a one-role width increase in a binding interval. Several lose kappa while the count of rank-1 idle children decreases. They do not verify the S-6 forced-rank-1 prediction.",
                exact_matching_perturbation_witness_available=False)
