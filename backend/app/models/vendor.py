# backend/app/models/vendor.py

from pydantic import BaseModel


class VendorBase(BaseModel):
    """Base vendor fields shared across create/read operations."""

    vendor_id: str
    name: str
    summary: str | None = None
    hq_country: str | None = None
    hq_city: str | None = None
    website: str | None = None
    primary_segments: list[str] = []
    typical_customer_profile: str | None = None
    risk_score_guess: float | None = None
    financial_stability_guess: str | None = None
    culture_text: str | None = None


class VendorCreate(VendorBase):
    """Schema for creating a new Vendor node."""

    pass


class VendorRead(VendorBase):
    """Schema for reading a Vendor node from the database."""

    pass
