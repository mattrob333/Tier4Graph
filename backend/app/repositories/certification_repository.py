# backend/app/repositories/certification_repository.py

from neo4j import AsyncSession

from app.models import CertificationBase


class CertificationRepository:
    """Repository for Certification node operations in Neo4j."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_certification(self, cert: CertificationBase) -> None:
        """
        MERGE Certification node by cert_id and set all properties.

        Uses MERGE to respect unique constraint on cert_id.
        """
        cypher = """
        MERGE (c:Certification {cert_id: $cert_id})
        SET c.name = $name,
            c.notes = $notes
        """
        await self._session.run(
            cypher,
            cert_id=cert.cert_id,
            name=cert.name,
            notes=cert.notes,
        )

    async def get_certification_by_id(self, cert_id: str) -> CertificationBase | None:
        """
        MATCH Certification by cert_id, return CertificationBase or None if not found.
        """
        cypher = """
        MATCH (c:Certification {cert_id: $cert_id})
        RETURN c.cert_id AS cert_id,
               c.name AS name,
               c.notes AS notes
        """
        result = await self._session.run(cypher, cert_id=cert_id)
        record = await result.single()

        if record is None:
            return None

        return CertificationBase(
            cert_id=record["cert_id"],
            name=record["name"],
            notes=record["notes"],
        )
