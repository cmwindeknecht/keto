"""Pydantic models for USDA API requests."""

from pydantic import BaseModel, Field


class FoodsCriteria(BaseModel):
    """Request body for POST /v1/foods endpoint."""

    fdc_ids: list[int] = Field(..., min_items=1, max_items=20, alias="fdcIds")
    format: str = Field("full", pattern="^(abridged|full)$")
    nutrients: list[int] | None = Field(None, min_items=1, max_items=25)

    class Config:
        populate_by_name = True


class FoodListCriteria(BaseModel):
    """Request body for POST /v1/foods/list endpoint."""

    data_type: list[str] | None = Field(None, alias="dataType")
    page_size: int | None = Field(None, ge=1, le=200, alias="pageSize")
    page_number: int | None = Field(None, alias="pageNumber")
    sort_by: str | None = Field(None, alias="sortBy")
    sort_order: str | None = Field(None, pattern="^(asc|desc)$", alias="sortOrder")

    class Config:
        populate_by_name = True


class FoodSearchCriteria(BaseModel):
    """Request body for POST /v1/foods/search endpoint."""

    query: str
    data_type: list[str] | None = Field(None, alias="dataType")
    page_size: int | None = Field(None, ge=1, le=200, alias="pageSize")
    page_number: int | None = Field(None, alias="pageNumber")
    sort_by: str | None = Field(None, alias="sortBy")
    sort_order: str | None = Field(None, pattern="^(asc|desc)$", alias="sortOrder")
    brand_owner: str | None = Field(None, alias="brandOwner")
    trade_channel: list[str] | None = Field(None, alias="tradeChannel")
    start_date: str | None = Field(None, alias="startDate")
    end_date: str | None = Field(None, alias="endDate")

    class Config:
        populate_by_name = True
