"""Pydantic models for Kafka events."""

from pydantic import BaseModel
from datetime import datetime


class IngredientCached(BaseModel):
    """Event published when an ingredient is cached."""
    fdc_id: int
    data: dict
    cached_at: datetime
