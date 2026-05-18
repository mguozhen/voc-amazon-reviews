"""Render a VOC report as a black-gold HTML dashboard.

Output is single-file standalone HTML — no external deps, opens in any browser.

Visual design credit: structure inspired by buluslan/review-analyzer-skill
(MIT). Color palette and layout adapted for the review-analyzer VOC report
schema (sentiment + pain_points + selling_points + tips +
listing_improvements).
"""
from __future__ import annotations

import datetime
import html
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_PATH = HERE / "dashboard_template.html"


def _esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def _render_point(p: dict) -> str:
    zh = _esc(p.get("zh", ""))
    en = _esc(p.get("en", ""))
    count = p.get("count")
    freq = f"×{count}" if count is not None else ""
    return (
        f'<li>'
        f'<span class="label"><b>{zh}</b>'
        f'{(f"<div class=&quot;en&quot;>{en}</div>") if en else ""}</span>'
        f'<span class="freq">{freq}</span>'
        f'</li>'
    )


def _render_listing(report: dict, improvements: dict | None) -> str:
    if not improvements:
        return (
            '<div class="listing-card">'
            '<h3>Listing Optimization</h3>'
            '<p style="color:var(--text-muted);">Call '
            '<code>extract_listing_improvements</code> to populate this section '
            'with copy-ready title / bullets / description rewrites grounded '
            'in actual customer language.</p>'
            '</div>'
        )

    title = _esc(improvements.get("title_suggestion", ""))
    title_reason = _esc(improvements.get("title_reasoning", ""))
    bullets = improvements.get("bullet_suggestions") or []
    description = _esc(improvements.get("description_paragraph", ""))
    keywords = improvements.get("keyword_opportunities") or []
    warnings = improvements.get("warnings") or []

    bullets_html = "".join(
        f'<li>{_esc(b.get("text",""))}'
        + (f'<span class="addresses">addresses: {_esc(b.get("addresses",""))}</span>' if b.get("addresses") else "")
        + '</li>'
        for b in bullets
    )

    kw_html = ""
    if keywords:
        items = "".join(f'<li><span class="label">{_esc(k)}</span></li>' for k in keywords)
        kw_html = (
            '<div class="listing-field">'
            '<div class="label">Missing Keyword Opportunities</div>'
            f'<ul class="bullet-list">{items}</ul>'
            '</div>'
        )

    warn_html = ""
    if warnings:
        items = "".join(f'<li>{_esc(w)}</li>' for w in warnings)
        warn_html = (
            '<div class="listing-field">'
            '<div class="label">Signals NOT fixable in copy (product/QA)</div>'
            f'<ul class="bullet-list" style="border-left:3px solid var(--accent-coral);">{items}</ul>'
            '</div>'
        )

    return f"""
<div class="listing-card">
  <h3>Listing Optimization · grounded in customer language</h3>

  <div class="listing-field">
    <div class="label">Proposed Title</div>
    <div class="value">{title}</div>
    <div class="reasoning">{title_reason}</div>
  </div>

  <div class="listing-field">
    <div class="label">Bullet Suggestions</div>
    <ul class="bullet-list">{bullets_html}</ul>
  </div>

  <div class="listing-field">
    <div class="label">Description Paragraph</div>
    <div class="value" style="color:var(--text-primary);">{description}</div>
  </div>

  {kw_html}
  {warn_html}
</div>
"""


