"""Lane D: #2802 FILL/PLAN/OWNERS detail + timing of one capacity-respecting shuffle of the 271,728 roles."""
import gzip, json, time, collections, random
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
P = str(_ROOT / "research/t74-joint-twelve-retired7")
fill = json.load(gzip.open(P + "/inputs/FILL.json.gz")); rows = fill["rows"]; cols = fill["columns"]
print("FILL columns:", cols)
for i, c in enumerate(cols):
    v = [r[i] for r in rows]; print(f"  {c}: min {min(v)} max {max(v)} distinct {len(set(v))}")
plan = json.load(gzip.open(P + "/inputs/PLAN.json.gz"))
win = plan["windows"]; k0 = next(iter(win)); print("PLAN windows:", len(win), "example key", k0, "value", str(win[k0])[:300])
print("PLAN sides example:", str(plan["sides"]["0"])[:200]); print("PLAN pairs example:", str(plan["pairs"]["0"])[:200])
print("PLAN profile:", plan["profile"], "live", plan["live"], "deficit", plan["deficit"])
pw = plan["per_call_widths"]; print("per_call_widths: calls", len(pw), "helpers per call", len(pw[0]["widths"]), "width hist", dict(sorted(collections.Counter(pw[0]["widths"]).items())))
tpl = json.load(gzip.open(P + "/inputs/GLOBAL-TEMPLATE.json.gz"))
ic = tpl["idle_children"]; print("template idle_children:", len(ic), "rank hist", dict(sorted(collections.Counter(c["rank"] for c in ic).items())), "replicas hist", dict(sorted(collections.Counter(c["replicas"] for c in ic).items())))
print("template calls:", len(tpl["calls"]), "keys", list(tpl["calls"][0].keys()))
own = json.load(open(P + "/evidence/OWNERS.json")); print("OWNERS windows field:", str(own.get("windows"))[:300], "| rank_mass", own.get("rank_mass"), "| helpers_per_call", own.get("helpers_per_call"))
# windows as (time, side?) occupancy
occ = collections.Counter((r[0]) for r in rows); print("roles per time value: count of distinct times", len(occ), "max per time", max(occ.values()), "min", min(occ.values()))
# timing: a within-window shuffle of role identities
t = time.time(); by = collections.defaultdict(list)
for r in rows: by[(r[0], r[1])].append(r)
keys = list(by); print("bins by (col0,col1):", len(keys), "sizes hist", dict(sorted(collections.Counter(len(v) for v in by.values()).items())[:12]))
rng = random.Random(1)
for k in keys: rng.shuffle(by[k])
print(f"one within-bin shuffle of all roles: {time.time()-t:.2f}s")
