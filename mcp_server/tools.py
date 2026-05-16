"""Tool implementations behind the MCP server.

Each public function returns plain JSON-serializable dicts so the MCP layer
can hand them back to the client unchanged. The functions are split out
(rather than living inside the `@mcp.tool` decorators) so they can be
exercised in tests without spinning up the MCP server.

All shell calls go through `_run_script`, which executes the existing
`fetch.sh` / `voc.sh` / `analyze.sh` from the repo root — no fork of the
scraping or analysis logic.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Optional

from .schemas import ListingImprovements

REPO_ROOT = Path(__file__).resolve().parent.parent

# Sane upper bound on subprocess wall-clock. Real fetch.sh calls poll the
# Shulex API for up to ~60s before declaring failure; voc.sh adds an LLM
# analysis call after that. 300s leaves room for slow markets without
# letting a wedged subprocess hang an MCP client forever.
DEFAULT_TIMEOUT_S = 300

VALID_ASIN_RE = re.compile(r"^[A-Z0-9]{10}$")


# ── helpers ──────────────────────────────────────────────────────────────

def _validate_asin(asin: str) -> str:
    """Validate ASIN shape. We accept lowercase from MCP clients but normalize
    to upper before passing to the shell scripts (which warn but proceed on
    lowercase) — this keeps our error messages clearer.
    """
    asin = asin.strip().upper()
    if not VALID_ASIN_RE.match(asin):
        raise ValueError(
            f"invalid ASIN {asin!r}: must be 10 alphanumeric characters (e.g. B08N5WRWNW)"
        )
    return asin


def _run_script(
    script: str,
    args: list[str],
    *,
    timeout_s: int = DEFAULT_TIMEOUT_S,
    env_extra: Optional[dict[str, str]] = None,
) -> str:
    """Run one of the repo's shell scripts. Returns stdout.

    Raises RuntimeError on non-zero exit with the trailing 600 chars of
    stderr — enough to debug fetch failures without flooding the client.
    """
    cmd = ["bash", str(REPO_ROOT / script), *args]
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)

    try:
        res = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=timeout_s,
            env=env,
        )
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(
            f"{script} timed out after {timeout_s}s. "
            f"Common causes: Shulex API slow, large --limit, or network issue."
        ) from e

    if res.returncode != 0:
        raise RuntimeError(
            f"{script} failed (exit {res.returncode}): "
            f"{res.stderr.strip()[-600:] or '<no stderr>'}"
        )
    return res.stdout


# ── tool 1: fetch_reviews ────────────────────────────────────────────────

def fetch_reviews(asin: str, market: str = "US", limit: int = 100) -> dict[str, Any]:
    """Fetch raw Amazon reviews via the Shulex VOC API, no analysis."""
    asin = _validate_asin(asin)
    if limit < 1 or limit > 1000:
        raise ValueError(f"limit must be 1-1000, got {limit}")

    with tempfile.NamedTemporaryFile(
        prefix="mcp_fetch_", suffix=".json", delete=False, mode="w"
    ) as tmp:
        out_path = tmp.name
    try:
        _run_script(
            "fetch.sh",
            [asin, "--limit", str(limit), "--market", market, "--output", out_path],
        )
        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # fetch.sh's output shape is already `{reviews: [...], meta: {...}}` —
        # pass through unchanged.
        return data
    finally:
        try:
            os.unlink(out_path)
        except OSError:
            pass


# ── analyze.sh output parser ────────────────────────────────────────────

_LINE_RE = re.compile(r"^([A-Z_0-9]+):\s*(.+)$")


def _parse_analyze_markdown(asin: str, market: str, report_md: str) -> dict[str, Any]:
    """Pull the structured fields analyze.sh embedded as `KEY: value` lines.

    The renderer in analyze.sh emits markers like `SENTIMENT_POSITIVE: 37`,
    `PAIN_POINT_1_ZH: ...`, `TIP_3_EN: ...` interleaved with the prose
    markdown. We grep them out into a flat dict, then assemble structured
    fields. Anything we can't parse stays accessible via `report_markdown`.
    """
    flat: dict[str, str] = {}
    for line in report_md.splitlines():
        m = _LINE_RE.match(line.strip())
        if m:
            flat.setdefault(m.group(1), m.group(2).strip())

    def grouped(prefix: str, suffixes: tuple[str, ...]) -> list[dict[str, str]]:
        items = []
        for i in range(1, 11):  # support up to 10; reports typically have 5
            row = {}
            for suf in suffixes:
                key = f"{prefix}_{i}_{suf}"
                if key in flat:
                    row[suf.lower()] = flat[key]
            if row:
                items.append(row)
        return items

    sentiment: Optional[dict[str, int]] = None
    if {"SENTIMENT_POSITIVE", "SENTIMENT_NEUTRAL", "SENTIMENT_NEGATIVE"} <= flat.keys():
        try:
            sentiment = {
                "positive": int(flat["SENTIMENT_POSITIVE"]),
                "neutral": int(flat["SENTIMENT_NEUTRAL"]),
                "negative": int(flat["SENTIMENT_NEGATIVE"]),
            }
        except ValueError:
            sentiment = None

    return {
        "asin": asin,
        "market": market,
        "report_markdown": report_md,
        "sentiment": sentiment,
        "pain_points": grouped("PAIN_POINT", ("ZH", "EN", "COUNT")),
        "selling_points": grouped("SELLING_POINT", ("ZH", "EN", "COUNT")),
        "tips": grouped("TIP", ("ZH", "EN")),
        "summary_zh": flat.get("SUMMARY_ZH", ""),
        "summary_en": flat.get("SUMMARY_EN", ""),
    }


# ── tool 2: analyze_reviews ──────────────────────────────────────────────

def analyze_reviews(reviews_json: dict[str, Any] | list[dict], asin: str) -> dict[str, Any]:
    """Run AI analysis on a reviews JSON object (or list) that was previously
    fetched. Useful when the caller already has reviews from `fetch_reviews`
    and wants to re-analyze without paying the Shulex API a second time.
    """
    asin = _validate_asin(asin)

    # Accept both fetch.sh's `{reviews, meta}` shape and a bare list.
    if isinstance(reviews_json, list):
        wrapped = {"reviews": reviews_json, "meta": {"asin": asin, "market": "US"}}
    else:
        wrapped = reviews_json
        wrapped.setdefault("meta", {}).setdefault("asin", asin)

    market = wrapped.get("meta", {}).get("market", "US")

    with tempfile.NamedTemporaryFile(
        prefix="mcp_reviews_", suffix=".json", delete=False, mode="w", encoding="utf-8"
    ) as tmp:
        json.dump(wrapped, tmp, ensure_ascii=False)
        reviews_path = tmp.name
    try:
        report_md = _run_script("analyze.sh", [reviews_path, asin])
    finally:
        try:
            os.unlink(reviews_path)
        except OSError:
            pass

    return _parse_analyze_markdown(asin, market, report_md)


# ── tool 3: voc_full ─────────────────────────────────────────────────────

def voc_full(asin: str, market: str = "US", limit: int = 100) -> dict[str, Any]:
    """One-shot: scrape + analyze. Equivalent to `bash voc.sh ASIN`."""
    asin = _validate_asin(asin)
    if limit < 1 or limit > 1000:
        raise ValueError(f"limit must be 1-1000, got {limit}")

    report_md = _run_script(
        "voc.sh",
        [asin, "--limit", str(limit), "--market", market],
    )
    return _parse_analyze_markdown(asin, market, report_md)


# ── tool 4: extract_listing_improvements ─────────────────────────────────

# Static rubric — frozen so prompt caching works. Do not interpolate
# per-request data into this string (timestamps, user IDs, ASIN values, etc.)
# or every call will be a cache miss.
_LISTING_SYSTEM_PROMPT = """You are a senior Amazon listing strategist with 10+ years of FBA experience.

