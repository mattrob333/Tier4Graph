# backend/app/models/constraint.py

from typing import Any

from pydantic import BaseModel


class ConstraintBase(BaseModel):
    """Base constraint fields."""

    constraint_id: str
    type: str
    description: str | None = None
    parameters: dict[str, Any] | None = None
