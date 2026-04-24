#!/usr/bin/env bash
# Amazon review scraper - based on browse CLI (browser skill)
# Usage: scraper.sh <ASIN> [--limit N] [--market amazon.com]

set -euo pipefail

ASIN="${1:-}"
LIMIT=100
MARKET="amazon.com"
OUTPUT_FILE=""

# Parse arguments
shift || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --limit) LIMIT="$2"; shift 2 ;;
    --market) MARKET="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$ASIN" ]]; then
  echo "Usage: scraper.sh <ASIN> [--limit N] [--market amazon.com]" >&2
  exit 1
fi

# Check for browse CLI
if ! command -v browse &>/dev/null; then
  echo "❌ browse CLI not found. Install the browser skill first:" >&2
  echo "   npx skills add browserbase/skills@browser" >&2
  exit 1
fi

REVIEWS=()
PAGE=1
COLLECTED=0
MAX_PAGES=$(( (LIMIT + 9) / 10 ))  # 10 reviews per page

echo "🔍 Fetching ASIN: $ASIN (target: $LIMIT reviews)" >&2
echo "   Market: https://www.$MARKET" >&2

# Open review page in browser
REVIEW_URL="https://www.${MARKET}/product-reviews/${ASIN}/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews&sortBy=recent"

browse open "$REVIEW_URL" 2>/dev/null || {
  echo "❌ Cannot open review page. Check that ASIN is valid." >&2
  exit 1
}

sleep 3

# Scrape page by page
while [[ $PAGE -le $MAX_PAGES && $COLLECTED -lt $LIMIT ]]; do
  echo "   📄 Scraping page $PAGE..." >&2

  # Get page text content
  PAGE_TEXT=$(browse get text "body" 2>/dev/null || echo "")

  if [[ -z "$PAGE_TEXT" ]]; then
    echo "   ⚠️  Page $PAGE is empty, stopping" >&2
    break
  fi

  # Check for anti-scraping block
  if echo "$PAGE_TEXT" | grep -qi "robot\|captcha\|verify you are human\|automated access"; then
    echo "   ⚠️  Anti-bot block detected. Set BROWSERBASE_API_KEY to use a remote browser." >&2
    echo "   browse env remote" >&2
    break
  fi

  # Extract review section HTML for parsing
  PAGE_HTML=$(browse get html "#cm_cr-review_list" 2>/dev/null || echo "")

  if [[ -n "$PAGE_HTML" ]]; then
    # Temp file for Claude to parse
    TEMP_FILE=$(mktemp /tmp/voc_page_XXXXXX.html)
    echo "$PAGE_HTML" > "$TEMP_FILE"

    # Use Claude to extract structured review data from HTML
    PAGE_REVIEWS=$(infsh app run openrouter/claude-haiku-45 \
      --input "{\"prompt\": \"Extract all reviews from the following Amazon review page HTML and output them as a JSON array. Each review should include: rating (integer 1-5), title, body, date (date string), verified (boolean for verified purchase). Output only the JSON array, no other text.\\n\\nHTML:\\n$(cat "$TEMP_FILE" | head -c 8000)\"}" \
      2>/dev/null || echo "[]")

    rm -f "$TEMP_FILE"

    # Validate JSON array
    if echo "$PAGE_REVIEWS" | python3 -c "import sys,json; data=json.load(sys.stdin); assert isinstance(data, list)" 2>/dev/null; then
      COUNT=$(echo "$PAGE_REVIEWS" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
      REVIEWS+=("$PAGE_REVIEWS")
      COLLECTED=$((COLLECTED + COUNT))
      echo "   ✓ Page $PAGE: $COUNT reviews (total so far: $COLLECTED)" >&2
    else
      echo "   ⚠️  Page $PAGE parse failed, skipping" >&2
    fi
  fi

  # Next page
  PAGE=$((PAGE + 1))
  if [[ $PAGE -le $MAX_PAGES && $COLLECTED -lt $LIMIT ]]; then
    # Click next page
    NEXT_CLICKED=$(browse click "a[data-hook='pagination-bar-anchor']:last-child" 2>/dev/null && echo "ok" || echo "fail")
    if [[ "$NEXT_CLICKED" == "fail" ]]; then
      # Try fallback selector
      browse click "li.a-last a" 2>/dev/null || {
        echo "   ℹ️  Reached last page" >&2
        break
      }
    fi
    sleep 2
  fi
done

browse stop 2>/dev/null || true

# Merge reviews from all pages
echo "📦 Merging review data..." >&2

MERGED=$(python3 - <<'PYEOF'
import sys, json, os

reviews_data = os.environ.get('REVIEWS_JSON', '[]')
all_reviews = []

try:
    pages = json.loads(reviews_data)
    for page in pages:
        if isinstance(page, list):
            all_reviews.extend(page)
        elif isinstance(page, dict):
            all_reviews.append(page)
except:
    pass

# Deduplicate (by first 100 chars of body)
seen = set()
unique = []
for r in all_reviews:
    key = str(r.get('body', ''))[:100]
    if key not in seen:
        seen.add(key)
        unique.append(r)

print(json.dumps(unique, ensure_ascii=False, indent=2))
PYEOF
)

TOTAL=$(echo "$MERGED" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")

echo "✅ Done. Retrieved $TOTAL valid reviews." >&2

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$MERGED" > "$OUTPUT_FILE"
  echo "💾 Data saved to: $OUTPUT_FILE" >&2
else
  echo "$MERGED"
fi
