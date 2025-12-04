# backend/app/models/certification.py

from pydantic import BaseModel


class CertificationBase(BaseModel):
    """Base certification fields."""

    cert_id: str
    name: str
    notes: str | None = None
