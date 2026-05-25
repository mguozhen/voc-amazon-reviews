#!/usr/bin/env bash
set -euo pipefail

DAY="${1:-$(date -u +%F)}"
if [[ -z "${REDIS_URL:-}" ]]; then
  echo "[error] REDIS_URL is required" >&2
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

installs="$(sum_pattern "mcp:voc:install:${DAY}:*")"
first_calls="$(redis-cli -u "$REDIS_URL" SCARD "mcp:voc:active:${DAY}" 2>/dev/null || echo 0)"
ok_calls="$(sum_pattern "mcp:voc:calls:${DAY}:*:*:ok")"

echo "day=$DAY installs=$installs first_call_clients=$first_calls ok_calls=$ok_calls"
