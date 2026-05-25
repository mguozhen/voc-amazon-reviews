#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date -u +%F)}"
MIN_CALLS="${MIN_CALLS:-1}"
MAX_ERROR_RATE_PCT="${MAX_ERROR_RATE_PCT:-20}"
MAX_P95_MS="${MAX_P95_MS:-15000}"

if [[ -z "${REDIS_URL:-}" ]]; then
  echo "[error] REDIS_URL is required for alerts" >&2
  exit 2
fi
if ! command -v redis-cli >/dev/null 2>&1; then
  echo "[error] redis-cli not found" >&2
  exit 2
fi
if ! redis-cli -u "$REDIS_URL" PING >/dev/null 2>&1; then
  echo "[error] redis unreachable: $REDIS_URL" >&2
  exit 2
fi

sum_pattern() {
  local pattern="$1"
  local total=0
  local key
  while IFS= read -r key; do
    [[ -z "$key" ]] && continue
    local v
    v="$(redis-cli -u "$REDIS_URL" GET "$key" 2>/dev/null || echo 0)"
    v="${v:-0}"
    total=$((total + v))
  done < <(redis-cli -u "$REDIS_URL" --scan --pattern "$pattern")
  echo "$total"
}

# Aggregate p95 across all latency keys for the day.
all_latencies="$(redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:latency:${DAY}:*" | while read -r key; do redis-cli -u "$REDIS_URL" LRANGE "$key" 0 -1; done | awk 'NF')"
if [[ -n "$all_latencies" ]]; then
  p95_ms="$(echo "$all_latencies" | sort -n | awk '
    { a[NR]=$1 }
    END {
      if (NR==0) { print 0; exit }
      idx=int((NR*95+99)/100)
      if (idx<1) idx=1
      if (idx>NR) idx=NR
      print a[idx]
    }
  ')"
else
  p95_ms=0
fi

total_ok="$(sum_pattern "mcp:voc:calls:${DAY}:*:*:ok")"
total_err="$(sum_pattern "mcp:voc:calls:${DAY}:*:*:error")"
total_calls=$((total_ok + total_err))

if [[ "$total_calls" -gt 0 ]]; then
  error_rate="$(awk "BEGIN { printf \"%.2f\", (${total_err}*100)/${total_calls} }")"
else
  error_rate="0.00"
fi

status=0

echo "day=$DAY total_calls=$total_calls error_rate_pct=$error_rate p95_ms=$p95_ms"

if (( total_calls < MIN_CALLS )); then
  echo "[ALERT] total_calls ${total_calls} < MIN_CALLS ${MIN_CALLS}"
  status=1
fi

awk -v e="$error_rate" -v max="$MAX_ERROR_RATE_PCT" 'BEGIN { if (e > max) exit 1; exit 0 }' || {
  echo "[ALERT] error_rate_pct ${error_rate} > MAX_ERROR_RATE_PCT ${MAX_ERROR_RATE_PCT}"
  status=1
}

if (( p95_ms > MAX_P95_MS )); then
  echo "[ALERT] p95_ms ${p95_ms} > MAX_P95_MS ${MAX_P95_MS}"
  status=1
fi

if (( status == 0 )); then
  echo "[OK] telemetry thresholds healthy"
fi

exit "$status"
