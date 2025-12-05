# backend/app/services/matching_service.py

from loguru import logger
from neo4j import AsyncSession

from app.models import MatchingRequest, MatchVendor, ScoreBreakdown


def _cert_matches(required_cert: str, held_cert: str) -> bool:
    """
    Check if a held certification matches a required certification.

    Uses case-insensitive substring matching:
    - "SOC 2" matches "SOC 2 Type II"
    - "hipaa" matches "HIPAA"
    - "iso 27001" matches "ISO 27001"
    """
    return required_cert.lower() in held_cert.lower()


def _count_cert_matches(required_certs: list[str], held_certs: list[str]) -> int:
    """
    Count how many required certs are matched by held certs.

    Each required cert is matched if ANY held cert contains it (case-insensitive).
    Returns count of matched required certs.
    """
    count = 0
    for req_cert in required_certs:
        for held_cert in held_certs:
            if _cert_matches(req_cert, held_cert):
                count += 1
                break  # Found a match for this required cert, move to next
    return count


def _find_matching_cert(required_cert: str, held_certs: list[str]) -> str | None:
    """
    Find the first held cert that matches the required cert.

    Returns the actual cert name (e.g., "SOC 2 Type II") or None if no match.
    """
    for held_cert in held_certs:
        if _cert_matches(required_cert, held_cert):
            return held_cert
    return None


