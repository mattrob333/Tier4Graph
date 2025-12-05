# backend/app/routers/match.py

from fastapi import APIRouter, Depends
from loguru import logger
from neo4j import AsyncSession

from app.core.config import settings
from app.db.neo4j import get_neo4j_session
from app.models import MatchingRequest, MatchResponse, NLMatchRequest
from app.services.matching_service import match_vendors
from app.services.nl_parser_service import get_nl_parser

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/structured", response_model=MatchResponse)
async def match_structured(
    request: MatchingRequest,
    session: AsyncSession = Depends(get_neo4j_session),
) -> MatchResponse:
    """
    Run a structured matching query against Neo4j.

    Accepts criteria like industry, region, and risk_tolerance to filter
    and rank vendors. Returns a list of matched vendors with scores.
    """
    vendors = await match_vendors(request, session)
    return MatchResponse(vendors=vendors)


@router.post("/nl", response_model=MatchResponse)
async def match_nl(
    nl_request: NLMatchRequest,
    session: AsyncSession = Depends(get_neo4j_session),
) -> MatchResponse:
    """
    Run a natural language matching query against Neo4j.

    Accepts a free-form text query describing vendor requirements.
    The query is parsed to extract structured criteria (industry, region,
    certifications, services, risk tolerance) which are then used to
    filter and rank vendors.

    Example queries:
        - "I need a HIPAA-compliant colo in the US East with low risk"
        - "Looking for managed cloud services, preferably SOC 2 certified"
        - "Healthcare data center with Tier III facilities"

    The parsing is done by an NL parser which may be:
        - MockNLParser: Rule-based keyword extraction (default, no API keys needed)
        - OpenAINLParser: GPT-backed extraction (when configured)
        - AnthropicNLParser: Claude-backed extraction (when configured)
    """
    logger.info(f"Received NL match request: {nl_request.query[:100]}...")

    # Get the appropriate NL parser based on configuration
    parser = get_nl_parser(settings)

    # Parse natural language into structured MatchingRequest
    matching_request = await parser.parse(nl_request.query)

    # Log the full parsed request for debugging and future LLM tuning
    logger.info(f"NL parsed request: {matching_request.model_dump()}")

    # Execute matching with the structured request
    vendors = await match_vendors(matching_request, session)

    logger.info(f"NL match returned {len(vendors)} vendors")

    return MatchResponse(vendors=vendors)
