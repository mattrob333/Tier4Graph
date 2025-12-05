# backend/app/routers/vendor.py

from fastapi import APIRouter, Depends, HTTPException
from neo4j import AsyncSession

from app.db.neo4j import get_neo4j_session
from app.models import VendorCreate, VendorRead
from app.repositories import VendorRepository

router = APIRouter(prefix="/vendors", tags=["vendors"])


@router.post("", response_model=VendorRead)
async def create_or_update_vendor(
    vendor: VendorCreate,
    session: AsyncSession = Depends(get_neo4j_session),
) -> VendorRead:
    """
    Create or update a Vendor node.

    Uses MERGE to upsert by vendor_id, then returns the resulting vendor.
    """
    repo = VendorRepository(session)
    await repo.upsert_vendor(vendor)
    result = await repo.get_vendor_by_id(vendor.vendor_id)
    # result is guaranteed to exist after upsert
    return result  # type: ignore[return-value]


@router.get("/{vendor_id}", response_model=VendorRead)
async def get_vendor(
    vendor_id: str,
    session: AsyncSession = Depends(get_neo4j_session),
) -> VendorRead:
    """
    Get a Vendor by vendor_id.

    Returns 404 if not found.
    """
    repo = VendorRepository(session)
    result = await repo.get_vendor_by_id(vendor_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return result


@router.delete("/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    session: AsyncSession = Depends(get_neo4j_session),
) -> dict:
    """
    Delete a Vendor and all its relationships.

    Returns success message or 404 if not found.
    """
    # First check if vendor exists
    repo = VendorRepository(session)
    result = await repo.get_vendor_by_id(vendor_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Delete vendor and all relationships
    await session.run("""
        MATCH (v:Vendor {vendor_id: $vendor_id})
        OPTIONAL MATCH (v)-[r]-()
        DELETE r, v
    """, vendor_id=vendor_id)
    
    return {"message": f"Vendor {vendor_id} deleted successfully"}
