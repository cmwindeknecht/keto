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
    Stored in Redis with 30-day TTL.
    """
    fdc_id: int
    name: str
    nutrients: list[CachedNutrient]
    brand_owner: Optional[str] = None  # For branded foods
    data_type: str  # "SR Legacy", "Foundation", "Survey", "Branded", "Abridged"

    class Config:
        json_schema_extra = {
            "example": {
                "fdc_id": 534358,
                "name": "Chicken, raw, breast, with skin",
                "nutrients": [
                    {"nutrient_type": "calories", "amount": 165, "unit": "kcal"},
                    {"nutrient_type": "carbs", "amount": 0, "unit": "g"},
                    {"nutrient_type": "protein", "amount": 18.3, "unit": "g"},
                    {"nutrient_type": "fat", "amount": 9.3, "unit": "g"},
                ],
                "data_type": "SR Legacy"
            }
        }
