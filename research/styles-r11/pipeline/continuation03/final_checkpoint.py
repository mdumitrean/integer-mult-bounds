"""Read-only final status checkpoint; no scientific pivot or code execution."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import json

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("trusted_final_acquisition", HERE / "checkpoint_sources.py")
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)


def main():
    a = C.Acquisition(C.PKG / "data/continuation-03/final-checkpoint")
    a.receipt["script_sha256"] = C.digest(Path(__file__).read_bytes())
    a.receipt["acquisition_helper_sha256"] = C.digest((HERE / "checkpoint_sources.py").read_bytes())
    a.receipt["limits"] = [
        "Final administrative source/status capture only; the word lane remains stopped and no scientific family is reopened.",
        "Only canonical main, exact-head priority catalog, PR2957/2966/2969 metadata and complete Discussion2612 are refreshed.",
        "This is not an all-PR or all-discussion census; preceding full and pivot checkpoints remain separate immutable evidence.",
        "Public claims remain author-reported and unexecuted here; concurrent edits can occur during acquisition."]
    try:
        main = a.gh([f"repos/{C.REPOSITORY}/commits/main"])
        a.save("main.json.gz", main, {"kind":"REST", "endpoint":f"repos/{C.REPOSITORY}/commits/main"})
        head = main["sha"]
        a.receipt["canonical_main"] = head
        path = "docs/research/agent-task-catalog.json"
        item = a.gh([f"repos/{C.REPOSITORY}/contents/{path}?ref={head}"])
        raw = base64.b64decode(item["content"])
        blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        if blob != item["sha"]:
            raise ValueError("priority catalog Git blob mismatch")
        value = json.loads(raw)
        a.save("priority-catalog.json.gz", value, {"kind":"REST", "commit":head,
            "path":path, "git_blob":blob, "source_sha256":C.digest(raw)})
        a.receipt["priority_revision"] = value["priority_revision"]
        a.receipt["pull_requests"] = {}
        for number in (2957, 2966, 2969):
            pr = a.gh([f"repos/{C.REPOSITORY}/pulls/{number}"])
            a.save(f"pr-{number}.json.gz", pr, {"kind":"REST", "endpoint":f"repos/{C.REPOSITORY}/pulls/{number}"})
            record = {"head":pr["head"]["sha"], "state":pr["state"], "merged":pr["merged"],
                      "updated_at":pr["updated_at"], "author":pr["user"]["login"], "title":pr["title"]}
            a.receipt["pull_requests"][str(number)] = record
            print(json.dumps({"pr":number, **record}), flush=True)
        a.discussion_thread(2612)
    finally:
        a.finish()


if __name__ == "__main__":
    main()
