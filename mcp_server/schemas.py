"""Pydantic models for tool outputs.

Kept in a separate module so tests and tool implementations can both import
them without pulling in MCP/Anthropic SDKs.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Review(BaseModel):
    rating: Optional[int] = None
    title: str = ""
    body: str = ""
    date: str = ""
    verified: bool = False
    variant: str = ""
    author: str = ""
    helpful: Optional[int] = None
    reviewId: str = ""
    vineVoice: bool = False


class FetchMeta(BaseModel):
    asin: str
    market: str
    total_available: int = 0
    fetched: int = 0


class FetchResult(BaseModel):
    reviews: list[Review]
    meta: FetchMeta


class AnalyzeReport(BaseModel):
    """Report returned by `analyze_reviews` / `voc_full`.

    Always includes the raw markdown (`report_markdown`). When the report can
    be parsed cleanly, structured fields are populated; on parse failure the
    structured fields are None and the markdown is still returned verbatim.
    """
    asin: str
    market: str = "US"
    report_markdown: str
    sentiment: Optional[dict] = None
    pain_points: list[dict] = Field(default_factory=list)
    selling_points: list[dict] = Field(default_factory=list)
    tips: list[dict] = Field(default_factory=list)
    summary_zh: str = ""
    summary_en: str = ""


class BulletSuggestion(BaseModel):
    """A single bullet point suggestion, with the source pain/selling point
    it addresses so the seller can verify the suggestion is review-grounded."""
    text: str
    addresses: str = Field(
        description="The pain point or selling point this bullet addresses (verbatim from the report)"
    )


class ListingImprovements(BaseModel):
    """Structured listing copy suggestions derived from the VOC report.

    Every suggestion must cite the review evidence it addresses (the
    `addresses` field) so the seller can verify it's grounded in actual
    customer language, not hallucinated.
    """
    title_suggestion: str = Field(
        description="A proposed new product title (max 200 chars per Amazon's limit), incorporating top selling points and key search terms surfaced in the reviews."
    )
    title_reasoning: str = Field(
        description="One sentence on why this title — which pain points it preempts, which selling points it amplifies."
    )
    bullet_suggestions: list[BulletSuggestion] = Field(
        description="5 proposed bullet points. Each bullet should preempt a top pain point or amplify a top selling point. Order by importance."
    )
    description_paragraph: str = Field(
        description="A short product description paragraph (150-250 words) that incorporates the top 3 selling points and addresses the top 2 pain points head-on."
    )
    keyword_opportunities: list[str] = Field(
        description="3-5 search keywords that buyers used in their reviews but are likely missing from the current listing. Pull from review language, not assumptions."
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Any review signals the seller should NOT try to fix via listing copy (e.g., 'product quality complaints can't be solved by better copy — needs a product fix')."
    )
