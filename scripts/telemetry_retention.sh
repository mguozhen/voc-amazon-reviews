#!/usr/bin/env bash
set -euo pipefail

COHORT_DAY="${1:-$(date -u +%F)}"
if [[ -z "${REDIS_URL:-}" ]]; then
  echo "[error] REDIS_URL is required" >&2
  exit 2
fi

day_plus() {
  /bin/date -u -j -v"+$2"d -f "%Y-%m-%d" "$1" +"%Y-%m-%d"
}

d1="$(day_plus "$COHORT_DAY" 1)"
d7="$(day_plus "$COHORT_DAY" 7)"
d30="$(day_plus "$COHORT_DAY" 30)"

cohort_size="$(redis-cli -u "$REDIS_URL" SCARD "mcp:voc:active:${COHORT_DAY}" 2>/dev/null || echo 0)"
if [[ "$cohort_size" -eq 0 ]]; then
  echo "cohort_day=$COHORT_DAY cohort_size=0 d1=0 d7=0 d30=0"
  exit 0
fi

overlap() {
  local a="$1" b="$2"
  redis-cli -u "$REDIS_URL" SINTERSTORE mcp:voc:_tmp:retain "$a" "$b" >/dev/null
  redis-cli -u "$REDIS_URL" EXPIRE mcp:voc:_tmp:retain 30 >/dev/null
  redis-cli -u "$REDIS_URL" SCARD mcp:voc:_tmp:retain
}

d1_retained="$(overlap "mcp:voc:active:${COHORT_DAY}" "mcp:voc:active:${d1}")"
d7_retained="$(overlap "mcp:voc:active:${COHORT_DAY}" "mcp:voc:active:${d7}")"
d30_retained="$(overlap "mcp:voc:active:${COHORT_DAY}" "mcp:voc:active:${d30}")"

pct() { awk "BEGIN { if ($2==0) print \"0.00\"; else printf \"%.2f\", ($1*100)/$2 }"; }

d1_pct="$(pct "$d1_retained" "$cohort_size")"
d7_pct="$(pct "$d7_retained" "$cohort_size")"
d30_pct="$(pct "$d30_retained" "$cohort_size")"

echo "cohort_day=$COHORT_DAY cohort_size=$cohort_size d1=$d1_retained(${d1_pct}%) d7=$d7_retained(${d7_pct}%) d30=$d30_retained(${d30_pct}%)"