async def match_vendors(
    request: MatchingRequest, session: AsyncSession
) -> list[MatchVendor]:
    """
    Execute a hard-filter + scoring query against Neo4j Vendor nodes.

    Scoring:
    - +1 if request.industry is in vendor's primary_segments
    - +1 if request.region matches vendor's region
    - +1 for each required_cert the vendor holds (via HOLDS relationship)

    Filtering:
    - Excludes vendors with risk_score_guess > request.risk_tolerance (when specified)
    - Excludes vendors missing ANY required_certs (hard filter, not soft score)

    Certification matching uses case-insensitive substring matching:
    - "SOC 2" matches vendors with "SOC 2 Type II" or "SOC 2 Type I"
    - "hipaa" matches vendors with "HIPAA"

    Returns vendors with matched_reasons explaining why each vendor matched:
    - "industry match: <value>"
    - "region match: <value>"
    - "risk within tolerance: <vendor_risk> <= <tolerance>"
    - "holds certification: <cert_name>"
    """
    # Build certification matching clause
    # If required_certs is provided, we filter to vendors that HOLD all of them
    # and also score based on how many they hold
    has_cert_filter = len(request.required_certs) > 0

    # Normalize required certs to lowercase for matching
    required_certs_lower = [c.lower() for c in request.required_certs]

    if has_cert_filter:
        # Query that joins certifications and does substring matching in Cypher
        # Uses toLower() and CONTAINS for case-insensitive substring matching
        query = """
        MATCH (v:Vendor)
        OPTIONAL MATCH (v)-[:HOLDS]->(c:Certification)
        WITH v, collect(c.name) AS held_certs
        WITH v, held_certs,
             CASE WHEN $industry IS NOT NULL AND $industry IN v.primary_segments THEN 1 ELSE 0 END AS segment_score,
             CASE WHEN $region IS NOT NULL AND v.region = $region THEN 1 ELSE 0 END AS region_score,
             size([req_cert IN $required_certs_lower WHERE
                   size([hc IN held_certs WHERE toLower(hc) CONTAINS req_cert]) > 0
             ]) AS cert_match_count
        WHERE
             ($risk_tolerance IS NULL OR v.risk_score_guess IS NULL OR v.risk_score_guess <= $risk_tolerance)
             AND cert_match_count = size($required_certs_lower)
        RETURN v.vendor_id AS vendor_id,
               v.name AS name,
               (segment_score + region_score + cert_match_count) AS score,
               v.region AS region,
               v.primary_segments AS primary_segments,
               v.risk_score_guess AS risk_score_guess,
               held_certs
        ORDER BY score DESC, name ASC
        LIMIT 20
        """
    else:
        # Original query without certification filtering (but still collect held certs for display)
        query = """
        MATCH (v:Vendor)
        OPTIONAL MATCH (v)-[:HOLDS]->(c:Certification)
        WITH v, collect(c.name) AS held_certs
        WITH v, held_certs,
             CASE WHEN $industry IS NOT NULL AND $industry IN v.primary_segments THEN 1 ELSE 0 END AS segment_score,
             CASE WHEN $region IS NOT NULL AND v.region = $region THEN 1 ELSE 0 END AS region_score
        WHERE
             ($risk_tolerance IS NULL OR v.risk_score_guess IS NULL OR v.risk_score_guess <= $risk_tolerance)
        RETURN v.vendor_id AS vendor_id,
               v.name AS name,
               (segment_score + region_score) AS score,
               v.region AS region,
               v.primary_segments AS primary_segments,
               v.risk_score_guess AS risk_score_guess,
               held_certs
        ORDER BY score DESC, name ASC
        LIMIT 20
        """

    # Convert risk_tolerance to float for comparison (it's 1-10 scale, risk_score_guess is 0-1)
    # Risk tolerance mapping:
    #   1 = very conservative (<=0.20)
    #   3 = low risk (<=0.30)
    #   5 = medium risk (<=0.50)
    #   7 = higher risk (<=0.70)
    #   10 = any risk (<=1.0)
    risk_threshold = None
    if request.risk_tolerance is not None:
        # More generous mapping: risk_tolerance * 0.1 with a minimum floor
        # This allows risk_tolerance=1 to still match vendors with risk_score up to 0.20
        risk_threshold = max(0.20, request.risk_tolerance / 10.0)

    logger.debug(
        f"match_vendors: industry={request.industry}, region={request.region}, "
        f"required_certs={request.required_certs}, "
        f"risk_tolerance={request.risk_tolerance} -> threshold={risk_threshold}"
    )

    result = await session.run(
        query,
        industry=request.industry,
        region=request.region,
        risk_tolerance=risk_threshold,
        required_certs_lower=required_certs_lower,
    )

    vendors: list[MatchVendor] = []
    async for record in result:
        matched_reasons: list[str] = []
        held_certs = record["held_certs"] or []

        # Track score breakdown
        industry_score = 0
        region_score = 0
        cert_score = 0

        # Build matched_reasons based on what criteria matched

        # Industry match
        if request.industry and record["primary_segments"]:
            if request.industry in record["primary_segments"]:
                matched_reasons.append(f"industry match: {request.industry}")
                industry_score = 1

        # Region match
        if request.region and record["region"]:
            if request.region == record["region"]:
                matched_reasons.append(f"region match: {request.region}")
                region_score = 1

        # Certification matches (case-insensitive substring)
        for cert in request.required_certs:
            matching_cert = _find_matching_cert(cert, held_certs)
            if matching_cert:
                matched_reasons.append(f"holds certification: {matching_cert}")
                cert_score += 1

        # Risk within tolerance
        vendor_risk = record["risk_score_guess"]
        if risk_threshold is not None and vendor_risk is not None:
            matched_reasons.append(
                f"risk within tolerance: {vendor_risk:.2f} <= {risk_threshold:.2f}"
            )

        # Build score breakdown
        breakdown = ScoreBreakdown(
            industry=industry_score,
            region=region_score,
            certifications=cert_score,
            total=industry_score + region_score + cert_score,
        )

        vendors.append(
            MatchVendor(
                vendor_id=record["vendor_id"],
                name=record["name"],
                score=float(record["score"]),
                score_breakdown=breakdown,
                matched_reasons=matched_reasons,
            )
        )

    logger.debug(f"match_vendors returned {len(vendors)} vendors")
    return vendors
