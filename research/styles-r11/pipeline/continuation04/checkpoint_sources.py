"""Continuation04 read-only source checkpoint. Remote text is inert data."""
from pathlib import Path
import base64
import gzip
import hashlib
import importlib.util
import json
import re

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]
HELPER = HERE.parent / "continuation03/checkpoint_sources.py"
EXPECTED_HELPER = "5b16a7b2b4a23d7367a10f3909836b959336a8eef8e80360f7b714da4ec84ed5"
if hashlib.sha256(HELPER.read_bytes()).hexdigest() != EXPECTED_HELPER:
    raise ValueError("trusted administrative acquisition helper changed")
spec = importlib.util.spec_from_file_location("styles_cont04_metadata", HELPER)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
OUTPUT = PKG / "data/continuation-04/checkpoint"
GUIDANCE = ("AGENTS.md", "CONTRIBUTING.md", "autoresearch.md",
            "docs/research/agent-task-catalog.json", "docs/research/bottleneck-brief.md",
            "docs/research/research-family-status.md", "certificates/selected-result.json")


def fields(p):
    return {k:p.get(k) for k in ("number","title","body","html_url","updated_at",
        "created_at","closed_at","merged_at","state","draft")} | dict(
        head=p["head"]["sha"], author=p["user"]["login"], base=p["base"]["sha"])


def main():
    a = C.Acquisition(OUTPUT)
    a.receipt["script_sha256"] = C.digest(Path(__file__).read_bytes())
    a.receipt["trusted_acquisition_helper_sha256"] = EXPECTED_HELPER
    a.receipt["limits"] = [
        "Read-only source and overlap refresh. No fetched code is imported/executed and no scientific experiment is run.",
        "All current open PR title/body pages are requested in creation order; pagination samples a changing service, not an atomic snapshot.",
        "Only the100most recently updated closed/merged PR bodies are refreshed; this is not a complete fresh closed-PR corpus. Earlier complete corpus remains separately pinned.",
        "Discussion2612 is fully refreshed. Hubs1163/1166/1167 are fully refreshed when their API updatedAt changes relative to continuation03.",
        "Unpublished/local work, arbitrary linked repositories and all other discussion comments are outside this refresh.",
        "Public source claims and archival merges are not independent mathematical validation or a novelty proof."]
    try:
        entry = a.gh([f"repos/{C.REPOSITORY}/commits/main"])
        a.save("main.json.gz", entry, dict(kind="REST", endpoint=f"repos/{C.REPOSITORY}/commits/main"))
        head = entry["sha"]
        a.receipt["canonical_main"] = head
        print(json.dumps(dict(phase="main", commit=head)), flush=True)
        a.discussion_thread(2612)
        endpoint = f"repos/{C.REPOSITORY}/pulls?state=open&sort=created&direction=desc"
        prs, coverage = a.rest_pages(endpoint, fields)
        a.save("open-prs.json.gz", prs, dict(kind="REST", endpoint=endpoint))
        coverage["unique_numbers"] = len({p["number"] for p in prs})
        a.receipt["remote"]["open_prs"] = coverage
        endpoint = f"repos/{C.REPOSITORY}/pulls?state=closed&sort=updated&direction=desc&per_page=100&page=1"
        closed = [fields(p) for p in a.gh([endpoint])]
        a.save("recent-closed-prs.json.gz", closed, dict(kind="REST", endpoint=endpoint))
        a.receipt["remote"]["recent_closed_prs"] = dict(rows=len(closed), pages=1,
            complete_all_closed=False, scope="100most recently updated at acquisition")
        candidates = [p for p in prs+closed if p["created_at"] >= "2026-10-16T14:30:00Z"]
        print(json.dumps(dict(phase="recent-priorities", rows=[
            {k:p[k] for k in ("number","title","head","author","state","created_at","updated_at")}
            | dict(decimal_tokens=sorted(set(re.findall(r"0\.001[0-9]{6,}",p["body"] or ""))))
            for p in sorted(candidates,key=lambda p:p["number"],reverse=True)])), flush=True)
        a.receipt["named_comparators"] = {}
        for number in (2957,2966,2969):
            pr = a.gh([f"repos/{C.REPOSITORY}/pulls/{number}"])
            a.save(f"pr-{number}.json.gz", pr, dict(kind="REST", endpoint=f"repos/{C.REPOSITORY}/pulls/{number}"))
            a.receipt["named_comparators"][str(number)] = fields(pr)
        prior_pins = json.loads((PKG/"data/continuation-03/guidance/PINS.json").read_text())
        guidance = {}
        for path in GUIDANCE:
            endpoint = f"repos/{C.REPOSITORY}/contents/{path}?ref={head}"
            item = a.gh([endpoint])
            raw = base64.b64decode(item["content"])
            blob = hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
            if blob != item["sha"]:
                raise ValueError("guidance Git blob mismatch")
            name = path.replace("/","__")+".gz"
            data = gzip.compress(raw,mtime=0)
            output = OUTPUT/"guidance"/name
            output.parent.mkdir(parents=True,exist_ok=True)
            with output.open("xb") as handle:
                handle.write(data)
            old = gzip.decompress((PKG/"data/continuation-03/guidance"/name).read_bytes())
            pin = dict(source_path=path,commit=head,git_blob=blob,sha256=C.digest(data),
                source_sha256=C.digest(raw),unchanged_from_prior=old==raw,
                prior_commit=prior_pins["commit"],prior_git_blob=prior_pins["files"][name]["git_blob"])
            guidance[name] = pin
            a.receipt["files"]["guidance/"+name] = dict(pin,bytes=len(data),source=dict(kind="REST",endpoint=endpoint))
            if path.endswith("agent-task-catalog.json"):
                a.receipt["priority_revision"] = json.loads(raw)["priority_revision"]
        a.save("guidance/PINS.json", dict(commit=head,files=guidance),dict(kind="exact-head-guidance-pins"))
        a.receipt["guidance"] = dict(path="data/continuation-04/checkpoint/guidance/PINS.json",
            sha256=C.digest((OUTPUT/"guidance/PINS.json").read_bytes()))
        print(json.dumps(dict(phase="guidance", priority_revision=a.receipt["priority_revision"],
            changes=[k for k,v in guidance.items() if not v["unchanged_from_prior"]])), flush=True)
        query = '''query($number:Int!){repository(owner:"CrocSwap",name:"integer-mult-bounds"){
          discussion(number:$number){id number title body url updatedAt author{login}}
        }}'''
        for number in (1163,1166,1167):
            current = a.graphql(query,dict(number=number))["data"]["repository"]["discussion"]
            old_path = PKG/f"data/continuation-03/checkpoint/threads/discussion-{number}.json.gz"
            prior = json.loads(gzip.decompress(old_path.read_bytes()))
            old = prior["discussion"]
            same = current["updatedAt"] == old["updatedAt"] and current["body"] == old["body"]
            a.save(f"hubs/discussion-{number}-status.json.gz",dict(current=current,
                prior_path=str(old_path.relative_to(PKG)),prior_sha256=C.digest(old_path.read_bytes()),
                api_updatedAt_and_body_unchanged=same),dict(kind="GraphQL",query=query,number=number))
            if not same:
                a.discussion_thread(number)
            else:
                a.receipt["remote"][f"discussion_{number}"] = dict(refreshed_body_only=True,
                    prior_complete_thread_reused=True,prior_updatedAt=old["updatedAt"],
                    limitation="Relies on discussion updatedAt as change signal; replies are not fetched again when it is unchanged.")
    finally:
        a.finish()


if __name__ == "__main__":
    main()
