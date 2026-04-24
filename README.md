<p align="center">
  <img src="https://cdn-icons-png.flaticon.com/512/1041/1041916.png" width="80" alt="VOC AI">
</p>

<h1 align="center">VOC Amazon Reviews</h1>

<p align="center">
  <strong>Analyze any Amazon product's reviews in 5 seconds — real API data, AI-powered insights, 10 marketplaces.</strong>
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/setup-30sec-brightgreen?style=flat-square" alt="30s Setup"></a>
  <a href="https://openclaw.ai"><img src="https://img.shields.io/badge/OpenClaw-compatible-blue?style=flat-square" alt="OpenClaw"></a>
  <a href="https://claude.ai/code"><img src="https://img.shields.io/badge/Claude%20Code-skill-8A2BE2?style=flat-square" alt="Claude Code"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="MIT License"></a>
  <img src="https://img.shields.io/badge/markets-10%20Amazon%20regions-FF9900?style=flat-square&logo=amazon&logoColor=white" alt="10 Marketplaces">
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> &bull;
  <a href="#demo">Demo</a> &bull;
  <a href="#usage">Usage</a> &bull;
  <a href="#how-it-works">How It Works</a> &bull;
  <a href="docs/ROADMAP.md">Roadmap</a>
</p>

---

## Demo

<p align="center">
  <img src="demo/voc-demo.gif" width="700" alt="VOC AI Demo — ASIN to report in 5 seconds">
</p>

> **Input an ASIN. Get deep bilingual insights in 5 seconds.** Fetches real Amazon reviews via Shulex VOC API, then runs AI semantic analysis — sentiment, pain points, selling points, and listing optimization tips. Not keyword counting. Actual language understanding.

## Features

| Feature | Description |
|---------|-------------|
| **Sentiment Analysis** | Positive / neutral / negative breakdown with percentages |
| **Pain Points** | Top 5 customer complaints with real quotes and mention counts |
| **Selling Points** | Top 5 things buyers love with real quotes and mention counts |
| **Listing Optimization** | Actionable copy suggestions backed by review data |
| **English Output** | Every insight in clear English |
| **10 Marketplaces** | US, CA, MX, GB, DE, FR, IT, ES, JP, AU |
| **Zero Dependencies** | Only needs `curl` + `python3` (no browser, no npm) |
| **Free to Start** | 8 reviews = 5 credits. New accounts include starter credits |

## Quick Start

**Step 1** — Get your free API key (30 seconds):

👉 [**apps.voc.ai/openapi**](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr)

**Step 2** — Clone and run:

```bash
git clone https://github.com/mguozhen/voc-amazon-reviews.git
cd voc-amazon-reviews
export VOC_API_KEY="your-key"
bash voc.sh B08N5WRWNW
```

That's it. No Docker. No npm install. No config files.

## Usage

```bash
# Quick analysis — 8 reviews (5 credits)
bash voc.sh B08N5WRWNW

# Deep analysis — 100 reviews (50 credits)
bash voc.sh B08N5WRWNW --limit 100

# Japan marketplace
bash voc.sh B08N5WRWNW --market JP

# Save report to file
bash voc.sh B08N5WRWNW --limit 100 --output report.md
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--limit N` | 8 | Number of reviews to fetch |
| `--market CODE` | US | Amazon marketplace (US CA MX GB DE FR IT ES JP AU) |
| `--output FILE` | stdout | Save report to markdown file |
| `--help` | — | Show help |

### Cost Guide

| Reviews | Credits | Use Case |
|---------|---------|----------|
| 8 (default) | 5 | Quick competitor check |
| 50 | 25 | Product validation |
| 100 | 50 | Deep analysis |
| 200 | 100 | Comprehensive audit |

## Sample Output

