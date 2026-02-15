from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import Cuisine


class NutrientInfo(BaseModel):
    """Single nutrient with amount and unit."""

    name: str = Field(..., description="Nutrient name (e.g., 'Protein', 'Total lipid (fat)')")
    amount: float = Field(..., description="Amount of nutrient")
    unit: str = Field(..., description="Unit of measurement (e.g., 'g', 'kcal')")


class IngredientResponse(BaseModel):
    """Ingredient response model with per-100g nutrition information."""

    usda_fdc_id: int = Field(..., description="USDA FoodData Central ID")
    name: str = Field(..., description="Ingredient name")
    data_type: Optional[str] = Field(None, description="Data type: Foundation, SR Legacy, Survey (FNDDS), Branded")
    brand_owner: Optional[str] = Field(None, description="Brand owner (for branded foods)")
    nutrients: list[NutrientInfo] = Field(..., description="All nutrients per 100g")


class RecipeIngredientResponse(BaseModel):
    """Ingredient with quantity and scaled nutrition for a recipe."""

    id: int = Field(..., description="RecipeIngredient ID for deletion")
    ingredient: IngredientResponse = Field(..., description="Ingredient details (per 100g)")
    quantity_grams: float = Field(..., description="Quantity in grams")
    nutrients: list[NutrientInfo] = Field(..., description="Scaled nutrients for this quantity")


class RecipeResponse(BaseModel):
    """Recipe response model with ingredients and complete nutrient breakdown."""

    id: int = Field(..., description="Database ID")
    name: str = Field(..., description="Recipe name")
    cuisine: Cuisine = Field(..., description="Cuisine type")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: list[RecipeIngredientResponse] = Field(..., description="Recipe ingredients with nutrition")
    nutrients: list[NutrientInfo] = Field(..., description="Total nutrients summed across all ingredients")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SearchIngredientsResponse(BaseModel):
    """Response from searching ingredients in USDA database."""

    results: list[IngredientResponse] = Field(..., description="List of matching ingredients")
    total: int = Field(..., description="Total number of results found")
