"""Bounded, read-only public source refresh before a possible G4 pivot."""
from pathlib import Path
import base64
import gzip
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("trusted_checkpoint_sources", HERE / "checkpoint_sources.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
OUT = C.PKG / "data/continuation-03/pivot-checkpoint"


def main():
    a = C.Acquisition(OUT)
    a.receipt["script_sha256"] = C.digest(Path(__file__).read_bytes())
    a.receipt["acquisition_helper_sha256"] = C.digest((HERE / "checkpoint_sources.py").read_bytes())
    a.receipt["limits"] = [
        "Read-only metadata checkpoint; no mathematical verification or fetched-code execution.",
        "Canonical main and exact-head priority catalog, current PR2957 metadata, all open PR bodies, and complete Discussion2612 comments/replies only.",
        "Open PR listing is paginated by creation order but sampled over time; newly closed PR bodies are not refreshed. Prior complete open/closed corpus remains separately pinned.",
        "No claim of global nonoverlap or novelty; other discussion comments, linked local work and unpublished work are outside this refresh."]
    try:
        main = a.gh([f"repos/{C.REPOSITORY}/commits/main"])
        a.save("main.json.gz", main, {"kind":"REST", "endpoint":f"repos/{C.REPOSITORY}/commits/main"})
        head = main["sha"]
        a.receipt["canonical_main"] = head
        print(json.dumps({"canonical_main":head}), flush=True)
        path = "docs/research/agent-task-catalog.json"
        entry = a.gh([f"repos/{C.REPOSITORY}/contents/{path}?ref={head}"])
        raw = base64.b64decode(entry["content"])
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != entry["sha"]:
            raise ValueError("priority catalog Git blob mismatch")
        catalog = json.loads(raw)
        a.save("priority-catalog.json.gz", catalog, {"kind":"REST", "path":path, "commit":head, "git_blob":blob, "source_sha256":C.digest(raw)})
        a.receipt["priority_revision"] = {k:v for k,v in catalog.items() if "revision" in k.lower()}
        pr = a.gh([f"repos/{C.REPOSITORY}/pulls/2957"])
        a.save("pr2957.json.gz", pr, {"kind":"REST", "endpoint":f"repos/{C.REPOSITORY}/pulls/2957"})
        a.receipt["pr2957_head"] = pr["head"]["sha"]
        print(json.dumps({"pr2957_head":pr["head"]["sha"], "updated_at":pr["updated_at"], "state":pr["state"]}), flush=True)
        a.discussion_thread(2612)
        endpoint = f"repos/{C.REPOSITORY}/pulls?state=open&sort=created&direction=desc"
        def fields(p):
            return {k:p.get(k) for k in ("number","title","body","html_url","updated_at","created_at","state")} | {"head":p["head"]["sha"], "author":p["user"]["login"]}
        rows, coverage = a.rest_pages(endpoint, fields)
        a.save("open-prs.json.gz", rows, {"kind":"REST", "endpoint":endpoint})
        coverage["unique_numbers"] = len({p["number"] for p in rows})
        a.receipt["remote"]["open_prs"] = coverage
        print(json.dumps({"phase":"open-prs", **coverage}), flush=True)
        print(json.dumps({"latest":rows[:12]}), flush=True)
    finally:
        a.finish()


if __name__ == "__main__":
    main()
