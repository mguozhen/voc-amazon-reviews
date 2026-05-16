"""MCP server entry point.

Run as:
    python -m mcp_server.server

Or register with Claude Desktop / Claude Code via the snippets in this
package's README.md. The server speaks the MCP protocol over stdio by
default — no port to manage, no HTTP server to expose.

Tools registered:
    - fetch_reviews                — scrape Amazon reviews for one ASIN
    - analyze_reviews              — AI analysis on already-fetched reviews
    - voc_full                     — fetch + analyze in one call
    - extract_listing_improvements — VOC report → copyable title/bullets/desc
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from . import tools

mcp = FastMCP("voc-amazon-reviews")


@mcp.tool()
def fetch_reviews(asin: str, market: str = "US", limit: int = 100) -> dict:
    """Fetch raw Amazon reviews for an ASIN via the Shulex VOC API.

    No analysis — returns the raw review array plus metadata. Use this when
    you want to plug reviews into your own analysis pipeline, or when you
    plan to call `analyze_reviews` later (avoids paying the Shulex API
    twice).

    Args:
        asin: 10-character Amazon product ID (e.g. "B08N5WRWNW").
        market: Market code (US, GB, DE, FR, IT, ES, JP, AU, CA, MX) or
            amazon.* domain ("amazon.co.uk"). Default: US.
        limit: Number of reviews to fetch (1-1000). Default: 100.
            Larger limits cost more credits.

    Returns:
        {
          "reviews": [{rating, title, body, date, verified, ...}, ...],
          "meta": {asin, market, total_available, fetched}
        }
    """
    return tools.fetch_reviews(asin=asin, market=market, limit=limit)


@mcp.tool()
def analyze_reviews(reviews_json: dict | list, asin: str) -> dict:
    """Run AI analysis on reviews you already have.

    Useful when you fetched reviews via `fetch_reviews` (or your own
    scraper) and want the VOC report — sentiment breakdown, pain points,
    selling points, listing tips — without re-paying the Shulex API.

    Args:
        reviews_json: Either fetch.sh's `{reviews, meta}` envelope, or a
            bare list of review objects.
        asin: 10-character ASIN that the reviews belong to (for the report
            header).

    Returns:
        {
          "asin", "market", "report_markdown",
          "sentiment": {positive, neutral, negative}    # percentages
          "pain_points": [{zh, en, count}, ...],
          "selling_points": [{zh, en, count}, ...],
          "tips": [{zh, en}, ...],
          "summary_zh", "summary_en"
        }
    """
    return tools.analyze_reviews(reviews_json=reviews_json, asin=asin)


@mcp.tool()
def voc_full(asin: str, market: str = "US", limit: int = 100) -> dict:
    """One-shot: fetch reviews AND run AI analysis. The default tool for
    "give me a VOC report on this ASIN" style requests.

    Internally equivalent to `bash voc.sh ASIN` — calls fetch.sh and
    analyze.sh in sequence.

    Args:
        asin: 10-character ASIN.
        market: Market code or amazon.* domain (default: US).
        limit: Number of reviews to fetch (default 100, max 1000).

    Returns: Same shape as `analyze_reviews`.
    """
    return tools.voc_full(asin=asin, market=market, limit=limit)


@mcp.tool()
def extract_listing_improvements(asin: str, market: str = "US", limit: int = 100) -> dict:
    """Differentiator tool — derive specific, copyable listing improvements
    from the VOC report, grounded in actual customer language.

    This is the value-add beyond Data Dive's keyword research: instead of
    raw search-volume tables, Claude reads the full VOC report and produces
    title, 5 bullets, a description paragraph, and missing keywords — each
    suggestion citing the pain point it preempts or selling point it
    amplifies.

    Requires the ANTHROPIC_API_KEY env var. Costs ~$0.05-0.20 per call
    depending on report length (model: claude-opus-4-7).

    Args:
        asin: 10-character ASIN.
        market: Market code or amazon.* domain (default: US).
        limit: Reviews to analyze (default 100).

    Returns:
        {
          "asin", "market",
          "improvements": {
              title_suggestion, title_reasoning,
              bullet_suggestions: [{text, addresses}, ...],
              description_paragraph,
              keyword_opportunities: [...],
              warnings: [...]    # signals that can't be fixed in copy
          },
          "source_report": {sentiment, pain_points, selling_points, summary_en}
        }
    """
    return tools.extract_listing_improvements(asin=asin, market=market, limit=limit)


def main() -> None:
    """Run the stdio-transport MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