def render_dashboard(
    report: dict,
    *,
    improvements: dict | None = None,
    product_name: str | None = None,
) -> str:
    """Render `report` as a standalone HTML dashboard.

    Args:
        report: The VOC analysis result. Expected shape:
            {
              "asin", "market", "report_markdown",
              "sentiment": {positive, neutral, negative},
              "pain_points": [{zh, en, count}, ...],
              "selling_points": [{zh, en, count}, ...],
              "tips": [{zh, en}, ...],
              "summary_zh", "summary_en"
            }
        improvements: Optional output of `extract_listing_improvements`.
        product_name: Optional friendly product name for the headline.

    Returns:
        Standalone HTML string. Save to .html and open in any browser.
    """
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    sentiment = report.get("sentiment") or {}
    pos = float(sentiment.get("positive", 0))
    neu = float(sentiment.get("neutral", 0))
    neg = float(sentiment.get("negative", 0))
    total = pos + neu + neg
    if total > 0:
        pos_pct = round(pos * 100 / total, 1)
        neu_pct = round(neu * 100 / total, 1)
        neg_pct = round(100 - pos_pct - neu_pct, 1)
    else:
        pos_pct = neu_pct = neg_pct = 0

    pains = report.get("pain_points") or []
    sellings = report.get("selling_points") or []
    asin = _esc(report.get("asin") or "")
    market = _esc(report.get("market") or "US")
    headline = product_name or asin or "Review Analysis"

    total_reviews = report.get("total_reviews") or report.get("meta", {}).get("rows_used") or "—"

    top_pain = pains[0]["zh"] if pains else "—"
    top_pain_count = pains[0].get("count") if pains and pains[0].get("count") is not None else ""

    meta_parts = [
        f'<span><b>ASIN</b>{asin or "—"}</span>',
        f'<span><b>Market</b>{market}</span>',
        f'<span><b>Reviews</b>{total_reviews}</span>',
        f'<span><b>Pain points</b>{len(pains)}</span>',
        f'<span><b>Selling points</b>{len(sellings)}</span>',
    ]

    substitutions = {
        "{{TITLE}}": _esc(headline),
        "{{HEADLINE_HTML}}": (
            f'<em>{_esc(headline)}</em> — VOC Report'
            if headline != "Review Analysis"
            else "<em>Voice-of-Customer</em> Report"
        ),
        "{{SUB_HTML}}": _esc(
            report.get("summary_en")
            or "Sentiment, pain points, selling points and copy-ready listing improvements — extracted from real customer language."
        ),
        "{{META_ROW_HTML}}": "\n".join(meta_parts),
        "{{KPI_TOTAL}}": str(total_reviews),
        "{{KPI_TOTAL_SUB}}": f"market={market}",
        "{{KPI_POS}}": str(pos_pct),
        "{{KPI_NEG}}": str(neg_pct),
        "{{KPI_PAIN}}": _esc(top_pain),
        "{{KPI_PAIN_SUB}}": f"flagged {top_pain_count}× across reviews" if top_pain_count else "Top signal to fix",
        "{{POS_PCT}}": str(pos_pct),
        "{{NEU_PCT}}": str(neu_pct),
        "{{NEG_PCT}}": str(neg_pct),
        "{{TOTAL_REVIEWS}}": str(total_reviews),
        "{{PAIN_COUNT}}": str(len(pains)),
        "{{SELLING_COUNT}}": str(len(sellings)),
        "{{PAIN_POINTS_HTML}}": "\n".join(_render_point(p) for p in pains[:8]) or '<li style="color:var(--text-muted);">No pain points detected</li>',
        "{{SELLING_POINTS_HTML}}": "\n".join(_render_point(p) for p in sellings[:8]) or '<li style="color:var(--text-muted);">No selling points detected</li>',
        "{{LISTING_HTML}}": _render_listing(report, improvements),
        "{{SUMMARY_EN}}": _esc(report.get("summary_en", "")),
        "{{SUMMARY_ZH}}": _esc(report.get("summary_zh", "")),
        "{{GENERATED_AT}}": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    # Decode escaped quotes in the embedded en-text spans:
    substitutions["{{PAIN_POINTS_HTML}}"] = substitutions["{{PAIN_POINTS_HTML}}"].replace("&quot;", '"')
    substitutions["{{SELLING_POINTS_HTML}}"] = substitutions["{{SELLING_POINTS_HTML}}"].replace("&quot;", '"')

    out = template
    for k, v in substitutions.items():
        out = out.replace(k, v)
    return out
