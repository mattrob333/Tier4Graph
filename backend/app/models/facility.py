# backend/app/models/facility.py

from pydantic import BaseModel


class FacilityBase(BaseModel):
    """Base facility fields."""

    facility_id: str
    vendor_id: str
    geo: str | None = None
    tier: str | None = None
    cooling: str | None = None
    power_density: float | None = None
    address: str | None = None
