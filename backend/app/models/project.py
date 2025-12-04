# backend/app/models/project.py

from pydantic import BaseModel


class ProjectBase(BaseModel):
    """Base project fields."""

    project_id: str
    client_id: str
    name: str | None = None
    timeline: str | None = None
    budget: float | None = None
    go_live_date: str | None = None
