from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import Cuisine


class IngredientResponse(BaseModel):
    """Ingredient response model with nutrition information."""

    id: int = Field(..., description="Database ID")
    usda_fdc_id: str = Field(..., description="USDA FoodData Central ID")
    name: str = Field(..., description="Ingredient name")
    calories_per_100g: float = Field(..., description="Calories per 100g")
    protein_per_100g: float = Field(..., description="Protein (g) per 100g")
    fat_per_100g: float = Field(..., description="Fat (g) per 100g")
    carbs_per_100g: float = Field(..., description="Carbs (g) per 100g")
    fiber_per_100g: float = Field(..., description="Fiber (g) per 100g")

    class Config:
        from_attributes = True


class RecipeIngredientResponse(BaseModel):
    """Ingredient with quantity and calculated nutrition for a recipe."""

    ingredient: IngredientResponse = Field(..., description="Ingredient details")
    quantity_grams: float = Field(..., description="Quantity in grams")
    calories: float = Field(..., description="Total calories for this quantity")
    protein: float = Field(..., description="Total protein (g) for this quantity")
    fat: float = Field(..., description="Total fat (g) for this quantity")
    carbs: float = Field(..., description="Total carbs (g) for this quantity")
    fiber: float = Field(..., description="Total fiber (g) for this quantity")


class RecipeResponse(BaseModel):
    """Recipe response model with ingredients and totals."""

    id: int = Field(..., description="Database ID")
    name: str = Field(..., description="Recipe name")
    cuisine: Cuisine = Field(..., description="Cuisine type")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: list[RecipeIngredientResponse] = Field(..., description="Recipe ingredients with nutrition")
    total_calories: float = Field(..., description="Total calories in recipe")
    total_protein: float = Field(..., description="Total protein (g) in recipe")
    total_fat: float = Field(..., description="Total fat (g) in recipe")
    total_carbs: float = Field(..., description="Total carbs (g) in recipe")
    total_fiber: float = Field(..., description="Total fiber (g) in recipe")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class SearchIngredientsResponse(BaseModel):
    """Response from searching ingredients in USDA database."""

    results: list[IngredientResponse] = Field(..., description="List of matching ingredients")
    total: int = Field(..., description="Total number of results found")
