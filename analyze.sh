#!/usr/bin/env bash
# Amazon review analysis script - using OpenClaw default model
# Usage: analyze.sh <reviews_json_file> <ASIN> [--output file.md]

set -euo pipefail

REVIEWS_FILE="${1:-}"
ASIN="${2:-unknown}"
OUTPUT_FILE=""

shift 2 || true
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ -z "$REVIEWS_FILE" || ! -f "$REVIEWS_FILE" ]]; then
  echo "❌ Reviews data file required" >&2
  echo "Usage: analyze.sh <reviews_json_file> <ASIN> [--output file.md]" >&2
  exit 1
fi

if ! command -v openclaw &>/dev/null; then
  echo "openclaw not found. Please install OpenClaw first." >&2
  exit 1
fi

VOC_MODEL=$(openclaw models status --plain 2>/dev/null || echo "unknown")
echo "Analyzing reviews with model: $VOC_MODEL ..." >&2

# Read review data
REVIEWS_JSON=$(cat "$REVIEWS_FILE")
TOTAL=$(echo "$REVIEWS_JSON" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")
TODAY=$(date +%Y-%m-%d)

# Build analysis prompt
PROMPT=$(cat <<PROMPT
You are a professional Amazon e-commerce analyst. Perform a deep VOC (Voice of Customer) analysis on the following review data.

## Analysis Task

Review count: ${TOTAL}
ASIN: ${ASIN}

## Review Data
\`\`\`json
$(echo "$REVIEWS_JSON" | python3 -c "
import sys, json
reviews = json.load(sys.stdin)
# Limit to 150 reviews to stay within token limit
sample = reviews[:150]
# Normalize fields (compatible with both scraper and API formats)
simplified = [{
    'rating': r.get('rating'),
    'title': r.get('title',''),
    'body': str(r.get('body','') or r.get('content',''))[:500],
    'date': r.get('date','') or r.get('reviewDate',''),
    'verified': bool(r.get('verified') or r.get('verifiedPurchase', False)),
    'variant': r.get('variant',''),
    'helpful': r.get('helpful', r.get('helpfulVotes', 0)),
} for r in sample]
print(json.dumps(simplified, ensure_ascii=False))
" 2>/dev/null || echo "$REVIEWS_JSON" | head -c 15000)
\`\`\`

## Output Format Requirements

Output strictly in the following format, all in English, no additional text:

---
SENTIMENT_POSITIVE: [percentage of positive reviews, e.g. 74]
SENTIMENT_NEUTRAL: [percentage of neutral reviews, e.g. 16]
SENTIMENT_NEGATIVE: [percentage of negative reviews, e.g. 10]
---
PAIN_POINT_1_ZH: [Pain point 1, under 15 words]
PAIN_POINT_1_EN: [Pain point 1 in English, under 15 words]
PAIN_POINT_1_COUNT: [mention count]
PAIN_POINT_1_QUOTE_ZH: [Most representative user quote, under 30 words]
PAIN_POINT_1_QUOTE_EN: [Most representative English user quote, under 30 words]
PAIN_POINT_2_ZH: ...
PAIN_POINT_2_EN: ...
PAIN_POINT_2_COUNT: ...
PAIN_POINT_2_QUOTE_ZH: ...
PAIN_POINT_2_QUOTE_EN: ...
PAIN_POINT_3_ZH: ...
PAIN_POINT_3_EN: ...
PAIN_POINT_3_COUNT: ...
PAIN_POINT_3_QUOTE_ZH: ...
PAIN_POINT_3_QUOTE_EN: ...
PAIN_POINT_4_ZH: ...
PAIN_POINT_4_EN: ...
PAIN_POINT_4_COUNT: ...
PAIN_POINT_4_QUOTE_ZH: ...
PAIN_POINT_4_QUOTE_EN: ...
PAIN_POINT_5_ZH: ...
PAIN_POINT_5_EN: ...
PAIN_POINT_5_COUNT: ...
PAIN_POINT_5_QUOTE_ZH: ...
PAIN_POINT_5_QUOTE_EN: ...
---
SELLING_POINT_1_ZH: [Selling point 1, under 15 words]
SELLING_POINT_1_EN: [Selling point 1 in English, under 15 words]
SELLING_POINT_1_COUNT: [mention count]
SELLING_POINT_1_QUOTE_ZH: [Most representative user quote, under 30 words]
SELLING_POINT_1_QUOTE_EN: [Most representative English user quote, under 30 words]
SELLING_POINT_2_ZH: ...
SELLING_POINT_2_EN: ...
SELLING_POINT_2_COUNT: ...
SELLING_POINT_2_QUOTE_ZH: ...
SELLING_POINT_2_QUOTE_EN: ...
SELLING_POINT_3_ZH: ...
SELLING_POINT_3_EN: ...
SELLING_POINT_3_COUNT: ...
SELLING_POINT_3_QUOTE_ZH: ...
SELLING_POINT_3_QUOTE_EN: ...
SELLING_POINT_4_ZH: ...
SELLING_POINT_4_EN: ...
SELLING_POINT_4_COUNT: ...
SELLING_POINT_4_QUOTE_ZH: ...
SELLING_POINT_4_QUOTE_EN: ...
SELLING_POINT_5_ZH: ...
SELLING_POINT_5_EN: ...
SELLING_POINT_5_COUNT: ...
SELLING_POINT_5_QUOTE_ZH: ...
SELLING_POINT_5_QUOTE_EN: ...
---
TIP_1_ZH: [Listing optimization tip 1, under 50 words]
TIP_1_EN: [Listing optimization tip 1, English, under 50 words]
TIP_2_ZH: ...
TIP_2_EN: ...
TIP_3_ZH: ...
TIP_3_EN: ...
---
SUMMARY_ZH: [One-sentence overall summary, under 30 words]
SUMMARY_EN: [One-sentence overall summary in English, under 30 words]
PROMPT
)

# Call OpenClaw default model
SESSION_ID="voc-$(date +%s)"
RESPONSE=$(openclaw agent --local --session-id "$SESSION_ID" -m "$PROMPT" --json 2>/dev/null)

ANALYSIS=$(echo "$RESPONSE" | python3 -c "
import sys, json
r = json.load(sys.stdin)
payloads = r.get('payloads', [])
if payloads:
    print(payloads[0].get('text', ''))
else:
    print('ERROR: empty response')
" 2>/dev/null)

if [[ -z "$ANALYSIS" ]] || echo "$ANALYSIS" | grep -q "^ERROR:"; then
  echo "❌ OpenClaw call failed: $ANALYSIS" >&2
  exit 1
fi

# Parse structured output and render report
REPORT=$(python3 - <<PYEOF
import re, sys

raw = """$ANALYSIS"""

def get(key):
    m = re.search(rf'^{key}:\s*(.+)$', raw, re.MULTILINE)
    return m.group(1).strip() if m else '—'

def bar(pct):
    try:
        n = int(pct)
        filled = round(n / 5)
        return '█' * filled + '░' * (20 - filled)
    except:
        return '░' * 20

pos = get('SENTIMENT_POSITIVE')
neu = get('SENTIMENT_NEUTRAL')
neg = get('SENTIMENT_NEGATIVE')

report = f"""
╔══════════════════════════════════════════════════════════════╗
║                 VOC AI Analysis Report                       ║
║  ASIN: $ASIN  |  analyzed: $TOTAL reviews                   ║
║  Market: amazon.com  |  Generated: $TODAY                   ║
╚══════════════════════════════════════════════════════════════╝

📊 Sentiment Distribution
─────────────────────────────────────────
  Positive  {bar(pos)}  {pos}%
  Neutral   {bar(neu)}  {neu}%
  Negative  {bar(neg)}  {neg}%

🔴 Top 5 Pain Points
═══════════════════════════════════════════════════════════════
"""

for i in range(1, 6):
    en = get(f'PAIN_POINT_{i}_EN')
    cnt = get(f'PAIN_POINT_{i}_COUNT')
    qen = get(f'PAIN_POINT_{i}_QUOTE_EN')
    if en == '—':
        break
    report += f"""{i}. {en} ({cnt} mentions)
   "{qen}"

"""

report += """🟢 Top 5 Selling Points
═══════════════════════════════════════════════════════════════
"""

for i in range(1, 6):
    en = get(f'SELLING_POINT_{i}_EN')
    cnt = get(f'SELLING_POINT_{i}_COUNT')
    qen = get(f'SELLING_POINT_{i}_QUOTE_EN')
    if en == '—':
        break
    report += f"""{i}. {en} ({cnt} mentions)
   "{qen}"

"""

report += """💡 Listing Optimization Suggestions
═══════════════════════════════════════════════════════════════
"""

for i in range(1, 4):
    en = get(f'TIP_{i}_EN')
    if en == '—':
        break
    report += f"""{i}. {en}

"""

summary_en = get('SUMMARY_EN')
report += f"""📌 Summary
─────────────────────────────────────────
  {summary_en}

══════════════════════════════════════════════════════════════
  Generated by VOC AI Skill
  https://github.com/mguozhen/voc-amazon-reviews
══════════════════════════════════════════════════════════════
"""

print(report)
PYEOF
)

echo "$REPORT"

if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REPORT" > "$OUTPUT_FILE"
  echo "" >&2
  echo "💾 Report saved to: $OUTPUT_FILE" >&2
fi
