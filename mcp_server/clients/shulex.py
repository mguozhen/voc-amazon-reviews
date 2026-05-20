"""Shulex VOC OpenAPI client.

Pure-Python replacement for fetch.sh. Submits a "realtime task" to fetch
Amazon reviews via Shulex VOC, polls until SUCCESS/FAILED, then normalizes
the response into the same shape fetch.sh emitted.

Public entry point: `fetch_reviews(asin, market="US", limit=100)`.
"""
from __future__ import annotations

import os
import time
from typing import Any, Optional

import httpx

API_BASE = "https://openapi.shulex.com"

VALID_MARKETS: frozenset[str] = frozenset(
    {"US", "CA", "MX", "GB", "DE", "FR", "IT", "ES", "JP", "AU"}
)

# Common aliases users pass (domain forms, lowercase) → canonical code.
_MARKET_ALIASES: dict[str, str] = {
    "amazon.com": "US", "us": "US",
    "amazon.ca": "CA", "ca": "CA",
    "amazon.com.mx": "MX", "mx": "MX",
    "amazon.co.uk": "GB", "gb": "GB", "uk": "GB",
    "amazon.de": "DE", "de": "DE",
    "amazon.fr": "FR", "fr": "FR",
    "amazon.it": "IT", "it": "IT",
    "amazon.es": "ES", "es": "ES",
    "amazon.co.jp": "JP", "jp": "JP",
    "amazon.com.au": "AU", "au": "AU",
}

POLL_INTERVAL_S = 5
POLL_TIMEOUT_S = 120
HTTP_TIMEOUT_S = 30


class ShulexError(RuntimeError):
    """Raised when the Shulex API rejects a request or a task fails."""


def _normalize_market(market: str) -> str:
    key = market.strip().lower()
    if key in _MARKET_ALIASES:
        return _MARKET_ALIASES[key]
    upper = market.strip().upper()
    if upper in VALID_MARKETS:
        return upper
    raise ValueError(
        f"unsupported market {market!r}; expected one of "
        f"{sorted(VALID_MARKETS)} (or amazon.com / amazon.co.uk / etc.)"
    )


def _api_key() -> str:
    key = os.environ.get("VOC_API_KEY", "").strip()
    if not key:
        raise ShulexError(
            "VOC_API_KEY not set. Get one free at "
            "https://apps.voc.ai/openapi?utm_source=mcp&utm_medium=onboarding"
        )
    return key


def _safe_json(resp: httpx.Response) -> dict[str, Any]:
    try:
        return resp.json()
    except ValueError:
        return {}


def fetch_reviews(
    asin: str,
    *,
    market: str = "US",
    limit: int = 100,
    poll_interval_s: int = POLL_INTERVAL_S,
    poll_timeout_s: int = POLL_TIMEOUT_S,
    client: Optional[httpx.Client] = None,
) -> dict[str, Any]:
    """Fetch Amazon reviews for an ASIN via Shulex Realtime Task API.

    Args:
        asin: Amazon ASIN (10 alphanumeric chars). Caller is responsible
            for upstream validation.
        market: Marketplace code (US, CA, MX, GB, DE, FR, IT, ES, JP, AU)
            or domain alias (amazon.com, amazon.co.uk, ...).
        limit: Max reviews to return (1-1000). Translates to maxPage on
            the Shulex side (5 credits per page).
        poll_interval_s / poll_timeout_s: Polling cadence + budget.
        client: Optional httpx.Client for dependency injection (tests).

    Returns:
        {"reviews": [...], "meta": {asin, market, total_available, fetched}}

    Raises:
        ShulexError on API failure (auth, task failure, network, timeout).
    """
    market = _normalize_market(market)
    api_key = _api_key()

    # Amazon pages are ~10 reviews each. Cap at 100 pages (Shulex's max).
    max_page = max(1, min(100, (limit + 9) // 10))

    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}

    owned = client is None
    if owned:
        client = httpx.Client(timeout=HTTP_TIMEOUT_S)
    try:
        # ── Step 1: submit realtime review task ───────────────────────
        submit = client.post(
            f"{API_BASE}/v1/api/RtTask01",
            json={
                "asin": asin,
                "market": market,
                "maxPage": max_page,
                "platform": "AMAZON",
            },
            headers=headers,
        )
        submit_data = _safe_json(submit)
        if submit.status_code != 200 or str(submit_data.get("code")) != "0":
            raise ShulexError(
                f"task submit failed (HTTP {submit.status_code}): "
                f"{submit_data or submit.text[:600]}"
            )
        task_id = submit_data.get("data", {}).get("taskId")
        if not task_id:
            raise ShulexError(f"no taskId in submit response: {submit_data}")

        # ── Step 2: poll until SUCCESS / FAILED / timeout ─────────────
        waited = 0
        poll_data: dict[str, Any] = {}
        while waited < poll_timeout_s:
            time.sleep(poll_interval_s)
            waited += poll_interval_s
            poll = client.get(
                f"{API_BASE}/v1/api/RtQry01",
                params={"taskId": task_id, "pageNo": 1, "pageSize": limit},
                headers=headers,
            )
            poll_data = _safe_json(poll)
            status = poll_data.get("data", {}).get("status", "UNKNOWN")
            if status == "SUCCESS":
                break
            if status == "FAILED":
                d = poll_data.get("data", {})
                msg = d.get("errorMsg") or d.get("message") or "unknown error"
                raise ShulexError(f"Shulex task failed: {msg}")
        else:
            raise ShulexError(
                f"Shulex task timed out after {poll_timeout_s}s. "
                "Common causes: API slow, large limit, or network issue."
            )

        # ── Step 3: normalize ─────────────────────────────────────────
        data = poll_data.get("data", {})
        raw_reviews = data.get("reviews", [])[:limit]
        normalized = [
            {
                "rating": r.get("rating"),
                "title": r.get("title", ""),
                "body": r.get("body", "") or r.get("content", ""),
                "date": r.get("reviewDate", ""),
                "verified": bool(r.get("verified") or r.get("verifiedPurchase")),
                "variant": r.get("variant", ""),
                "author": r.get("author", "") or r.get("reviewerName", ""),
                "helpful": r.get("helpfulVotes", 0),
                "reviewId": r.get("reviewId", ""),
                "vineVoice": bool(r.get("isVineVoice")),
            }
            for r in raw_reviews
        ]
        return {
            "reviews": normalized,
            "meta": {
                "asin": data.get("asin", asin),
                "market": data.get("market", market),
                "total_available": data.get("total", 0),
                "fetched": len(normalized),
            },
        }
    finally:
        if owned:
            client.close()
