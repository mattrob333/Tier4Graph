# backend/app/routers/ingestion.py

from fastapi import APIRouter, Depends
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session
from app.models import FacilityBase, ServiceBase, CertificationBase
from app.repositories import (
    FacilityRepository,
    ServiceRepository,
    CertificationRepository,
)

router = APIRouter(prefix="/ingestion", tags=["ingestion"])


@router.post("/vendors/{vendor_id}/facilities")
async def ingest_facilities(
    vendor_id: str,
    facilities: list[FacilityBase],
    session: AsyncSession = Depends(get_neo4j_session),
) -> dict:
    """
    Ingest facilities for a vendor.

    Override facility.vendor_id to match path vendor_id.
    Returns count of inserted facilities.
    """
    repo = FacilityRepository(session)
    for facility in facilities:
        # Override vendor_id to match path parameter
        facility_with_vendor = FacilityBase(
            facility_id=facility.facility_id,
            vendor_id=vendor_id,
            geo=facility.geo,
            tier=facility.tier,
            cooling=facility.cooling,
            power_density=facility.power_density,
            address=facility.address,
        )
        await repo.upsert_facility(facility_with_vendor)
    return {"inserted": len(facilities)}


@router.post("/vendors/{vendor_id}/services")
async def ingest_services(
    vendor_id: str,
    services: list[ServiceBase],
    session: AsyncSession = Depends(get_neo4j_session),
) -> dict:
    """
    Ingest services for a vendor.

    Creates Service nodes and OFFERS relationships to the Vendor.
    Returns count of inserted services.
    """
    repo = ServiceRepository(session)
    for service in services:
        await repo.upsert_service(service, vendor_id=vendor_id)
    return {"inserted": len(services)}


@router.post("/vendors/{vendor_id}/certifications")
async def ingest_certifications(
    vendor_id: str,
    certifications: list[CertificationBase],
    session: AsyncSession = Depends(get_neo4j_session),
) -> dict:
    """
    Ingest certifications for a vendor.

    Creates Certification nodes and HOLDS relationships to the Vendor.
    Returns count of inserted certifications.
    """
    repo = CertificationRepository(session)
    for cert in certifications:
        await repo.upsert_certification_for_vendor(vendor_id, cert)
    return {"inserted": len(certifications)}
