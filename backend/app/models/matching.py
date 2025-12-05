# backend/app/models/matching.py

from pydantic import BaseModel


class MatchingRequest(BaseModel):
    """Request schema for structured vendor matching."""

    industry: str | None = None  # matches against primary_segments (e.g., "backup-dr", "network")
    region: str | None = None  # Single region filter for vendor's HQ region
    regions: list[str] = []  # Required facility regions (e.g., ["us-west", "eu-central"])
    required_certs: list[str] = []  # e.g., ["SOC 2", "HIPAA", "ISO 27001"]
    required_services: list[str] = []  # e.g., ["wavelength", "immutable", "disaster-recovery"]
    risk_tolerance: int | None = None  # 1-10 scale, converts to 0.0-1.0 threshold
    max_risk_score: float | None = None  # Direct 0.0-1.0 threshold (overrides risk_tolerance)
    cities: list[str] = []  # Specific cities to match against facility locations
    result_limit: int | None = None  # Max results to return (e.g., "top 2")
    sort_by: str | None = None  # Sort order: "risk_asc", "score_desc", "name_asc"
    text_query: str | None = None  # Original query text for logging/debugging


class ScoreBreakdown(BaseModel):
    """Breakdown of how a vendor's score was calculated."""

    industry: int = 0
    region: int = 0
    certifications: int = 0
    services: int = 0
    locations: int = 0  # Cities/facilities match score
    total: int = 0


class MatchVendor(BaseModel):
    """A vendor result from matching with score and reasons."""

    vendor_id: str
    name: str
    score: float
    score_breakdown: ScoreBreakdown | None = None
    matched_reasons: list[str] = []
    # Additional vendor context for UI display
    summary: str | None = None
    region: str | None = None
    risk_score: float | None = None
    primary_segments: list[str] = []
    certifications: list[str] = []
    services: list[str] = []
    facilities: list[str] = []  # City names from facilities


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
