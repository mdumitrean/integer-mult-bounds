#!/bin/sh
# after.sh LOGFILE PATTERN RUN...: wait until PATTERN appears in LOGFILE (a finished chain), then chain4.sh RUN...
G=$(cd "$(dirname "$0")/.." && pwd); f=$1; pat=$2; shift 2
until grep -q "$pat" "$f" 2>/dev/null; do sleep 10; done
sh $G/tools/chain4.sh "$@"
