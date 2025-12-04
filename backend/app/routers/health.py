from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_root() -> dict:
    return {"status": "ok"}


@router.get("/neo4j")
async def neo4j_health(session: AsyncSession = Depends(get_neo4j_session)) -> dict:
    """
    Basic Neo4j connectivity check.

    Runs 'RETURN 1 AS ok' and verifies the result.
    """
    result = await session.run("RETURN 1 AS ok")
    record = await result.single()
    is_ok = bool(record and record["ok"] == 1)
    return {"neo4j_ok": is_ok}
