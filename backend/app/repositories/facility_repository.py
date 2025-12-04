# backend/app/repositories/facility_repository.py

from neo4j import AsyncSession

from app.models import FacilityBase


class FacilityRepository:
    """Repository for Facility node operations in Neo4j."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_facility(self, facility: FacilityBase) -> None:
        """
        MERGE Facility node by facility_id and set all properties.

        Uses MERGE to respect unique constraint on facility_id.
        """
        cypher = """
        MERGE (f:Facility {facility_id: $facility_id})
        SET f.vendor_id = $vendor_id,
            f.geo = $geo,
            f.tier = $tier,
            f.cooling = $cooling,
            f.power_density = $power_density,
            f.address = $address
        """
        await self._session.run(
            cypher,
            facility_id=facility.facility_id,
            vendor_id=facility.vendor_id,
            geo=facility.geo,
            tier=facility.tier,
            cooling=facility.cooling,
            power_density=facility.power_density,
            address=facility.address,
        )

    async def get_facility_by_id(self, facility_id: str) -> FacilityBase | None:
        """
        MATCH Facility by facility_id, return FacilityBase or None if not found.
        """
        cypher = """
        MATCH (f:Facility {facility_id: $facility_id})
        RETURN f.facility_id AS facility_id,
               f.vendor_id AS vendor_id,
               f.geo AS geo,
               f.tier AS tier,
               f.cooling AS cooling,
               f.power_density AS power_density,
               f.address AS address
        """
        result = await self._session.run(cypher, facility_id=facility_id)
        record = await result.single()

        if record is None:
            return None

        return FacilityBase(
            facility_id=record["facility_id"],
            vendor_id=record["vendor_id"],
            geo=record["geo"],
            tier=record["tier"],
            cooling=record["cooling"],
            power_density=record["power_density"],
            address=record["address"],
        )
