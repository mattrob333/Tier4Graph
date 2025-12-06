# backend/app/services/matching_service.py

from loguru import logger
from neo4j import AsyncSession

from app.models import MatchingRequest, MatchVendor, ScoreBreakdown


def _substring_match(required: str, actual: str) -> bool:
    """Case-insensitive substring matching with null safety."""
    if not required or not actual:
        return False
    return required.lower() in actual.lower()


def _find_match(required: str, items: list[str]) -> str | None:
    """Find first item that contains required string (case-insensitive)."""
    if not required:
        return None
    for item in items:
        if item and _substring_match(required, item):
            return item
    return None


def _count_matches(required_items: list[str], actual_items: list[str]) -> int:
    """Count how many required items have a match in actual items."""
    count = 0
    for req in required_items:
        if _find_match(req, actual_items):
            count += 1
    return count


def _industry_matches(required_industry: str, vendor_segments: list[str]) -> bool:
    """Check if required industry matches vendor's segments with fuzzy matching."""
    if not required_industry or not vendor_segments:
        return False
    req_lower = required_industry.lower()
    for segment in vendor_segments:
        seg_lower = segment.lower() if segment else ""
        # Direct match
        if req_lower == seg_lower:
            return True
        # Partial match (backup-dr matches backup, dr, disaster-recovery)
        if req_lower in seg_lower or seg_lower in req_lower:
            return True
        # Handle common aliases
        industry_aliases = {
            "backup-dr": ["backup", "disaster-recovery", "dr", "disaster recovery"],
            "backup": ["backup-dr"],
            "disaster-recovery": ["backup-dr", "dr"],
            "network": ["carrier", "fiber", "wavelength", "interconnection"],
            "colocation": ["colo", "data center", "datacenter"],
            "cloud": ["iaas", "paas", "hyperscaler"],
            "security": ["cybersecurity", "soc", "mdr", "siem"],
        }
        if req_lower in industry_aliases:
            for alias in industry_aliases[req_lower]:
                if alias in seg_lower:
                    return True
    return False


def _region_matches(required_region: str, facility_geos: list[str]) -> bool:
    """Check if any facility is in the required region."""
    if not required_region:
        return False
    req_lower = required_region.lower().replace("-", "").replace("_", "")
    for geo in facility_geos:
        geo_lower = (geo.lower() if geo else "").replace("-", "").replace("_", "")
        # Direct match or substring match
        if req_lower in geo_lower or geo_lower in req_lower:
            return True
        # Handle common region variations
        region_aliases = {
            "uswest": ["usw", "west", "california", "oregon", "washington"],
            "useast": ["use", "east", "virginia", "ashburn", "newyork"],
            "uscentral": ["usc", "central", "texas", "dallas", "chicago"],
            "euwest": ["euw", "ireland", "london", "uk", "amsterdam"],
            "eucentral": ["euc", "frankfurt", "germany", "amsterdam"],
            "apac": ["asia", "singapore", "tokyo", "sydney", "hongkong"],
        }
        if req_lower in region_aliases:
            for alias in region_aliases[req_lower]:
                if alias in geo_lower:
                    return True
    return False


def _city_matches(required_city: str, facility_cities: list[str]) -> bool:
    """Check if any facility is in or near the required city."""
    req_lower = required_city.lower()
    for city in facility_cities:
        city_lower = city.lower() if city else ""
        # Direct match or substring match
        if req_lower in city_lower or city_lower in req_lower:
            return True
        # Handle common variations
        city_aliases = {
            "silicon valley": ["san jose", "santa clara", "palo alto", "sunnyvale"],
            "san jose": ["silicon valley"],
            "ashburn": ["virginia", "northern virginia", "nova"],
            "dallas": ["dfw", "fort worth", "plano"],
            "chicago": ["illinois", "il"],
        }
        if req_lower in city_aliases:
            for alias in city_aliases[req_lower]:
                if alias in city_lower:
                    return True
    return False


def _service_matches(required_service: str, service_texts: list[str]) -> str | None:
    """Check if any service matches the required service with keyword matching."""
    if not required_service:
        return None
    req_lower = required_service.lower()
    
    # Service keyword mappings for flexible matching
    service_keywords = {
        "immutable": ["immutable", "worm", "write-once", "air-gap", "unchangeable"],
        "disaster-recovery": ["disaster recovery", "dr", "rto", "rpo", "failover", "recovery"],
        "backup": ["backup", "data protection", "replication"],
        "wavelength": ["wavelength", "wave", "optical", "dwdm", "lambda"],
        "dark-fiber": ["dark fiber", "dark-fiber", "unlit fiber"],
        "colocation": ["colocation", "colo", "rack", "cage", "cabinet"],
        "interconnection": ["interconnect", "cross-connect", "peering"],
        "draas": ["draas", "disaster recovery as a service", "dr-as-a-service"],
    }
    
    # Get keywords for this service type
    keywords = service_keywords.get(req_lower, [req_lower])
    
    for svc in service_texts:
        svc_lower = svc.lower() if svc else ""
        for keyword in keywords:
            if keyword in svc_lower:
                return svc
    return None


