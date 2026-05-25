"""MCP server entry point.

Run as:
    python -m mcp_server.server

Or register with Codex, Claude Desktop / Claude Code, or another MCP client via the snippets in the
package's README.md. The server speaks the MCP protocol over stdio by
default — no port to manage, no HTTP server to expose.

Set MCP_TRANSPORT=streamable-http (and optionally PORT / MCP_HOST) to
run as an HTTP server instead — used by Smithery and other remote
hosts.

Tools registered:
    - fetch_reviews                — scrape Amazon reviews for one ASIN
    - analyze_reviews              — AI analysis on already-fetched reviews
    - voc_full                     — fetch + analyze in one call
    - extract_listing_improvements — VOC report → copyable title/bullets/desc
    - analyze_csv                  — CSV/Excel input (any platform, not just Amazon)
    - render_dashboard             — VOC report → standalone black-gold HTML
"""
from __future__ import annotations

import os
from time import perf_counter
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

from . import otel_metrics, telemetry, tools

mcp = FastMCP(
    "review-analyzer",
    host=os.environ.get("MCP_HOST", "0.0.0.0"),
    port=int(os.environ.get("PORT", "8080")),
)


def _run_tool_with_telemetry(
    tool_name: str,
    fn: Callable[..., dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    start = perf_counter()
    status = "ok"
    error_type: str | None = None
    try:
        return fn(**kwargs)
    except Exception as exc:
        status = "error"
        error_type = type(exc).__name__
        raise
    finally:
        latency_ms = int((perf_counter() - start) * 1000)
        client = telemetry.detect_client()
        telemetry.track_tool_call(
            tool=tool_name,
            status=status,
            latency_ms=latency_ms,
            error_type=error_type,
            asin=kwargs.get("asin"),
            market=kwargs.get("market"),
            limit=kwargs.get("limit"),
        )
        otel_metrics.record(
            tool=tool_name,
            status=status,
            latency_ms=latency_ms,
            client=client,
            error_type=error_type,
        )


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

    Returns:
        {
          "reviews": [{rating, title, body, date, verified, ...}, ...],
          "meta": {asin, market, total_available, fetched}
        }
    """
    return _run_tool_with_telemetry(
        "fetch_reviews",
        tools.fetch_reviews,
        asin=asin,
        market=market,
        limit=limit,
    )


@mcp.tool()
def analyze_reviews(reviews_json: dict | list, asin: str) -> dict:
    """Run AI analysis on reviews you already have.

    Useful when you fetched reviews via `fetch_reviews` (or your own scraper)
    and want the VOC report — sentiment breakdown, pain points, selling
    points, listing tips — without re-paying the Shulex API.

    Args:
        reviews_json: Either fetch.sh's `{reviews, meta}` envelope, or a
            bare list of review objects.
        asin: 10-character ASIN that the reviews belong to (for the report
            header).

    Returns:
        {asin, market, report_markdown, sentiment, pain_points,
         selling_points, tips, summary_zh, summary_en}
    """
    return _run_tool_with_telemetry(
        "analyze_reviews",
        tools.analyze_reviews,
        reviews_json=reviews_json,
        asin=asin,
    )


@mcp.tool()
def voc_full(asin: str, market: str = "US", limit: int = 100) -> dict:
    """One-shot: fetch reviews AND run AI analysis.

    The default tool for "give me a VOC report on this ASIN" style requests.
    Internally equivalent to `bash voc.sh ASIN` — calls fetch.sh and
    analyze.sh in sequence.

    Args:
        asin: 10-character ASIN.
        market: Market code or amazon.* domain (default: US).
        limit: Number of reviews to fetch (default 100, max 1000).

    Returns: Same shape as `analyze_reviews`.
    """
    return _run_tool_with_telemetry(
        "voc_full",
        tools.voc_full,
        asin=asin,
        market=market,
        limit=limit,
    )


@mcp.tool()
def extract_listing_improvements(asin: str, market: str = "US", limit: int = 100) -> dict:
    """Differentiator tool — derive specific, copyable listing improvements
    from the VOC report, grounded in actual customer language.

    Instead of raw search-volume tables (Data Dive style), the model reads the
    full VOC report and produces a title, 5 bullets, a description paragraph,
    and missing keywords — each suggestion citing the pain point it preempts
    or selling point it amplifies.

    Requires OPENAI_API_KEY. Model defaults to OPENAI_LISTING_MODEL or gpt-4.1.
    """
    return _run_tool_with_telemetry(
        "extract_listing_improvements",
        tools.extract_listing_improvements,
        asin=asin,
        market=market,
        limit=limit,
    )


@mcp.tool()
def analyze_csv(
    csv_path: str,
    product_name: str | None = None,
    market: str = "OTHER",
) -> dict:
    """Analyze any review CSV / Excel — not just Amazon.

    Drag in a Helium 10 export, an eBay / AliExpress scrape, or your own
    Shopify export. The loader fuzzy-matches column names (`内容` / `评价` /
    `body` / `review` / `content` all detected automatically) so you don't
    have to reformat the file.

    Use this when:
      - The product is NOT on Amazon (eBay / AliExpress / D2C)
      - You already have a reviews file from another source
      - You want to bypass the Shulex VOC API entirely

    Args:
        csv_path: Local path or HTTP(S) URL to a .csv / .xls / .xlsx file.
        product_name: Optional friendly name for the report header.
        market: Optional marketplace tag (US / GB / OTHER, etc.).

    Returns: Same shape as `analyze_reviews`, with `meta.columns_detected`
    showing which columns the loader matched.
    """
    return _run_tool_with_telemetry(
        "analyze_csv",
        tools.analyze_csv,
        csv_path=csv_path,
        product_name=product_name,
        market=market,
    )


@mcp.tool()
def render_dashboard(
    report: dict,
    improvements: dict | None = None,
    product_name: str | None = None,
    output_path: str | None = None,
) -> dict:
    """Render a VOC report as a standalone black-gold HTML dashboard.

    The output is single-file HTML — no external dependencies, opens directly
    in any browser. Includes sentiment bar, pain-point / selling-point
    panels, executive summary, and (if `improvements` provided) a
    copy-ready listing optimization card.

    Args:
        report: Output from `analyze_reviews` / `voc_full` / `analyze_csv`.
        improvements: Optional output from `extract_listing_improvements`.
        product_name: Friendly product name for the headline.
        output_path: Optional file path to write the HTML to.

    Returns: {html, bytes, output_path}
    """
    return _run_tool_with_telemetry(
        "render_dashboard",
        tools.render_dashboard,
        report=report,
        improvements=improvements,
        product_name=product_name,
        output_path=output_path,
    )


def main() -> None:
    """Run the MCP server. Transport defaults to stdio; set
    MCP_TRANSPORT=streamable-http (or sse) for remote/HTTP deployment."""
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)


if __name__ == "__main__":
    main()