You read VOC (Voice of Customer) analysis reports and translate the customer signals into specific, copyable listing improvements: title, bullets, description, and missing keywords.

NON-NEGOTIABLE RULES:

1. **Ground every suggestion in actual review language.** Each bullet must cite the pain point it preempts or the selling point it amplifies. No invented benefits.

2. **Preempt complaints, don't hide them.** If reviews say "battery dies in 2 hours," don't write "all-day battery." Write something the product can actually deliver, like "Tested for 3 hours of continuous use" — or flag that this can't be fixed in copy.

3. **Use buyer words, not seller words.** If reviews say "comfy," use "comfy" — don't translate to "ergonomic." Search keywords should be pulled directly from review text.

4. **Some problems can't be fixed in copy.** If reviews flag a real product defect (e.g., "stitching falls apart"), say so in `warnings`. Better listing copy on a broken product gets more returns, not more sales.

5. **5 bullets, not more, not fewer.** Amazon allows 5 main bullets; that's the production format.

6. **Title under 200 chars.** Amazon's limit; longer titles get truncated.
"""


def extract_listing_improvements(
    asin: str,
    market: str = "US",
    limit: int = 100,
    *,
    _client: Any = None,  # injected by tests
) -> dict[str, Any]:
    """Run the full VOC pipeline, then call Claude to extract structured
    listing copy suggestions.

    The differentiator vs. Data Dive's MCP: their MCP exposes keyword
    research; ours adds *actionable copy suggestions* directly grounded in
    the customer signal from real reviews.
    """
    # 1. Get the analysis (re-uses voc_full, including its ASIN validation).
    report = voc_full(asin, market=market, limit=limit)

    # 2. Run Claude with structured-output coercion to a ListingImprovements
    #    pydantic model. Uses prompt caching on the system rubric so
    #    repeated extract_listing_improvements calls in the same session
    #    share the cache.
    if _client is None:
        # Imported lazily so tests can run without the package installed.
        import anthropic
        _client = anthropic.Anthropic()

    user_content = (
        f"ASIN: {report['asin']}  ({report['market']} marketplace)\n\n"
        f"Here is the VOC analysis report for this listing:\n\n"
        f"---\n{report['report_markdown']}\n---\n\n"
        f"Produce the structured listing improvements per your rubric. "
        f"Cite the specific pain points and selling points from the report."
    )

    result = _client.messages.parse(
        model="claude-opus-4-7",
        max_tokens=16000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        system=[
            {
                "type": "text",
                "text": _LISTING_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
        output_format=ListingImprovements,
    )

    improvements = result.parsed_output
    if improvements is None:
        raise RuntimeError(
            "Claude returned a refusal or unparseable structured output. "
            f"stop_reason={result.stop_reason}"
        )

    return {
        "asin": report["asin"],
        "market": report["market"],
        "improvements": improvements.model_dump(),
        "source_report": {
            "sentiment": report["sentiment"],
            "pain_points": report["pain_points"],
            "selling_points": report["selling_points"],
            "summary_en": report["summary_en"],
        },
    }
