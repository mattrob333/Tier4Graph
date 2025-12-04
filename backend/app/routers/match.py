# backend/app/routers/match.py

from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session
from app.models import MatchingRequest, MatchResponse
from app.services.matching_service import match_vendors

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
