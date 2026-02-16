"""Pydantic models for USDA API requests."""

from pydantic import BaseModel, Field


class FoodsByFdcID(BaseModel):
    """Request body for POST /v1/foods endpoint."""

    fdc_ids: list[int] = Field(
        ...,
        min_items=1,
        max_items=20,
        alias="fdcIds",
        description="List of USDA FoodData Central IDs to retrieve (1-20 IDs per request).",
        examples=[[2706337, 2706340]],
    )
    format: str = Field(
        "full", pattern="^(abridged|full)$", description="Response format: 'abridged' (basic info) or 'full' (detailed nutrition data)."
    )

    class Config:
        populate_by_name = True


class FoodsByCriteria(BaseModel):
    """Request body for POST /v1/foods/search endpoint."""

    query: str = Field(..., description="Search keywords (e.g., 'apple', 'red cabbage', 'chicken breast').")
    data_type: list[str] | None = Field(
        None,
        alias="dataType",
        description="Filter by food database types: 'Branded', 'Foundation', 'Survey (FNDDS)', or 'SR Legacy'.",
        examples=[["Foundation"]],
    )
    brand_owner: str | None = Field(None, alias="brandOwner", description="Filter by brand owner name (for branded foods only).")
    page_size: int | None = Field(200, ge=1, le=200, alias="pageSize", description="Number of results per page (1-200). Default is 200.")
    page_number: int | None = Field(None, alias="pageNumber", description="Page number (1-based).")
    sort_by: str | None = Field(
        None,
        alias="sortBy",
        description="Field to sort by: 'fdcId', 'publishedDate', 'dataType.keyword', or 'lowercaseDescription.keyword'.",
        examples=["fdcId"],
    )
    sort_order: str | None = Field(
        None, pattern="^(asc|desc)$", alias="sortOrder", description="Sort order: 'asc' (ascending) or 'desc' (descending)."
    )

    class Config:
        populate_by_name = True
