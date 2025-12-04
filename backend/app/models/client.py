# backend/app/models/client.py

from pydantic import BaseModel


class ClientBase(BaseModel):
    """Base client fields."""

    client_id: str
    name: str
    industry: str | None = None
    revenue: float | None = None
    risk_tolerance: int | None = None  # 1-10 scale
    need_text: str | None = None
