"""Lane D grounding: the owner fill as bins.  A bin = (owner_replica, child, port) cell group within a call time; the PLAN window
of a (stage, replica) call lists [capacity, children].  Measures: number of bins, occupancy, idle per bin, and the size of the
bipartite roles-vs-bins graph Lane C would build.  Run with -I."""
import gzip, json, time, collections
import os as _os
from pathlib import Path as _P
_ROOT = _P(_os.environ.get('IMB_ROOT', _P(__file__).resolve().parents[4]))  # repository root (research/styles-r11/planning/<lane>/)
P = str(_ROOT / "research/t74-joint-twelve-retired7/inputs")
rows = json.load(gzip.open(P + "/FILL.json.gz"))["rows"]          # [time, helper, owner_replica, child, port, offset]
plan = json.load(gzip.open(P + "/PLAN.json.gz")); win = plan["windows"]; disp = json.load(gzip.open(P + "/DISPATCH.json.gz"))
tpl = json.load(gzip.open(P + "/GLOBAL-TEMPLATE.json.gz")); idle = tpl["idle_children"]
cap_of_child = {}
for c in idle: cap_of_child[(c["child"], c["port"])] = c["rank"]
print("idle children (child,port) cells:", len(cap_of_child), "| capacity hist:", dict(sorted(collections.Counter(cap_of_child.values()).items())))
t = time.time()
bins = collections.defaultdict(list)
for r in rows: bins[(r[0], r[2], r[3], r[4])].append(r)
print(f"bins (time, owner_replica, child, port): {len(bins)} | build {time.time()-t:.2f}s")
occ = collections.Counter(len(v) for v in bins.values()); print("roles per bin hist (first 12):", dict(sorted(occ.items())[:12]))
# occupancy per (replica, child, port) across all times = the chip configuration of a bin over the 666 steps
per_cell = collections.Counter((r[2], r[3], r[4]) for r in rows); print("distinct (replica, child, port) cells touched:", len(per_cell), "| max roles in one cell over all times:", max(per_cell.values()))
# helper width per role: from the word's width inventory (helper index -> width) is in the word; here use offset spread as a proxy
by_helper = collections.defaultdict(set)
for r in rows: by_helper[r[1]].add(r[5])
print("offsets per helper (distinct):", dict(sorted(collections.Counter(len(v) for v in by_helper.values()).items())))
w0 = next(iter(win)); print("PLAN window example", w0, win[w0], "| window capacity hist:", dict(sorted(collections.Counter(v[0] for v in win.values()).items())), "| children per window hist:", dict(sorted(collections.Counter(len(v[1]) for v in win.values()).items())))
print("DISPATCH stage/replica/provider example:", disp[:3], "| provider counts:", dict(collections.Counter(d[2] for d in disp)))
print("bipartite graph Lane C would build: roles", len(rows), "x bins", len(bins), "edges = roles (one bin each) =", len(rows), "; window graph: 1332 windows (OWNERS) over 666 call times")
