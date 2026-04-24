---
name: voc-amazon-reviews
description: "VOC AI — Amazon Review Intelligence. Input an ASIN, fetch real Amazon reviews via Shulex VOC API and run AI analysis. Outputs a structured English report: sentiment breakdown, top pain points, key selling points, and Listing optimization suggestions. Triggers: voc, amazon review analysis, asin analysis, voice of customer, listing optimization, pain points, selling points, review insights, amazon fba, product research"
allowed-tools: Bash
metadata:
  openclaw:
    homepage: https://github.com/mguozhen/voc-amazon-reviews
---

# VOC AI — Amazon Review Intelligence

> Input an ASIN, fetch real Amazon reviews via Shulex VOC API, and get a structured English insight report powered by AI.

## Quick Setup (30 seconds)

1. **Get your free API key** at [apps.voc.ai/openapi](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)
2. **Create a key** at [API Keys page](https://apps.voc.ai/openapi/api/keys?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)
3. **Set it**:

```bash
export VOC_API_KEY="your-api-key"
```

New accounts include starter credits — enough for multiple analyses.

## Usage

```bash
# Quick analysis — 8 reviews (5 credits)
bash ~/.agents/skills/voc-amazon-reviews/voc.sh B08N5WRWNW

# Deep analysis — 100 reviews (50 credits)
bash ~/.agents/skills/voc-amazon-reviews/voc.sh B08N5WRWNW --limit 100

# Japan marketplace
bash ~/.agents/skills/voc-amazon-reviews/voc.sh B08N5WRWNW --market JP

# Save report to file
bash ~/.agents/skills/voc-amazon-reviews/voc.sh B08N5WRWNW --limit 100 --output report.md
```

### Supported Marketplaces

| Code | Marketplace |
|------|-------------|
| US | amazon.com |
| CA | amazon.ca |
| MX | amazon.com.mx |
| GB | amazon.co.uk |
| DE | amazon.de |
| FR | amazon.fr |
| IT | amazon.it |
| ES | amazon.es |
| JP | amazon.co.jp |
| AU | amazon.com.au |

## Sample Output

```
╔══════════════════════════════════════════════════════════╗
║     VOC AI Analysis Report                               ║
║  ASIN: B08N5WRWNW  |  Reviews Analyzed: 100              ║
║  Market: US  |  Generated: 2026-04-18                     ║
╚══════════════════════════════════════════════════════════╝

📊 Sentiment Distribution
  Positive  ████████████████░░░░  74%
  Neutral   ███░░░░░░░░░░░░░░░░░  16%
  Negative  ██░░░░░░░░░░░░░░░░░░  10%

🔴 Top 5 Pain Points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Short battery life (28 mentions)
   "Battery drained in 2 days, very disappointed"

🟢 Top 5 Selling Points
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Excellent sound quality (52 mentions)
   "Amazing bass and crystal clear highs for the price"

💡 Listing Optimization Suggestions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Add battery capacity and playtime hours to title
```

## How It Works

```
① Input ASIN
      ↓
② Shulex VOC API fetches real-time Amazon reviews
      ↓
③ Structured review data (rating, body, date, verified, variant)
      ↓
④ AI deep semantic analysis (sentiment, pain points, selling points)
      ↓
⑤ English report
```

## Cost Guide

| Reviews | API Credits | Use Case |
|---------|------------|----------|
| 8 (default) | 5 credits | Quick competitor check |
| 50 | 25 credits | Product validation |
| 100 | 50 credits | Deep analysis |
| 200 | 100 credits | Comprehensive audit |

## Scripts

| File | Description |
|---|---|
| `voc.sh` | Main entry point — orchestrates fetch + analyze |
| `fetch.sh` | Shulex VOC API client (submit task → poll → get reviews) |
| `analyze.sh` | AI analysis engine (sentiment, pain points, selling points) |
| `scraper.sh` | Legacy browser-based scraper (deprecated) |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VOC_API_KEY` | Yes | Shulex VOC API key ([get one free](https://apps.voc.ai/openapi/api/keys?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)) |

## Resources

- [Shulex VOC API Docs](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)
- [API Keys](https://apps.voc.ai/openapi/api/keys?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)
- [Buy Credits](https://apps.voc.ai/openapi/api/billing?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)
