"""Pydantic models for Kafka events."""

from datetime import datetime

from pydantic import BaseModel


class IngredientCached(BaseModel):
    """Event published when an ingredient is cached."""

    fdc_id: int
    data: dict
    cached_at: datetime

    def model_dump(self, **kwargs):
        """Override to serialize datetime to ISO string."""
        result = super().model_dump(**kwargs)
        if isinstance(result.get("cached_at"), datetime):
            result["cached_at"] = result["cached_at"].isoformat()
        return result
