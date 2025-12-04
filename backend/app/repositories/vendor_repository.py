# backend/app/repositories/vendor_repository.py

from neo4j import AsyncSession

from app.models import VendorCreate, VendorRead


class VendorRepository:
    """Repository for Vendor node operations in Neo4j."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_vendor(self, vendor: VendorCreate) -> None:
        """
        MERGE Vendor node by vendor_id and set all properties.

        Uses MERGE to respect unique constraint on vendor_id.
        """
        cypher = """
        MERGE (v:Vendor {vendor_id: $vendor_id})
        SET v.name = $name,
            v.summary = $summary,
            v.hq_country = $hq_country,
            v.hq_city = $hq_city,
            v.website = $website,
            v.primary_segments = $primary_segments,
            v.typical_customer_profile = $typical_customer_profile,
            v.risk_score_guess = $risk_score_guess,
            v.financial_stability_guess = $financial_stability_guess,
            v.culture_text = $culture_text
        """
        await self._session.run(
            cypher,
            vendor_id=vendor.vendor_id,
            name=vendor.name,
            summary=vendor.summary,
            hq_country=vendor.hq_country,
            hq_city=vendor.hq_city,
            website=vendor.website,
            primary_segments=vendor.primary_segments,
            typical_customer_profile=vendor.typical_customer_profile,
            risk_score_guess=vendor.risk_score_guess,
            financial_stability_guess=vendor.financial_stability_guess,
            culture_text=vendor.culture_text,
        )

    async def get_vendor_by_id(self, vendor_id: str) -> VendorRead | None:
        """
        MATCH Vendor by vendor_id, return VendorRead or None if not found.
        """
        cypher = """
        MATCH (v:Vendor {vendor_id: $vendor_id})
        RETURN v.vendor_id AS vendor_id,
               v.name AS name,
               v.summary AS summary,
               v.hq_country AS hq_country,
               v.hq_city AS hq_city,
               v.website AS website,
               v.primary_segments AS primary_segments,
               v.typical_customer_profile AS typical_customer_profile,
               v.risk_score_guess AS risk_score_guess,
               v.financial_stability_guess AS financial_stability_guess,
               v.culture_text AS culture_text
        """
        result = await self._session.run(cypher, vendor_id=vendor_id)
        record = await result.single()

        if record is None:
            return None

        return VendorRead(
            vendor_id=record["vendor_id"],
            name=record["name"],
            summary=record["summary"],
            hq_country=record["hq_country"],
            hq_city=record["hq_city"],
            website=record["website"],
            primary_segments=record["primary_segments"] or [],
            typical_customer_profile=record["typical_customer_profile"],
            risk_score_guess=record["risk_score_guess"],
            financial_stability_guess=record["financial_stability_guess"],
            culture_text=record["culture_text"],
        )
