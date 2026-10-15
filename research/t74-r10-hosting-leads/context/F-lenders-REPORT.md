# r10 F-lenders REPORT

**Gain (candidate, not fully released):** two more retired-lender aliases via augmenting paths. kappa = 0.001717794984118634663827 - 1e-46 - 1e-70
(root80 0.0017177949841186346638272299184281789040885843854623122009009272567619811451693129), +3.857e-7 over our retired5 candidate, +5.38e-7 over #2766/#2767.

- Census on the candidate words: 52 followers (48 (1,1) width-8, 4 (4,5) width-5: 667/669/670/671), 404 lenders, 0 direct pairs, 0 chains.
- Treating every B-warp hosting as movable: 24 early hosted lenders (warps 1-4, 22-41; own life ends before B259, lo 4) can take a (4,5)
  follower if their hostee moves to a free lo-5 lender retired before it: only 564/565 qualify -> 192 paths, at most 2 extra aliases.
  Width-8 followers stay blocked (need lo <= 1; minimum lender lo is 4).
- Best: move warps 30/31 (hostees already dim 5 at entry) to 564/565; alias 667<-401, 669<-403. Local {1:-4,2:+6,3:-6}; inventory 5:4->2.
- Checks: pinned PR2679 auditor PASS (both words), native chain PASS 5/5 (both), literal owner check PASS (271,728 roles), exact 1e-24 bracket,
  relaxation = realized fill. NOT run: full_replay.py / strict T74 / outer ledger.
- Evidence: out/RESULT.json, out/EDITS-{base,extra}.json, words/{b,e}-30_564_667-31_565_669.cert.json.gz, out/AUDIT-*-double.json,
  out/NATIVE-*-double.log, out/owner-double/ (FILL, PROVIDERS, OWNER-CHECK.json), out/VALUE-MAP.json, out/CENSUS-cand-*.json, out/AUGMENT-base.json.
