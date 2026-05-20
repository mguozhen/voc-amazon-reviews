"""VOC analysis client — Anthropic SDK replacement for analyze.sh.

Builds the bilingual VOC analysis prompt, sends it to Claude, returns the
raw LLM response with `KEY: VALUE` markers intact so tools.py's parser
(`_parse_analyze_markdown`) can extract the structured fields.

Public entry point: `analyze_reviews(reviews, asin)`.
"""
from __future__ import annotations

import json
from typing import Any, Optional

MODEL = "claude-opus-4-7"
MAX_TOKENS = 4096

# Cap the reviews fed to the model. 150 was the bash script's limit;
# preserving it keeps prompt costs predictable and output stable.
_MAX_REVIEWS = 150
_MAX_BODY_CHARS = 500

# The bilingual rubric is frozen so prompt caching works — never
# interpolate per-request values (timestamps, ASIN, review text) into it.
_SYSTEM_PROMPT = """你是一位专业的亚马逊电商分析师，请对评论数据进行深度 VOC（Voice of Customer）分析。

请严格按以下格式输出，中英文双语，不要添加额外说明：

---
SENTIMENT_POSITIVE: [正面评论数量占比，如 74]
SENTIMENT_NEUTRAL: [中性评论数量占比，如 16]
SENTIMENT_NEGATIVE: [负面评论数量占比，如 10]
---
PAIN_POINT_1_ZH: [痛点1中文描述，15字以内]
PAIN_POINT_1_EN: [Pain point 1 in English, under 15 words]
PAIN_POINT_1_COUNT: [提及次数]
PAIN_POINT_1_QUOTE_ZH: [最典型的中文用户原话或翻译，30字以内]
PAIN_POINT_1_QUOTE_EN: [Most representative English user quote, under 30 words]
PAIN_POINT_2_ZH: ...
PAIN_POINT_2_EN: ...
PAIN_POINT_2_COUNT: ...
PAIN_POINT_2_QUOTE_ZH: ...
PAIN_POINT_2_QUOTE_EN: ...
(continue through PAIN_POINT_5)
---
SELLING_POINT_1_ZH: [卖点1中文描述，15字以内]
SELLING_POINT_1_EN: [Selling point 1 in English, under 15 words]
SELLING_POINT_1_COUNT: [提及次数]
SELLING_POINT_1_QUOTE_ZH: [最典型的中文用户原话或翻译，30字以内]
SELLING_POINT_1_QUOTE_EN: [Most representative English user quote, under 30 words]
(continue through SELLING_POINT_5)
---
TIP_1_ZH: [Listing 优化建议1，中文，50字以内]
TIP_1_EN: [Listing optimization tip 1, English, under 50 words]
TIP_2_ZH: ...
TIP_2_EN: ...
TIP_3_ZH: ...
TIP_3_EN: ...
---
SUMMARY_ZH: [整体一句话总结，30字以内]
SUMMARY_EN: [One-sentence overall summary in English, under 30 words]
"""


class AnalyzerError(RuntimeError):
    """Raised when the LLM returns nothing usable."""


def _simplify_reviews(reviews: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Trim reviews to the fields the analyzer needs, capping body length."""
    out = []
    for r in reviews[:_MAX_REVIEWS]:
        body = r.get("body", "") or r.get("content", "") or ""
        out.append({
            "rating": r.get("rating"),
            "title": r.get("title", ""),
            "body": str(body)[:_MAX_BODY_CHARS],
            "date": r.get("date", "") or r.get("reviewDate", ""),
            "verified": bool(r.get("verified") or r.get("verifiedPurchase", False)),
            "variant": r.get("variant", ""),
            "helpful": r.get("helpful", r.get("helpfulVotes", 0)),
        })
    return out


def analyze_reviews(
    reviews: list[dict[str, Any]],
    asin: str,
    *,
    client: Optional[Any] = None,
) -> str:
    """Run VOC analysis on a list of reviews. Returns raw LLM output with
    `KEY: VALUE` markers — the caller parses it into structured fields.

    Args:
        reviews: List of review dicts (Shulex / fetch_reviews shape).
        asin: ASIN being analyzed — embedded in the user message for the LLM.
        client: Optional `anthropic.Anthropic()` for tests / DI.

    Returns:
        Raw LLM response text. Contains the structured markers the parser
        in `tools._parse_analyze_markdown` extracts.

    Raises:
        AnalyzerError if the response is empty or a refusal.
    """
    if not reviews:
        raise ValueError("analyze_reviews requires at least one review")

    if client is None:
        import anthropic
        client = anthropic.Anthropic()

    simplified = _simplify_reviews(reviews)
    user_content = (
        f"评论数量 / Review count: {len(simplified)}\n"
        f"ASIN: {asin}\n\n"
        f"评论数据 / Reviews data:\n"
        f"```json\n{json.dumps(simplified, ensure_ascii=False)}\n```\n\n"
        f"Produce the structured VOC analysis per the system rubric."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": _SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": user_content}],
    )

    # Extract text blocks; concatenate (usually just one).
    parts = []
    for block in getattr(response, "content", []) or []:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    text = "\n".join(parts).strip()

    if not text:
        raise AnalyzerError(
            f"empty response from Claude. stop_reason={getattr(response, 'stop_reason', '?')}"
        )
    return text
