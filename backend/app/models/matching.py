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


class MatchVendor(BaseModel):
    """A vendor result from matching with score and reasons."""

    vendor_id: str
    name: str
    score: float
    matched_reasons: list[str] = []


class MatchResponse(BaseModel):
    """Response schema containing ranked vendor matches."""

    vendors: list[MatchVendor]
