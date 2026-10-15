#!/bin/sh
# capped.sh LOG cmd...: run with a 6 GiB address-space-free RSS watchdog (macOS: poll ps) and wall timeout from $TMO.
LOG=$1; shift
"$@" > "$LOG" 2>&1 &
PID=$!
T=0; TMO=${TMO:-1800}
while kill -0 $PID 2>/dev/null; do
  RSS=$(ps -o rss= -p $PID 2>/dev/null | tr -d ' ')
  if [ -n "$RSS" ] && [ "$RSS" -gt 6291456 ]; then echo "RSS CAP HIT $RSS KiB" >> "$LOG"; kill -9 $PID; fi
  if [ $T -ge $TMO ]; then echo "TIMEOUT ${TMO}s" >> "$LOG"; kill -9 $PID; fi
  sleep 2; T=$((T+2))
done
wait $PID; echo "EXIT $?" >> "$LOG"