```
╔══════════════════════════════════════════════════════════════╗
║                 VOC AI Analysis Report                       ║
║  ASIN: B099Z93WD9  |  analyzed: 8 reviews                   ║
║  Market: US  |  Generated: 2026-04-19                        ║
╚══════════════════════════════════════════════════════════════╝

📊 Sentiment Distribution
─────────────────────────────────────────
  Positive  ████████░░░░░░░░░░░░  37%
  Neutral   ██░░░░░░░░░░░░░░░░░░  13%
  Negative  ██████████░░░░░░░░░░  50%

🔴 Top 5 Pain Points
═══════════════════════════════════════════════════════════════
1. Charging port moisture glitch (2 mentions)
   "Moisture in charging port — known glitch, can't charge"

2. Video stalling and weak connection (2 mentions)
   "Stalls out, pausing videos, really annoying"

🟢 Top 5 Selling Points
═══════════════════════════════════════════════════════════════
1. Great value for money (3 mentions)
   "Budget friendly, entertainment on the go"

2. Perfect portable size (2 mentions)
   "Perfect size, light and easy to fit in my purse"

💡 Listing Optimization Suggestions
═══════════════════════════════════════════════════════════════
1. Highlight budget-friendly and portability in title
2. Add charging port care instructions in A+ Content
3. Guide users to sideload popular apps
```

## How It Works

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Input ASIN │────▶│  Shulex VOC API  │────▶│  AI Analysis    │
│             │     │                  │     │                 │
│  B099Z93WD9 │     │  • Real reviews  │     │  • Sentiment    │
│  --market US│     │  • 10 markets    │     │  • Pain points  │
│  --limit 8  │     │  • 5s response   │     │  • Sell points  │
│             │     │  • No scraping   │     │  • Optimization │
└─────────────┘     └──────────────────┘     └────────┬────────┘
                                                      │
                                                      ▼
                                            ┌─────────────────┐
                                            │ English Report  │
                                            │                 │
                                            └─────────────────┘
```

## File Structure

```
voc-amazon-reviews/
├── SKILL.md        # Skill definition (Claude/OpenClaw)
├── voc.sh          # Main entry point
├── fetch.sh        # Shulex VOC API client
├── analyze.sh      # AI analysis + report renderer
├── scraper.sh      # Legacy browser scraper (deprecated)
├── tests/
│   ├── test_unit.sh        # 50 unit tests
│   └── test_regression.sh  # 17 regression tests (live API)
├── demo/
│   ├── voc-demo.gif        # Demo recording
│   └── demo.sh             # Demo script
└── docs/
    ├── GTM.md        # Go-to-market strategy
    ├── ROADMAP.md    # Product roadmap
    └── STORY.md      # Project narrative
```

## FAQ

<details>
<summary><strong>Where does the review data come from?</strong></summary>

Reviews are fetched via the [Shulex VOC API](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr) — a legitimate data provider with proper Amazon data licensing. No scraping. No browser automation. Just a clean API call.
</details>

<details>
<summary><strong>How much does it cost?</strong></summary>

| Component | Cost |
|-----------|------|
| VOC API (8 reviews) | 5 credits |
| VOC API (100 reviews) | 50 credits |
| AI analysis | Depends on your OpenClaw model |

New accounts include starter credits — enough for multiple analyses. [Get your free API key](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr).
</details>

<details>
<summary><strong>Is this against Amazon's Terms of Service?</strong></summary>

No. This tool uses the Shulex VOC API, which is a licensed data provider. It does not scrape Amazon directly.
</details>

<details>
<summary><strong>What about API keys and security?</strong></summary>

`VOC_API_KEY` is read from environment variables — never written to disk or printed to stdout.
</details>

## Related

- [VOC AI](https://www.voc.ai) — Full-featured Amazon review analytics platform
- [VOC Open API](https://apps.voc.ai/openapi?utm_source=github&utm_medium=readme&utm_campaign=launch_apr) — Get your free API key
- [Social Reply Bot](https://github.com/mguozhen/social-bot) — AI-powered social media bot
- [Solvea](https://solvea.cx) — AI receptionist for small businesses

## License

MIT
