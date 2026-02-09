"""Pydantic models for USDA API requests."""

from pydantic import BaseModel, Field


class FoodsCriteria(BaseModel):
    """Request body for POST /v1/foods endpoint."""

    fdc_ids: list[int] = Field(
        ...,
        min_items=1,
        max_items=20,
        alias="fdcIds",
        description="List of USDA FoodData Central IDs to retrieve (1-20 IDs per request).",
        examples=[[2706337, 2706340]]
    )
    format: str = Field(
        "full",
        pattern="^(abridged|full)$",
        description="Response format: 'abridged' (basic info) or 'full' (detailed nutrition data)."
    )
    nutrients: list[int] | None = Field(
        None,
        min_items=1,
        max_items=25,
        description="Optional: Specific nutrient numbers to include. If omitted, all nutrients are returned. Examples: 1008 (energy), 1003 (protein), 1004 (fat), 1005 (carbs)."
    )

    class Config:
        populate_by_name = True


class FoodListCriteria(BaseModel):
    """Request body for POST /v1/foods/list endpoint."""

    data_type: list[str] | None = Field(
        None,
        alias="dataType",
        description="Food database types to include. Options: 'Branded', 'Foundation', 'Survey (FNDDS)', 'SR Legacy'. Leave empty to include all types.",
        examples=[["Foundation", "SR Legacy"]]
    )
    page_size: int | None = Field(
        None,
        ge=1,
        le=200,
        alias="pageSize",
        description="Number of results per page (1-200). Default is 50."
    )
    page_number: int | None = Field(
        None,
        alias="pageNumber",
        description="Page number (1-based). Use with pageSize for pagination."
    )
    sort_by: str | None = Field(
        None,
        alias="sortBy",
        description="Field to sort by: 'fdcId', 'publishedDate', 'dataType.keyword', or 'lowercaseDescription.keyword'.",
        examples=["fdcId"]
    )
    sort_order: str | None = Field(
        None,
        pattern="^(asc|desc)$",
        alias="sortOrder",
        description="Sort order: 'asc' (ascending) or 'desc' (descending)."
    )

    class Config:
        populate_by_name = True


class FoodSearchCriteria(BaseModel):
    """Request body for POST /v1/foods/search endpoint."""

    query: str = Field(
        ...,
        description="Search keywords (e.g., 'apple', 'red cabbage', 'chicken breast')."
    )
    data_type: list[str] | None = Field(
        None,
        alias="dataType",
        description="Filter by food database types: 'Branded', 'Foundation', 'Survey (FNDDS)', or 'SR Legacy'.",
        examples=[["Foundation"]]
    )
    page_size: int | None = Field(
        None,
        ge=1,
        le=200,
        alias="pageSize",
        description="Number of results per page (1-200). Default is 50."
    )
    page_number: int | None = Field(
        None,
        alias="pageNumber",
        description="Page number (1-based)."
    )
    sort_by: str | None = Field(
        None,
        alias="sortBy",
        description="Field to sort by: 'fdcId', 'publishedDate', 'dataType.keyword', or 'lowercaseDescription.keyword'.",
        examples=["fdcId"]
    )
    sort_order: str | None = Field(
        None,
        pattern="^(asc|desc)$",
        alias="sortOrder",
        description="Sort order: 'asc' (ascending) or 'desc' (descending)."
    )
    brand_owner: str | None = Field(
        None,
        alias="brandOwner",
        description="Filter by brand owner name (for branded foods only)."
    )
    trade_channel: list[str] | None = Field(
        None,
        alias="tradeChannel",
        description="Filter by trade channel: 'CHILD_NUTRITION_FOOD_PROGRAMS', 'DRUG', 'FOOD_SERVICE', 'GROCERY', 'MASS_MERCHANDISING', 'MILITARY', 'ONLINE', or 'VENDING'.",
        examples=[["GROCERY"]]
    )
    start_date: str | None = Field(
        None,
        alias="startDate",
        description="Filter to foods modified on or after this date (ISO 8601 format: YYYY-MM-DD)."
    )
    end_date: str | None = Field(
        None,
        alias="endDate",
        description="Filter to foods modified on or before this date (ISO 8601 format: YYYY-MM-DD)."
    )

    class Config:
        populate_by_name = True
