"""Pydantic models for Elasticsearch operations."""

from pydantic import BaseModel


class IngredientSearchResult(BaseModel):
    """Search result from Elasticsearch."""
    fdc_id: int
    name: str
    data_type: str
