# backend/app/services/matching_service.py

from neo4j import AsyncSession

from app.models import MatchingRequest, MatchVendor


async def match_vendors(
    request: MatchingRequest, session: AsyncSession
) -> list[MatchVendor]:
    """
    Execute a simple hard-filter + scoring query against Neo4j Vendor nodes.

    Scoring:
    - +1 if request.industry is in vendor's primary_segments
    - +1 if request.region matches vendor's hq_country

    Filtering:
    - Excludes vendors with risk_score_guess > request.risk_tolerance (when specified)
    """
    query = """
    MATCH (v:Vendor)
    WITH v,
         CASE WHEN $industry IS NOT NULL AND $industry IN v.primary_segments THEN 1 ELSE 0 END AS segment_score,
         CASE WHEN $region IS NOT NULL AND v.hq_country = $region THEN 1 ELSE 0 END AS region_score
    WHERE
         ($risk_tolerance IS NULL OR v.risk_score_guess IS NULL OR v.risk_score_guess <= $risk_tolerance)
    RETURN v.vendor_id AS vendor_id,
           v.name AS name,
           (segment_score + region_score) AS score,
           v.hq_country AS hq_country,
           v.primary_segments AS primary_segments
    ORDER BY score DESC, name ASC
    LIMIT 20
    """

    result = await session.run(
        query,
        industry=request.industry,
        region=request.region,
        risk_tolerance=request.risk_tolerance,
    )

    vendors: list[MatchVendor] = []
    async for record in result:
        matched_reasons: list[str] = []

        # Build matched_reasons based on what criteria matched
        if request.industry and record["primary_segments"]:
            if request.industry in record["primary_segments"]:
                matched_reasons.append(f"industry match: {request.industry}")

        if request.region and record["hq_country"]:
            if request.region == record["hq_country"]:
                matched_reasons.append(f"region match: {request.region}")

        vendors.append(
            MatchVendor(
                vendor_id=record["vendor_id"],
                name=record["name"],
                score=float(record["score"]),
                matched_reasons=matched_reasons,
            )
        )

    return vendors
