#!/usr/bin/env bash
set -euo pipefail

# Lightweight healthcheck for MCP telemetry.
# - Works with Redis if REDIS_URL is set and redis-cli is installed.
# - Falls back to JSONL presence check when Redis is unavailable.

DAY="${1:-$(date -u +%F)}"
LOG_PATH="${TELEMETRY_LOG_PATH:-./logs/telemetry.jsonl}"

echo "=== telemetry healthcheck ==="
echo "day(UTC): ${DAY}"
echo "telemetry_enabled: ${TELEMETRY_ENABLED:-1}"
echo "log_path: ${LOG_PATH}"
echo

sum_key_pattern() {
  local pattern="$1"
  local total=0
  local key
  while IFS= read -r key; do
    [[ -z "${key}" ]] && continue
    local v
    v="$(redis-cli -u "$REDIS_URL" GET "$key" 2>/dev/null || echo 0)"
    v="${v:-0}"
    total=$((total + v))
  done < <(redis-cli -u "$REDIS_URL" --scan --pattern "$pattern" 2>/dev/null || true)
  echo "$total"
}

if [[ -n "${REDIS_URL:-}" ]] && command -v redis-cli >/dev/null 2>&1; then
  if redis-cli -u "$REDIS_URL" PING >/dev/null 2>&1; then
    echo "[ok] redis reachable"
    total_ok="$(sum_key_pattern "mcp:voc:calls:${DAY}:*:*:ok")"
    total_err="$(sum_key_pattern "mcp:voc:calls:${DAY}:*:*:error")"
    total_calls=$((total_ok + total_err))

    echo "total_calls: ${total_calls}"
    echo "ok_calls: ${total_ok}"
    echo "error_calls: ${total_err}"

    if [[ "$total_calls" -gt 0 ]]; then
      error_rate="$(awk "BEGIN { printf \"%.2f\", (${total_err}*100)/${total_calls} }")"
    else
      error_rate="0.00"
    fi
    echo "error_rate: ${error_rate}%"

    echo
    echo "top_tools (today):"
    redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:calls:${DAY}:*:*:ok" 2>/dev/null \
      | awk -F: '{print $6}' \
      | sort | uniq -c | sort -nr | head -n 10 \
      | sed 's/^/  /'

    echo
    echo "latency_keys_sample:"
    redis-cli -u "$REDIS_URL" --scan --pattern "mcp:voc:latency:${DAY}:*" 2>/dev/null | head -n 5 | sed 's/^/  /'
  else
    echo "[warn] REDIS_URL set but redis is unreachable"
  fi
else
  echo "[info] redis checks skipped (set REDIS_URL and install redis-cli)"
fi

echo
if [[ -f "${LOG_PATH}" ]]; then
  line_count="$(wc -l < "${LOG_PATH}" | tr -d ' ')"
  echo "[ok] jsonl fallback exists: ${LOG_PATH} (${line_count} lines)"
  echo "last_events:"
  tail -n 3 "${LOG_PATH}" | sed 's/^/  /'
else
  echo "[warn] jsonl fallback log not found at ${LOG_PATH}"
fi
