#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date -u +%F)}"
TOP_N="${TOP_N:-10}"

if [[ -z "${REDIS_URL:-}" ]]; then
  echo "[error] REDIS_URL is required for daily report" >&2
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

calc_p95_for_tool() {
  local tool="$1"
  local vals
  vals="$(redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:latency:${DAY}:*:${tool}" | while read -r key; do redis-cli -u "$REDIS_URL" LRANGE "$key" 0 -1; done | awk 'NF')"
  if [[ -z "$vals" ]]; then
    echo "n/a"
    return
  fi
  echo "$vals" | sort -n | awk '
    { a[NR]=$1 }
    END {
      if (NR==0) { print "n/a"; exit }
      idx=int((NR*95+99)/100)
      if (idx<1) idx=1
      if (idx>NR) idx=NR
      print a[idx]
    }
  '
}

echo "=== telemetry daily report ==="
echo "day(UTC): $DAY"

total_ok="$(sum_pattern "mcp:voc:calls:${DAY}:*:*:ok")"
total_err="$(sum_pattern "mcp:voc:calls:${DAY}:*:*:error")"
total_calls=$((total_ok + total_err))

if [[ "$total_calls" -gt 0 ]]; then
  error_rate="$(awk "BEGIN { printf \"%.2f\", (${total_err}*100)/${total_calls} }")"
else
  error_rate="0.00"
fi

echo "total_calls: $total_calls"
echo "ok_calls: $total_ok"
echo "error_calls: $total_err"
echo "error_rate_pct: $error_rate"

echo

echo "top_tools:"
redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:calls:${DAY}:*:*:ok" \
  | awk -F: '{print $6}' \
  | sort | uniq -c | sort -nr | head -n "$TOP_N" \
  | while read -r count tool; do
      p95="$(calc_p95_for_tool "$tool")"
      printf "  %s\t%s\tp95_ms=%s\n" "$tool" "$count" "$p95"
    done

echo

echo "top_clients:"
redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:calls:${DAY}:*:*:ok" \
  | awk -F: '{print $5}' \
  | sort | uniq -c | sort -nr | head -n "$TOP_N" \
  | sed 's/^/  /'
