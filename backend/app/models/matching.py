# backend/app/models/matching.py

from pydantic import BaseModel


class MatchingRequest(BaseModel):
    """Request schema for structured vendor matching."""

    industry: str | None = None  # matches against primary_segments
    region: str | None = None  # matches against hq_country
    required_certs: list[str] = []  # future use
    required_services: list[str] = []  # future use
    risk_tolerance: int | None = None  # 1-10, filter vendors with risk_score_guess
    text_query: str | None = None  # reserved for semantic search


class ScoreBreakdown(BaseModel):
    """Breakdown of how a vendor's score was calculated."""

    industry: int = 0
    region: int = 0
    certifications: int = 0
    total: int = 0


class MatchVendor(BaseModel):
    """A vendor result from matching with score and reasons."""

    vendor_id: str
    name: str
    score: float
    score_breakdown: ScoreBreakdown | None = None
    matched_reasons: list[str] = []


class MatchResponse(BaseModel):
    """Response schema containing ranked vendor matches."""

    vendors: list[MatchVendor]


class NLMatchRequest(BaseModel):
    """Natural language matching request.

    Accepts a free-form text query describing vendor requirements.
    The query is parsed by an NL parser to extract structured criteria.

    Example queries:
        - "I need a HIPAA-compliant colo in the US East with low risk"
        - "Looking for managed cloud services, preferably SOC 2 certified"
        - "Healthcare data center with Tier III facilities"
    """

    query: str
