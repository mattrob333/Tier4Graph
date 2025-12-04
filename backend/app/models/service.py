# backend/app/models/service.py

from pydantic import BaseModel


class ServiceBase(BaseModel):
    """Base service fields."""

    service_id: str
    category: str
    description: str | None = None
