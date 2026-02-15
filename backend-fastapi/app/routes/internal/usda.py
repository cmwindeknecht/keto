"""Routes for USDA FoodData Central API integration."""

from fastapi import APIRouter, Query, status

from app.services.usda.models.requests import FoodsByFdcID, FoodsByCriteria
from app.services.usda.models.responses import SearchResultFood
from app.services.usda.usda_service import usda_service

router = APIRouter(
    prefix="/internal/usda",
    tags=["usda"],
)


@router.post(
    "/foods",
    response_model=list[SearchResultFood],
    status_code=status.HTTP_200_OK,
    summary="Get multiple foods by FDC IDs",
)
async def get_multiple_foods(criteria: FoodsByFdcID):
    """Get detailed information for multiple foods by FDC IDs."""
    return await usda_service.search_by_fdcids(criteria)


@router.post(
    "/search",
    response_model=list[SearchResultFood],
    status_code=status.HTTP_200_OK,
    summary="Search for foods by criteria",
)
async def search_foods(criteria: FoodsByCriteria):
    """Search for foods with complex criteria."""
    return await usda_service.search_by_criteria(criteria)


@router.get(
    "/search-ingredients",
    response_model=list[SearchResultFood],
    status_code=status.HTTP_200_OK,
    summary="Search for ingredients",
)
async def search_ingredients(
    query: str = Query(..., description="Ingredient search term"),
    limit: int = Query(20, description="Maximum number of results"),
    include_brands: bool = Query(False, description="Include branded items"),
):
    """
    Search for ingredients with Elasticsearch cache-first strategy.

    Returns full ingredient data with complete nutrient information.
    Pulls from Elasticsearch cache when available, falls back to USDA API for new results.
    """
    return await usda_service.search_ingredients(query, limit, include_brands)
