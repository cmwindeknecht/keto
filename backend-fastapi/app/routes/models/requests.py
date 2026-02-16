from typing import Optional

from pydantic import BaseModel, Field

from app.db.models import Cuisine
from app.services.usda.models.requests import FoodsByFdcID, FoodsByCriteria


# Recipe Route Models
class RecipeIngredientInput(BaseModel):
    """Input for adding an ingredient to a recipe."""

    usda_fdc_id: int = Field(..., description="USDA FoodData Central ID of the ingredient")
    quantity_grams: float = Field(..., gt=0, description="Quantity of ingredient in grams")


class RecipeCreate(BaseModel):
    """Request to create a new recipe."""

    name: str = Field(..., min_length=1, description="Recipe name")
    cuisine: Cuisine = Field(..., description="Cuisine type")
    description: Optional[str] = Field(None, description="Recipe description")
    ingredients: list[RecipeIngredientInput] = Field(default=[], description="List of ingredients with quantities")


class RecipeUpdate(BaseModel):
    """Request to update an existing recipe."""

    name: Optional[str] = Field(None, min_length=1, description="Recipe name")
    cuisine: Optional[Cuisine] = Field(None, description="Cuisine type")
    description: Optional[str] = Field(None, description="Recipe description")


class SearchIngredientsRequest(BaseModel):
    """Request to search for ingredients in USDA database."""

    query: str = Field(..., min_length=1, description="Ingredient name or keyword to search")
    data_type: Optional[list[str]] = Field(
        None,
        description="Filter by data type: Foundation, SR Legacy, Survey (FNDDS), Branded"
    )
    brand_owner: Optional[str] = Field(None, description="Filter by brand owner name (for branded foods)")
    trade_channel: Optional[list[str]] = Field(
        None,
        description="Filter by trade channel: CHILD_NUTRITION_FOOD_PROGRAMS, GROCERY, etc."
    )
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")
