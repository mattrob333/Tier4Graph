# backend/app/repositories/service_repository.py

from neo4j import AsyncSession

from app.models import ServiceBase


class ServiceRepository:
    """Repository for Service node operations in Neo4j."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_service(self, service: ServiceBase, vendor_id: str | None = None) -> None:
        """
        MERGE Service node by service_id and set all properties.
        If vendor_id provided, also creates OFFERS relationship.

        Uses MERGE to respect unique constraint on service_id.
        """
        if vendor_id:
            # Create service and relationship to vendor
            cypher = """
            MATCH (v:Vendor {vendor_id: $vendor_id})
            MERGE (s:Service {service_id: $service_id})
            SET s.category = $category,
                s.description = $description,
                s.name = $name
            MERGE (v)-[:OFFERS]->(s)
            """
            await self._session.run(
                cypher,
                vendor_id=vendor_id,
                service_id=service.service_id,
                category=service.category,
                description=service.description,
                name=service.description or service.category,  # Use description as name for display
            )
        else:
            cypher = """
            MERGE (s:Service {service_id: $service_id})
            SET s.category = $category,
                s.description = $description
            """
            await self._session.run(
                cypher,
                service_id=service.service_id,
                category=service.category,
                description=service.description,
            )

    async def get_service_by_id(self, service_id: str) -> ServiceBase | None:
        """
        MATCH Service by service_id, return ServiceBase or None if not found.
        """
        cypher = """
        MATCH (s:Service {service_id: $service_id})
        RETURN s.service_id AS service_id,
               s.category AS category,
               s.description AS description
        """
        result = await self._session.run(cypher, service_id=service_id)
        record = await result.single()

        if record is None:
            return None

        return ServiceBase(
            service_id=record["service_id"],
            category=record["category"],
            description=record["description"],
        )
