# voc-amazon-reviews

Amazon review VOC (Voice of Customer) analysis skill for [Claude Code](https://claude.ai/code) and [OpenClaw](https://openclaw.ai). Input an ASIN, get deep bilingual insights — straight from your terminal.

## What it does

Scrapes Amazon customer reviews using a real browser (bypassing anti-bot) and runs them through Claude for semantic VOC analysis. No keyword counting — actual language understanding.

- **Sentiment breakdown** — positive / neutral / negative with percentages
- **Top 5 pain points** — what buyers complain about, with real quotes
- **Top 5 selling points** — what buyers love, with real quotes
- **Listing optimization tips** — actionable copy suggestions backed by review data
- **Bilingual output** — every insight in both English and Chinese

## Install

### Claude Code
```bash
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/mguozhen/voc-amazon-reviews.git voc-amazon-reviews
```

### OpenClaw
```bash
clawhub install voc-amazon-reviews
```

## Setup

1. **browser skill** — required for Amazon scraping:
   ```bash
   npx skills add browserbase/skills@browser
   ```

2. **Browserbase account** *(recommended)* — handles Amazon's anti-bot, CAPTCHAs, and residential proxies. [Sign up free](https://browserbase.com).
   ```bash
   export BROWSERBASE_API_KEY="your-key"
   export BROWSERBASE_PROJECT_ID="your-project-id"
   browse env remote
   ```
   Without Browserbase, the scraper falls back to local Chrome but may be blocked by Amazon's sign-in wall.

3. **Anthropic API Key** — for Claude-powered analysis:
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-..."
   ```

## Usage

### Natural language (just talk to Claude)
- "Analyze the reviews for ASIN B08N5WRWNW"
- "Do a VOC analysis on this product: B0F6VWT6SP"
- "What are customers complaining about for B09G9HD6PD?"
- "Find the top selling points from Amazon reviews for B08XYZ"

### CLI
```bash
# Basic analysis (scrapes 100 reviews)
bash skills/voc-amazon-reviews/voc.sh B08N5WRWNW

# Scrape more reviews for deeper analysis
bash skills/voc-amazon-reviews/voc.sh B08N5WRWNW --limit 200

# UK marketplace
bash skills/voc-amazon-reviews/voc.sh B08N5WRWNW --market amazon.co.uk

# Save report to file
bash skills/voc-amazon-reviews/voc.sh B08N5WRWNW --output report.md
```

## Sample output

```
╔══════════════════════════════════════════════════════════════╗
║                  VOC AI Analysis Report                     ║
║  ASIN: B08N5WRWNW  |  Reviews analyzed: 100                ║
║  Market: amazon.com  |  Generated: 2026-03-08              ║
╚══════════════════════════════════════════════════════════════╝

📊 Sentiment Distribution
  Positive  ████████████████░░░░  74%
  Neutral   ███░░░░░░░░░░░░░░░░░  16%
  Negative  ██░░░░░░░░░░░░░░░░░░  10%

🔴 Top 5 Pain Points
══════════════════════════════════════════════════════════════
1. Short battery life (28 mentions)
   "Battery drained in 2 days, very disappointed"

2. Unstable Bluetooth connection (19 mentions)
   "Keeps disconnecting randomly, have to re-pair every day"
...

🟢 Top 5 Selling Points
══════════════════════════════════════════════════════════════
1. Excellent sound quality (52 mentions)
   "Amazing bass and crystal clear highs for the price"
...

💡 Listing Optimization Suggestions
══════════════════════════════════════════════════════════════
1. Add battery capacity (e.g. 800mAh) and playtime to the title
   to reduce 1-star reviews from mismatched expectations

2. Lead with sound quality in the first bullet —
   use authentic customer language like "crystal clear" and "deep bass"
...
```

## Options

```
--limit N          Number of reviews to scrape (default: 100)
--market DOMAIN    Amazon marketplace (default: amazon.com)
                   Supported: amazon.co.uk, amazon.de, amazon.co.jp, amazon.ca, amazon.fr
--output FILE      Save report to a markdown file
--help             Show help
```

## How it works

```
① Input ASIN
      ↓
② browse CLI opens Amazon review page
   (Browserbase: stealth mode + residential proxy)
      ↓
③ Paginated scraping — ratings, titles, bodies, dates
      ↓
④ Claude semantic analysis
   (not keyword counting — actual language understanding)
      ↓
⑤ Bilingual structured report (EN + ZH)
```

## File structure

```
voc-amazon-reviews/
├── SKILL.md       # Skill definition (Claude reads this)
├── voc.sh         # Main entry point
├── scraper.sh     # Amazon review scraper (uses browse CLI)
└── analyze.sh     # Claude analysis + report renderer
```

## Why not use the Amazon API?

Amazon's Product Advertising API doesn't expose review text — only aggregate ratings. Seller Central exports are manual and incomplete. Real browser scraping is the only way to get the actual voice of your customers.

## Cost

| Component | Cost per run |
|---|---|
| Claude analysis (100 reviews) | ~$0.01–0.03 |
| Browserbase remote session | ~$0.01 |
| **Total per ASIN** | **~$0.02–0.05** |

Running on local Chrome (no Browserbase) is free but may be blocked by Amazon.

## Security

`ANTHROPIC_API_KEY` and `BROWSERBASE_API_KEY` are read from environment variables and never written to disk or printed to stdout. Be aware that AI agent session logs may capture tool call arguments — use shell-level `export`, not inline assignments.

**Amazon ToS:** This tool accesses publicly visible review pages the same way a browser does. Use responsibly — avoid high-frequency scraping of the same ASIN.

## License

MIT
