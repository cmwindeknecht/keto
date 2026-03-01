"""Routes for USDA FoodData Central API integration."""

from fastapi import APIRouter, status

from app.routes.models.requests import FoodsByCriteria as RouteFoodsByCriteria
from app.routes.models.requests import FoodsByFdcID as RouteFoodsByFdcID
from app.routes.models.responses import SearchResultFood
from app.routes.outbound_rate_limiter import OutboundRateLimiter
from app.services.usda.models.requests import FoodsByCriteria as ServiceFoodsByCriteria
from app.services.usda.models.requests import FoodsByFdcID as ServiceFoodsByFdcID
from app.services.usda.usda_service import usda_service

router = APIRouter(
    prefix="/internal/usda",
    tags=["usda"],
)
limiter = OutboundRateLimiter()


@router.post(
    "/foods",
    response_model=list[SearchResultFood],
    status_code=status.HTTP_200_OK,
    summary="Get multiple foods by FDC IDs",
)
@limiter
async def get_multiple_foods(criteria: RouteFoodsByFdcID):
    """Get detailed information for multiple foods by FDC IDs."""
    service_criteria = ServiceFoodsByFdcID.model_validate(criteria.model_dump(by_alias=True))
    results = await usda_service.search_by_fdcids(service_criteria)
    return [SearchResultFood.model_validate(item) for item in results]


@router.post(
    "/search",
    response_model=list[SearchResultFood],
    status_code=status.HTTP_200_OK,
    summary="Search for foods by criteria",
)
@limiter
async def search_foods(criteria: RouteFoodsByCriteria):
    """
    Search for foods with Elasticsearch cache-first strategy.

    Flow:
    1. Query Elasticsearch for matching ingredients (fuzzy search)
    2. Check Redis cache for those FDC IDs
    3. For missing results, query USDA API
    4. Cache new results and publish to Kafka for ES indexing
    5. Return merged results with complete nutrient data
    """
    service_criteria = ServiceFoodsByCriteria.model_validate(criteria.model_dump(by_alias=True))
    results = await usda_service.search_by_criteria(service_criteria)
    return [SearchResultFood.model_validate(item) for item in results]
