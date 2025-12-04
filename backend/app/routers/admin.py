# backend/app/routers/admin.py

from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session
from app.db.schema import apply_schema

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/apply-schema")
async def apply_schema_endpoint(
    session: AsyncSession = Depends(get_neo4j_session),
) -> dict:
    """
    Apply Neo4j schema constraints and indexes.

    Idempotent: safe to call multiple times.

    Returns:
        Dictionary with lists of applied constraints and indexes.
    """
    result = await apply_schema(session)
    return result
