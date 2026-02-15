from typing import Optional

from fastapi import APIRouter, Query, status

from app.services.usda.models.requests import (
    FoodsByFdcID,
    FoodListCriteria,
    FoodsByCriteria,
)
from app.services.usda.models.responses import (
    AbridgedFoodItem,
    BrandedFoodItem,
    FoundationFoodItem,
    SRLegacyFoodItem,
    SurveyFoodItem,
    SearchResult,
)
from app.services.usda.usda_service import usda_service

router = APIRouter(
    prefix="/internal/usda",
    tags=["usda"],
)


@router.get(
    "/food/{fdc_id}",
    response_model=AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem,
    status_code=status.HTTP_200_OK,
    summary="Get food details by FDC ID",
)
async def get_food_details(
    fdc_id: int,
    format: str = "full",
    nutrients: Optional[list[int]] = Query(None),
):
    """Get detailed information for a single food by FDC ID."""
    return await usda_service.search_single_detail(fdc_id, format, nutrients)


@router.post(
    "/foods",
    response_model=list[
        AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem
    ],
    status_code=status.HTTP_200_OK,
    summary="Get multiple foods by FDC IDs",
)
async def get_multiple_foods(criteria: FoodsByFdcID):
    """Get detailed information for multiple foods by FDC IDs."""
    return await usda_service.search_multi_detail(criteria)


@router.post(
    "/foods/list",
    response_model=list[AbridgedFoodItem],
    status_code=status.HTTP_200_OK,
    summary="List all foods",
)
async def list_all_foods(criteria: FoodListCriteria):
    """Get a paged list of foods in abridged format."""
    return await usda_service.list_all_foods(criteria)


@router.post(
    "/search",
    response_model=SearchResult,
    status_code=status.HTTP_200_OK,
    summary="Search for foods by query",
)
async def search_foods_query(
    query: str = Query(..., description="Search query string"),
):
    """Search for foods by keywords."""
    return await usda_service.search(query=query)


@router.post(
    "/search/advanced",
    response_model=SearchResult,
    status_code=status.HTTP_200_OK,
    summary="Advanced search for foods",
)
async def search_foods_advanced(criteria: FoodsByCriteria):
    """Advanced search for foods with complex criteria."""
    return await usda_service.search(criteria=criteria)


@router.get(
    "/search-ingredients",
    status_code=status.HTTP_200_OK,
    summary="Search for ingredients",
)
async def search_ingredients(
    query: str = Query(..., description="Ingredient search term"),
    limit: int = Query(20, description="Maximum number of results"),
):
    """Search for ingredients in USDA FoodData Central database."""
    return await usda_service.search_ingredients(query, limit)


@router.get(
    "/ingredient/{fdc_id}",
    status_code=status.HTTP_200_OK,
    summary="Get ingredient details",
)
async def get_ingredient_details(fdc_id: str):
    """Get detailed nutrition information for a specific ingredient."""
    return await usda_service.get_ingredient_details(fdc_id)
