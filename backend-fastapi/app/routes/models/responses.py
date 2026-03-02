from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import Cuisine


# Recipe Route Response Models
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

    model_config = ConfigDict(from_attributes=True)


class SearchIngredientsResponse(BaseModel):
    """Response from searching ingredients in USDA database."""

    results: list[IngredientResponse] = Field(..., description="List of matching ingredients")
    total: int = Field(..., description="Total number of results found")


# USDA Route Response Models
class MeasureUnit(BaseModel):
    """Unit of measure for a food portion (e.g. cup, tablespoon, leaf)."""

    id: Optional[int] = None
    name: Optional[str] = None
    abbreviation: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class FoodPortion(BaseModel):
    """A named serving size with gram weight."""

    id: Optional[int] = None
    amount: Optional[float] = None
    gram_weight: Optional[float] = Field(None, alias="gramWeight")
    portion_description: Optional[str] = Field(None, alias="portionDescription")
    modifier: Optional[str] = None
    measure_unit: Optional[MeasureUnit] = Field(None, alias="measureUnit")

    model_config = ConfigDict(populate_by_name=True)


class SearchResultFood(BaseModel):
    """Food item in search results."""

    fdc_id: int = Field(..., alias="fdcId", description="USDA FoodData Central ID")
    data_type: Optional[str] = Field(None, alias="dataType", description="Food data type")
    description: str = Field(..., description="Food description")
    food_nutrients: Optional[list] = Field(None, alias="foodNutrients", description="Nutrient information")
    publication_date: Optional[str] = Field(None, alias="publicationDate", description="Publication date")
    brand_owner: Optional[str] = Field(None, alias="brandOwner", description="Brand owner")
    gtin_upc: Optional[str] = Field(None, alias="gtinUpc", description="GTIN/UPC code")
    ingredients: Optional[str] = Field(None, description="Ingredients list")
    ndb_number: Optional[int] = Field(None, alias="ndbNumber", description="NDB number")
    score: Optional[float] = Field(None, description="Search relevance score")
    food_portions: Optional[list[FoodPortion]] = Field(None, alias="foodPortions", description="Named serving sizes")
    serving_size: Optional[float] = Field(None, alias="servingSize", description="Serving size value (branded foods)")
    serving_size_unit: Optional[str] = Field(None, alias="servingSizeUnit", description="Serving size unit (branded foods)")
    household_serving_full_text: Optional[str] = Field(
        None, alias="householdServingFullText", description="Human-readable serving description (branded foods, e.g. '1 tablespoon')"
    )

    model_config = ConfigDict(populate_by_name=True)
