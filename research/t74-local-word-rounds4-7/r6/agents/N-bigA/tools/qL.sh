#!/bin/sh
# qL.sh M1 [M2 ...]: lock-aware member queue: skip members another lane has taken (mkdir lock), else row generation + pricing.
S=$(cd "$(dirname "$0")/../../../.." && pwd); N=$S/r6/agents/N-bigA; cd $N || exit 1
for m in "$@"; do
  mkdir out/LOCK-m$m 2>/dev/null || continue
  sh tools/rgN.sh m$m m$m 900 300
  grep -q '"edit_ab"' out/RG-m$m.json 2>/dev/null && sh tools/priceRG.sh m$m
done
