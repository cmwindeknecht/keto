"""Pydantic models for USDA API responses."""

from pydantic import BaseModel, Field


class Nutrient(BaseModel):
    """Nutrient information. Always nested within FoodNutrient.nutrient."""

    id: int | None = None
    number: str | None = None
    name: str | None = None
    rank: int | None = None
    unit_name: str | None = Field(None, alias="unitName")

    class Config:
        populate_by_name = True


class AbridgedFoodNutrient(BaseModel):
    """
    Simplified nutrient information.

    Returned by:
    - GET /v1/food/{fdcId} (with format=abridged)
    - GET/POST /v1/foods (with format=abridged)
    - GET/POST /v1/foods/list
    - GET/POST /v1/foods/search (in SearchResultFood items)
    """

    number: int | None = None
    name: str | None = None
    amount: float | None = None
    unit_name: str | None = Field(None, alias="unitName")
    derivation_code: str | None = Field(None, alias="derivationCode")
    derivation_description: str | None = Field(None, alias="derivationDescription")

    class Config:
        populate_by_name = True


class FoodNutrientDerivation(BaseModel):
    """
    Nutrient derivation metadata.

    Always nested within FoodNutrient.food_nutrient_derivation.
    Describes how a nutrient value was derived (e.g., calculated, measured).
    """

    id: int | None = None
    code: str | None = None
    description: str | None = None

    class Config:
        populate_by_name = True


class FoodNutrient(BaseModel):
    """
    Detailed nutrient information with statistical data.

    Always nested within full food items (BrandedFoodItem, FoundationFoodItem, SRLegacyFoodItem, SurveyFoodItem).
    Includes min/max/median values and derivation information.
    """

    id: int | None = None
    amount: float | None = None
    data_points: int | None = Field(None, alias="dataPoints")
    min: float | None = None
    max: float | None = None
    median: float | None = None
    type: str | None = None
    nutrient: Nutrient | None = None
    food_nutrient_derivation: FoodNutrientDerivation | None = Field(None, alias="foodNutrientDerivation")

    class Config:
        populate_by_name = True


class FoodCategory(BaseModel):
    """
    Food category information.

    Always nested within FoundationFoodItem.food_category.
    """

    id: int | None = None
    code: str | None = None
    description: str | None = None


class FoodPortion(BaseModel):
    """
    Food portion/serving information.

    Always nested within FoundationFoodItem.food_portions or SurveyFoodItem.food_portions.
    """

    id: int | None = None
    amount: float | None = None
    gram_weight: float | None = Field(None, alias="gramWeight")
    portion_description: str | None = Field(None, alias="portionDescription")

    class Config:
        populate_by_name = True


class AbridgedFoodItem(BaseModel):
    """
    Minimal food item with basic information.

    Returned by:
    - GET /v1/food/{fdcId} (with format=abridged)
    - GET/POST /v1/foods (with format=abridged)
    - GET/POST /v1/foods/list

    Contains only essential fields and abridged nutrient data.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str = Field(..., alias="dataType")
    description: str
    food_nutrients: list[AbridgedFoodNutrient] | None = Field(None, alias="foodNutrients")
    publication_date: str | None = Field(None, alias="publicationDate")
    brand_owner: str | None = Field(None, alias="brandOwner")
    gtin_upc: str | None = Field(None, alias="gtinUpc")
    ndb_number: int | None = Field(None, alias="ndbNumber")
    food_code: str | None = Field(None, alias="foodCode")

    class Config:
        populate_by_name = True


class BrandedFoodItem(BaseModel):
    """
    Branded food item with comprehensive nutrition data.

    Returned by:
    - GET /v1/food/{fdcId} (if the food is a Branded food)
    - GET/POST /v1/foods (if the food is a Branded food, with format=full or default)

    Contains detailed nutrient information, serving sizes, and brand information.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str = Field(..., alias="dataType")
    description: str
    brand_owner: str | None = Field(None, alias="brandOwner")
    gtin_upc: str | None = Field(None, alias="gtinUpc")
    serving_size: float | None = Field(None, alias="servingSize")
    serving_size_unit: str | None = Field(None, alias="servingSizeUnit")
    food_nutrients: list[FoodNutrient] | None = Field(None, alias="foodNutrients")
    ingredients: str | None = None
    branded_food_category: str | None = Field(None, alias="brandedFoodCategory")

    class Config:
        populate_by_name = True


class FoundationFoodItem(BaseModel):
    """
    Foundation food item with comprehensive nutrition and portion data.

    Returned by:
    - GET /v1/food/{fdcId} (if the food is a Foundation food)
    - GET/POST /v1/foods (if the food is a Foundation food, with format=full or default)

    Contains detailed nutrient information, portion sizes, and food category.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str = Field(..., alias="dataType")
    description: str
    ndb_number: int | None = Field(None, alias="ndbNumber")
    scientific_name: str | None = Field(None, alias="scientificName")
    food_nutrients: list[FoodNutrient] | None = Field(None, alias="foodNutrients")
    food_category: FoodCategory | None = Field(None, alias="foodCategory")
    food_portions: list[FoodPortion] | None = Field(None, alias="foodPortions")

    class Config:
        populate_by_name = True


class SRLegacyFoodItem(BaseModel):
    """
    SR Legacy food item with comprehensive nutrition data.

    Returned by:
    - GET /v1/food/{fdcId} (if the food is an SR Legacy food)
    - GET/POST /v1/foods (if the food is an SR Legacy food, with format=full or default)

    Legacy food database item with detailed nutrient information.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str = Field(..., alias="dataType")
    description: str
    ndb_number: int | None = Field(None, alias="ndbNumber")
    scientific_name: str | None = Field(None, alias="scientificName")
    food_nutrients: list[FoodNutrient] | None = Field(None, alias="foodNutrients")

    class Config:
        populate_by_name = True


class SurveyFoodItem(BaseModel):
    """
    Survey (FNDDS) food item with comprehensive nutrition data.

    Returned by:
    - GET /v1/food/{fdcId} (if the food is a Survey food)
    - GET/POST /v1/foods (if the food is a Survey food, with format=full or default)

    Food from the USDA Automated Multiple-Pass Method Survey (FNDDS) with detailed nutrient information.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str = Field(..., alias="dataType")
    description: str
    food_code: str | None = Field(None, alias="foodCode")
    food_nutrients: list[FoodNutrient] | None = Field(None, alias="foodNutrients")

    class Config:
        populate_by_name = True


class SearchResultFood(BaseModel):
    """
    Simplified food item returned in search results.

    Always nested within SearchResult.foods.
    Contains minimal information optimized for search result display.
    """

    fdc_id: int = Field(..., alias="fdcId")
    data_type: str | None = Field(None, alias="dataType")
    description: str
    food_nutrients: list[AbridgedFoodNutrient] | None = Field(None, alias="foodNutrients")
    publication_date: str | None = Field(None, alias="publicationDate")
    brand_owner: str | None = Field(None, alias="brandOwner")
    gtin_upc: str | None = Field(None, alias="gtinUpc")
    ingredients: str | None = None
    ndb_number: int | None = Field(None, alias="ndbNumber")
    score: float | None = None

    class Config:
        populate_by_name = True


class SearchResult(BaseModel):
    """
    Search results response.

    Returned by:
    - GET /v1/foods/search
    - POST /v1/foods/search

    Contains paginated results with search metadata.
    """

    total_hits: int = Field(..., alias="totalHits")
    current_page: int | None = Field(None, alias="currentPage")
    total_pages: int | None = Field(None, alias="totalPages")
    foods: list[SearchResultFood]

    class Config:
        populate_by_name = True
