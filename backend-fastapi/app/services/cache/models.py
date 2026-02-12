"""Cache models for storing ingredient data from USDA in Redis."""

from typing import Optional
from pydantic import BaseModel


class CachedNutrient(BaseModel):
    """Nutrient value for a cached ingredient (per 100g)."""
    nutrient_type: str  # e.g., "carbs", "fiber", "protein"
    amount: float
    unit: str  # "g", "mg", "iu", etc.


class CachedIngredient(BaseModel):
    """
    Ingredient data cached from USDA (per 100g).

    All nutrient values are standardized to per-100g basis.
    Stored in Redis as JSON with 30-day TTL.
    """
    fdc_id: int
    name: str
    nutrients: list[CachedNutrient]
    brand_owner: Optional[str] = None  # For branded foods
    data_type: str  # "SR Legacy", "Foundation", "Survey", "Branded", "Abridged"
