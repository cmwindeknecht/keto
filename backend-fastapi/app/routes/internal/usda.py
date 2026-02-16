"""Routes for USDA FoodData Central API integration."""

from fastapi import APIRouter, status

from app.routes.models.requests import FoodsByCriteria, FoodsByFdcID
from app.routes.models.responses import SearchResultFood
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
    """
    Search for foods with Elasticsearch cache-first strategy.

    Flow:
    1. Query Elasticsearch for matching ingredients (fuzzy search)
    2. Check Redis cache for those FDC IDs
    3. For missing results, query USDA API
    4. Cache new results and publish to Kafka for ES indexing
    5. Return merged results with complete nutrient data
    """
    return await usda_service.search_by_criteria(criteria)
