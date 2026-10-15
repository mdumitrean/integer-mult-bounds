# r10 J-dim1: low-floor lenders for the 48 width-8 (1,1) followers (base: F's double-move words)

**Result: no positive net.** Nothing beats 0.001717794984118634663827. Base and extra words agree everywhere.

## Obstruction map
- **(i) Floor <= 1 lender:** none can exist. Frames are monotone, and every non-target register reaches dim >= 4 before it
  retires: own-life segments of hosted lenders have floor 4, free lenders 6..8 (402 lenders, out/CENSUS-b.json).
- **(iii) Raise the follower:** the first event of 47/48 followers is an anticipatory read `tgt += h` at the entrance frame
  (dim 1), pinned lo = hi = 1 = (target's next frame) ∩ (hostee's next frame), so it is a lattice maximum
  (out/WHY-HI-b.json, code/cap_chain.py). The other follower is written at hi 1.
- **(ii) Re-timing:** the read cannot pass the hostee's first write, and the target's frames stay <= 2 in that window.
- **(iv) Chains:** irrelevant, since no floor is <= 1.
- **(v) A true zero-buffer lender:** not expressible. In the auditor model every live register is a dirty column, and zero
  buffers exist only as cleanup images of restored helpers. Physical stock is not binding (row 2·bitlen + ... = 19545 < 20161).

## New exact mechanism (frame-feasible, auditor PASS, but negative)
The anticipatory reads become dyadic initial corrections `tgt += c·K_op(host)`, pulled back through the precondition. The
hostee is renamed into a cold host (whose row is its pure input) from its first write, with a warp U_host -> E <= hi(k1).
- Screen: 40 hostees with 26 width-4 hosts. 152 certified words were built, all passing the pinned PR2679 auditor.
- Best local delta is -H3 per call: the host's 4 dims absorb the hostee's 1->4 climbs. The inventory changes (4,8)->9.
- Fill relaxation (upper bound): -1.96e-7 per hosting (out/RELAX-host.json).
- **Lead:** keeping the host cold ((4,8)->7) would be worth +8.7e-7 (out/RELAX-host7.json). It needs an exact undo of the
  hostee's writes, but each first-write source is rewritten twice before the final read (code/undo_check.py).

Evidence: code/ (ehost_screen.py, ehost_build.py, ehost_build2.py, relax_host*.py), out/eh/, out/FOR-STACK.json.
