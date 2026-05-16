<p align="center">
  <strong>VOC Amazon Reviews — MCP Server</strong>
</p>

<p align="center">
  The most stable, most complete Amazon review data — accessible to Claude, Cursor, Windsurf, and any MCP-compatible client.<br/>
  <em>Open source. Self-hosted. Real OpenAPI underneath — no scrapers.</em>
</p>

---

## What this is — and why the data matters

[MCP (Model Context Protocol)](https://modelcontextprotocol.io) is the open standard for plugging tools into LLM clients. There are already plenty of MCP servers for Amazon — most ship with a fragile scraper or wrap a vendor's locked dashboard.

**This one is different where it counts: the data layer.** It sits on top of [Shulex VOC OpenAPI](https://apps.voc.ai/openapi) — paid, professional, no scraping. That means:

- **No DOM dependency** — won't break the day Amazon ships a CSS change
- **All 10 marketplaces** — US, CA, MX, GB, DE, FR, IT, ES, JP, AU
- **Up to 1,000 reviews per ASIN per call** — most "free" tools cap at 10–50
- **Full review schema** preserved — verified-purchase, helpful votes, vine voice, variant, dates
- **Live, not cached** — no stale daily snapshots
- **Non-English markets** handled natively — JP/DE/FR/IT/ES reviews captured verbatim, then AI-translated

The MCP server is the **delivery layer** on top of that. Four tools, all built on the same data foundation:

| Tool | What it does |
|---|---|
| `fetch_reviews` | Raw Amazon reviews for an ASIN (no analysis) |
| `analyze_reviews` | AI sentiment / pain-point / selling-point analysis on reviews you already have |
| `voc_full` | One-shot: fetch + analyze |
| `extract_listing_improvements` | **Value-add.** Title, 5 bullets, description, and missing keywords — each suggestion citing the specific review evidence it addresses |

## Why this exists

Most Amazon MCP servers (e.g. Data Dive's) limit you to their cloud-locked keyword research. The data underneath is vendor-locked, the analysis layer is opaque, and you can't audit what's in your context. This server:

- **Data layer is the moat** — paid OpenAPI, not scraping. Stable enough for production.
- **Open source end-to-end** — fork, audit, self-host. No vendor in your data path.
- **Bring your own keys** — Shulex VOC + Anthropic. No per-request middleman, no surprise pricing.
- **Full toolchain** — scrape → analyze → actionable copy, not just keyword tables.
- **Reuses the proven shell skill** — same `fetch.sh` / `analyze.sh` / `voc.sh` from the main repo. The MCP layer is a thin wrapper; the data and analysis logic have their own test suite.

## Install

```bash
git clone https://github.com/mguozhen/voc-amazon-reviews.git
cd voc-amazon-reviews

# Production deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r mcp_server/requirements.txt
```

You need two API keys in your environment:

```bash
export VOC_API_KEY="..."        # https://apps.voc.ai/openapi
export ANTHROPIC_API_KEY="..."  # for extract_listing_improvements only
```

The first three tools (`fetch_reviews`, `analyze_reviews`, `voc_full`) work with just `VOC_API_KEY`. `extract_listing_improvements` additionally needs `ANTHROPIC_API_KEY`.

## Connect to Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the Windows / Linux equivalent. Add the `voc-amazon-reviews` entry under `mcpServers`:

```json
{
  "mcpServers": {
    "voc-amazon-reviews": {
      "command": "/absolute/path/to/voc-amazon-reviews/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/voc-amazon-reviews",
      "env": {
        "VOC_API_KEY": "your-key-here",
        "ANTHROPIC_API_KEY": "your-key-here"
      }
    }
  }
}
```

Restart Claude Desktop. You should see the four tools in the 🔧 tools panel.

## Connect to Claude Code

Add to `~/.claude/mcp_servers.json` (or your project's `.mcp.json`):

```json
{
  "mcpServers": {
    "voc-amazon-reviews": {
      "command": "/absolute/path/to/voc-amazon-reviews/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "cwd": "/absolute/path/to/voc-amazon-reviews",
      "env": {
        "VOC_API_KEY": "...",
        "ANTHROPIC_API_KEY": "..."
      }
    }
  }
}
```

Then in a Claude Code session: `Analyze ASIN B08N5WRWNW and propose listing improvements.`

## Example session

```text
You:    Look up reviews for B08N5WRWNW and propose listing improvements.
Claude: [calls extract_listing_improvements(asin="B08N5WRWNW")]

Title suggestion:
  "8-Hour Battery Pro Earbuds — Premium Build, Stress-Tested USB-C"

Bullets:
  • 8+ hours of battery on a single charge — verified by 31 customer reviews
    (addresses: Battery lasts 8+ hours on a single charge)
  • Stress-tested USB-C port engineered for 5,000+ insertions
    (addresses: Charging port loose after 2 weeks)
  ...

Warnings:
  • Manual translation quality is a real product issue. Better copy
    will not fix it; consider a translator pass on the printed manual.

Keyword opportunities:
  long battery earbuds, premium feel earbuds, stylish wireless
```

## Run tests

```bash
pip install -r mcp_server/requirements-dev.txt
pytest mcp_server/tests/ -v
```

Tests are fully offline — they mock every subprocess and Anthropic call. No Amazon hits, no Shulex credits spent, no Anthropic tokens consumed. CI-safe.

## How it's wired

```
       ┌─────────────────┐
       │ MCP client      │  (Claude Desktop / Code, Cursor, etc.)
       │   tool call ───────┐
       └─────────────────┘  │  MCP over stdio
                            ▼
       ┌──────────────────────────────────────┐
       │  mcp_server.server  (FastMCP)        │
       │  ┌────────────────────────────────┐  │
       │  │ fetch_reviews   ┐              │  │
       │  │ analyze_reviews ┤ → tools.py   │  │
       │  │ voc_full        ┤              │  │
       │  │ extract_…       ┘              │  │
       │  └────────────────────────────────┘  │
       └──────────────────┬──────────────────┘
                          │  subprocess
                  ┌───────┴───────┐
                  ▼               ▼
            fetch.sh         analyze.sh
            (Shulex API)     (LLM analysis)
                  │               │
                  └───────┬───────┘
                          ▼
                 ┌─────────────────┐
                 │ Anthropic API   │  (only extract_listing_improvements)
                 └─────────────────┘
```

The MCP server is a thin Python wrapper. All scraping and base analysis logic continues to live in the shell scripts — same ones tested in `tests/test_unit.sh` and `tests/test_regression.sh`. The MCP layer adds: validated tool I/O, structured JSON output, and the listing-improvement extraction.

## Architecture notes

- **stdio transport.** Default MCP transport. No port to expose, no auth to manage. The client launches the server as a subprocess.
- **One server, four tools.** Adding new tools later (e.g. `compare_asins`, `keyword_research`) is a one-decorator change in `server.py`.
- **No fork of scraping logic.** `tools.py` shells out to the existing `fetch.sh` / `analyze.sh` / `voc.sh`. When those improve, the MCP server improves automatically.
- **Prompt caching on the listing rubric.** The system prompt in `extract_listing_improvements` is frozen, so multi-ASIN sessions share the cache after the first call.

## Limitations

- `extract_listing_improvements` costs ~$0.05–0.20 per call (Claude Opus 4.7). For batch jobs across many ASINs, use the shell skill directly or call from your own automation.
- The Shulex VOC API has its own rate limits + credit cost. See [the main repo README](../README.md) for limits and pricing.
- This is an MCP server, not an HTTP API. To expose over HTTP, wrap with the [MCP SSE adapter](https://modelcontextprotocol.io/docs/sse) (not included).

## License

MIT — same as the parent repo.
