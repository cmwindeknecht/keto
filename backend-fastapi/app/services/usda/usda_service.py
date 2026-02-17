"""Service for interacting with USDA FoodData Central API."""

import logging
from datetime import datetime, timezone
from functools import wraps

import httpx

from app.core.config import settings
from app.core.exceptions import USDAAPIError
from app.services.cache.cache_service import cache_service
from app.services.elasticsearch.es_service import elasticsearch_service
from app.services.kafka.models import IngredientCached
from app.services.kafka.producer import kafka_producer

from .models.requests import FoodsByCriteria, FoodsByFdcID
from .models.responses import SearchResult

logger = logging.getLogger(__name__)


def handle_usda_errors(func):
    """Decorator to handle USDA API errors consistently."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        self = args[0]
        url = kwargs.get("url")

        if not self.usda_api_key:
            raise USDAAPIError(url=url, detail="USDA API key not configured", status_code=None)

        try:
            return await func(*args, **kwargs)
        except httpx.HTTPStatusError as e:
            raise USDAAPIError(url=url, detail=f"USDA API error: {str(e)}", status_code=e.response.status_code) from e
        except httpx.HTTPError as e:
            raise USDAAPIError(url=url, detail=f"USDA API error: {str(e)}", status_code=None) from e

    return wrapper


class USDAService:
    """Service for interacting with USDA FoodData Central API."""

    USDA_FOODS_SEARCH_ENDPOINT = "/v1/foods/search"
    USDA_FOODS_BY_IDS_ENDPOINT = "/v1/foods"

    API_KEY = "api_key"
    DEFAULT_TIMEOUT = 10.0  # seconds

    def __init__(self):
        self.base_url = settings.USDA_API_BASE_URL
        self.usda_api_key = settings.USDA_API_KEY

    @handle_usda_errors
    async def search_by_fdcids(self, criteria: FoodsByFdcID, url: str | None = None) -> list[dict]:
        """
        Used to get recipe details with stored FdcIDs for ingredients in the recipe

        Args:
        - criteria: FoodsByFdcID with fdcIds and optional format/nutrients
        - url: for error handling context

        @Returns: List of food items with detailed information

        @Raises: USDAAPIError: If the API call fails
        """
        if url is None:
            url = f"{self.base_url}{self.USDA_FOODS_BY_IDS_ENDPOINT}"

        cached_ingredients: list[dict] = []
        missing_fdc_ids: list[int] = []
        for fdc_id in criteria.fdc_ids:
            cached = await cache_service.get_ingredient(fdc_id)
            if cached is not None:
                cached_ingredients.append(cached)
            else:
                missing_fdc_ids.append(fdc_id)

        # All ingredients were found in cache
        if len(missing_fdc_ids) == 0:
            logger.info(f"All {len(cached_ingredients)} ingredients found in cache for FDC IDs: {criteria.fdc_ids}")
            return cached_ingredients

        logger.info(f"{len(cached_ingredients)} ingredients found in cache, {len(missing_fdc_ids)} missing for FDC IDs: {criteria.fdc_ids}")
        # Update the critieria to only include missing FDC IDs that need to be fetched from USDA API
        criteria.fdc_ids = missing_fdc_ids

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                url,
                json=criteria.model_dump(by_alias=True, exclude_none=True),
                params=self.get_api_params(),
            )
            response.raise_for_status()

            for food in response.json():
                await cache_service.set_ingredient(food)

            return response.json()

    @handle_usda_errors
    async def search_by_criteria(self, criteria: FoodsByCriteria, url: str | None = None, include_brands: bool = False) -> list[dict]:
        """
        Search for ingredients with Elasticsearch-first strategy.

        Flow:
        1. Query Elasticsearch for matching FDC IDs (fuzzy search)
        2. Check cache for those IDs
        3. For missing IDs, query USDA API
        4. Cache new results in Redis
        5. Publish to Kafka for ES indexing
        6. Return merged results

        Args:
            criteria: FoodsByCriteria with search query and filters
            url: for error handling context
            include_brands: Include Branded items in search

        Returns:
            List of food items matching search criteria with full nutrient data

        Raises:
            USDAAPIError: If the API call fails
        """
        # Determine data types to search
        data_types = ["Foundation", "SR Legacy"]
        if include_brands:
            data_types.append("Branded")

        # Step 1: Query Elasticsearch for matching ingredient IDs
        es_results = await elasticsearch_service.search_ingredients(criteria.query, data_types, criteria.page_size or 20)

        results, missing_fdc_ids = await self.intersect_results(es_results)

        # If all results found in cache (and ES returned something), return early
        if not missing_fdc_ids and results:
            logger.info(f"All {len(results)} ES search results found in cache for query '{criteria.query}' with data types {data_types}")
            return results

        logger.info(f"{len(results)} ES search results found in cache, {len(missing_fdc_ids)} missing for query '{criteria.query}'")

        # Step 3: Query USDA for missing ingredients (or if ES returned nothing)
        if url is None:
            url = f"{self.base_url}{self.USDA_FOODS_SEARCH_ENDPOINT}"

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            request_body = criteria.model_dump(by_alias=True, exclude_none=True)
            logger.info(f"search_by_criteria request to {url}, Request body: {request_body}")

            response = await client.post(
                url,
                json=request_body,
                params=self.get_api_params(),
            )

            response.raise_for_status()

            result_dict = response.json()
            if result_dict.get("foods"):
                logger.info(f"Got {len(result_dict['foods'])} results from USDA search")
            search_result = SearchResult.model_validate(result_dict)

            # Cache and publish each result
            for food in search_result.foods:
                food_dict = food.model_dump(by_alias=True, exclude_none=True)

                # Only add if not already in results
                if food_dict["fdcId"] not in [r.get("fdcId") for r in results]:
                    # Cache in Redis
                    await cache_service.set_ingredient(food_dict)

                    # Publish to Kafka
                    try:
                        await kafka_producer.publish_ingredient_cached(
                            IngredientCached(fdc_id=food_dict["fdcId"], data=food_dict, cached_at=datetime.now(timezone.utc))
                        )
                    except Exception as e:
                        logger.warning(f"Failed to publish ingredient {food_dict['fdcId']} to Kafka: {e}")

                    results.append(food_dict)

            return results

    async def intersect_results(self, es_results: list[dict]) -> tuple[list[dict], list[dict]]:
        results = []
        missing_fdc_ids = []

        # Step 2: Try to get full data from cache for ES results
        for es_result in es_results:
            fdc_id = es_result["fdc_id"]
            cached_data = await cache_service.get_ingredient(fdc_id)
            if cached_data:
                results.append(cached_data)
            else:
                missing_fdc_ids.append(fdc_id)

        return results, missing_fdc_ids

    async def _fetch_from_usda(self, fdc_id: int) -> dict:
        """
        Fetch a single ingredient by FDC ID from USDA API.

        Internal helper method used by cronjobs and refresh operations.

        Args:
            fdc_id: USDA FoodData Central ID

        Returns:
            Raw USDA API response as dictionary

        Raises:
            USDAAPIError: If the API call fails
        """
        url = f"{self.base_url}{self.USDA_FOODS_BY_IDS_ENDPOINT}"
        criteria = FoodsByFdcID(fdc_ids=[fdc_id])

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                url,
                json=criteria.model_dump(by_alias=True, exclude_none=True),
                params=self.get_api_params(),
            )
            response.raise_for_status()

            # USDA returns a list, extract the first item
            results = response.json()
            if results:
                return results[0]
            raise USDAAPIError(url=url, detail=f"Ingredient {fdc_id} not found", status_code=404)

    def get_api_params(self):
        return {self.API_KEY: self.usda_api_key}


usda_service = USDAService()