async def match_vendors(
    request: MatchingRequest, session: AsyncSession
) -> list[MatchVendor]:
    """
    Execute a comprehensive matching query against Neo4j Vendor nodes.

    Scoring (each +1):
    - Industry: request.industry matches vendor's primary_segments (fuzzy)
    - Region: Each requested region matched by vendor's facilities
    - Certifications: Each required cert the vendor holds
    - Services: Each required service the vendor offers (keyword matching)
    - Locations: Each required city where vendor has facilities

    Filtering:
    - Risk: Excludes vendors with risk_score_guess > threshold
    - Certifications: Must hold ALL required certs (hard filter)
    
    Sorting & Limiting:
    - sort_by: "risk_asc", "score_desc" (default), "name_asc"
    - result_limit: Max number of results to return
    """
    # Normalize inputs for matching
    required_certs_lower = [c.lower() for c in request.required_certs]

    # Determine risk threshold
    # max_risk_score takes precedence over risk_tolerance
    risk_threshold = None
    if request.max_risk_score is not None:
        risk_threshold = request.max_risk_score
    elif request.risk_tolerance is not None:
        risk_threshold = max(0.20, request.risk_tolerance / 10.0)

    logger.info(
        f"match_vendors: industry={request.industry}, regions={request.regions}, "
        f"cities={request.cities}, certs={request.required_certs}, "
        f"services={request.required_services}, risk_threshold={risk_threshold}, "
        f"limit={request.result_limit}, sort={request.sort_by}"
    )

    # Comprehensive query that fetches all related data
    query = """
    MATCH (v:Vendor)
    OPTIONAL MATCH (v)-[:HOLDS]->(c:Certification)
    OPTIONAL MATCH (v)-[:OFFERS]->(s:Service)
    OPTIONAL MATCH (v)-[:HAS_FACILITY]->(f:Facility)
    WITH v,
         collect(DISTINCT c.name) AS held_certs,
         collect(DISTINCT {name: s.name, category: s.category, desc: s.description}) AS services_data,
         collect(DISTINCT {city: f.address, geo: f.geo, tier: f.tier}) AS facilities_data
    
    // Calculate base scores in Cypher
    WITH v, held_certs, services_data, facilities_data,
         CASE WHEN $industry IS NOT NULL AND $industry IN v.primary_segments THEN 1 ELSE 0 END AS segment_score,
         CASE WHEN $region IS NOT NULL AND v.region = $region THEN 1 ELSE 0 END AS region_score,
         // Cert match count (substring matching)
         size([req_cert IN $required_certs_lower WHERE
               size([hc IN held_certs WHERE toLower(hc) CONTAINS req_cert]) > 0
         ]) AS cert_match_count
    
    // Apply filters
    WHERE
        ($risk_threshold IS NULL OR v.risk_score_guess IS NULL OR v.risk_score_guess <= $risk_threshold)
        AND (size($required_certs_lower) = 0 OR cert_match_count = size($required_certs_lower))
    
    RETURN v.vendor_id AS vendor_id,
           v.name AS name,
           v.summary AS summary,
           v.region AS region,
           v.primary_segments AS primary_segments,
           v.risk_score_guess AS risk_score_guess,
           held_certs,
           services_data,
           facilities_data,
           segment_score,
           region_score,
           cert_match_count
    ORDER BY (segment_score + region_score + cert_match_count) DESC, name ASC
    LIMIT 30
    """

    result = await session.run(
        query,
        industry=request.industry,
        region=request.region,
        risk_threshold=risk_threshold,
        required_certs_lower=required_certs_lower,
    )

    vendors: list[MatchVendor] = []
    async for record in result:
        matched_reasons: list[str] = []
        held_certs = record["held_certs"] or []
        services_data = record["services_data"] or []
        facilities_data = record["facilities_data"] or []

        # Extract service names/descriptions and facility geos for matching
        service_texts = []
        for s in services_data:
            if s:
                name = s.get("name", "") or ""
                desc = s.get("desc", "") or ""
                cat = s.get("category", "") or ""
                service_texts.append(f"{name} {desc} {cat}")
        
        # Extract facility geo regions AND city names
        facility_geos = [f.get("geo", "") for f in facilities_data if f and f.get("geo")]
        facility_cities = [f.get("city", "") for f in facilities_data if f and f.get("city")]
        all_facility_locations = facility_geos + facility_cities

        # Calculate detailed scores
        industry_score = 0
        region_score = 0
        cert_score = 0
        service_score = 0
        location_score = 0

        # Industry match - use fuzzy matching
        primary_segments = record["primary_segments"] or []
        if request.industry and _industry_matches(request.industry, primary_segments):
            matched_reasons.append(f"✓ Industry: {request.industry}")
            industry_score = 1

        # Region match - check requested regions against facility geos
        vendor_region = record["region"]
        matched_regions = []
        for region in request.regions:
            if _region_matches(region, facility_geos):
                matched_regions.append(region)
                region_score += 1
            # Also check if vendor's HQ region matches
            elif vendor_region and _region_matches(region, [vendor_region]):
                matched_regions.append(region)
                region_score += 1
            # Global vendors can serve any region (cloud/SaaS providers)
            elif vendor_region == "global":
                matched_regions.append(f"{region}*")  # * indicates via global coverage
                region_score += 1
        if matched_regions:
            matched_reasons.append(f"✓ Regions: {', '.join(matched_regions)}")
        
        # Legacy single-region match (backward compatibility)
        if request.region and vendor_region == request.region:
            if not matched_regions:  # Don't double-count
                matched_reasons.append(f"✓ HQ Region: {request.region}")
                region_score += 1

        # Certification matches
        for cert in request.required_certs:
            matching_cert = _find_match(cert, held_certs)
            if matching_cert:
                matched_reasons.append(f"✓ Certification: {matching_cert}")
                cert_score += 1

        # Service matches - use keyword matching
        for service in request.required_services:
            matching_service = _service_matches(service, service_texts)
            if matching_service:
                # Truncate long service descriptions for display
                display_svc = matching_service[:60] + "..." if len(matching_service) > 60 else matching_service
                matched_reasons.append(f"✓ Service: {display_svc}")
                service_score += 1

        # City/location matches
        matched_cities = []
        for city in request.cities:
            if _city_matches(city, all_facility_locations):
                matched_cities.append(city)
                location_score += 1
        if matched_cities:
            matched_reasons.append(f"✓ Cities: {', '.join(matched_cities)}")

        # Risk info
        vendor_risk = record["risk_score_guess"]
        if risk_threshold is not None and vendor_risk is not None:
            if vendor_risk <= risk_threshold:
                matched_reasons.append(f"✓ Risk: {vendor_risk:.2f} ≤ {risk_threshold:.2f}")

        # Calculate total score
        total_score = industry_score + region_score + cert_score + service_score + location_score

        # Build score breakdown
        breakdown = ScoreBreakdown(
            industry=industry_score,
            region=region_score,
            certifications=cert_score,
            services=service_score,
            locations=location_score,
            total=total_score,
        )

        # Format service and facility lists for display (filter out None values)
        service_list = [s.get("name") or s.get("desc") or s.get("category") for s in services_data if s]
        service_list = [s for s in service_list if s]
        
        facility_list = [f.get("geo") or f.get("city") for f in facilities_data if f]
        facility_list = list(set(f for f in facility_list if f))  # Unique, non-None values
        
        # Filter None from certifications and segments
        clean_certs = [c for c in held_certs if c]
        clean_segments = [s for s in primary_segments if s] if primary_segments else []

        vendors.append(
            MatchVendor(
                vendor_id=record["vendor_id"],
                name=record["name"] or record["vendor_id"],
                score=float(total_score),
                score_breakdown=breakdown,
                matched_reasons=matched_reasons,
                summary=record["summary"],
                region=vendor_region,
                risk_score=vendor_risk,
                primary_segments=clean_segments,
                certifications=clean_certs,
                services=service_list,
                facilities=facility_list,
            )
        )

    # Apply sorting based on request.sort_by
    # Always prioritize score first, then apply secondary sort
    if request.sort_by == "risk_asc":
        # Sort by score DESC first, then by risk ASC for equal scores
        vendors.sort(key=lambda v: (-v.score, v.risk_score if v.risk_score is not None else 999, v.name))
    elif request.sort_by == "name_asc":
        vendors.sort(key=lambda v: (-v.score, v.name))
    else:  # Default: score_desc
        vendors.sort(key=lambda v: (-v.score, v.risk_score if v.risk_score is not None else 999, v.name))
    
    # Apply result limit
    if request.result_limit and request.result_limit > 0:
        vendors = vendors[:request.result_limit]

    logger.info(f"match_vendors returned {len(vendors)} vendors (limit={request.result_limit}, sort={request.sort_by})")
    return vendors
