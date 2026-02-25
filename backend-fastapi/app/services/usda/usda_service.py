"""Service for interacting with USDA FoodData Central API."""

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Any

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

            foods: list[dict[Any, Any]] = response.json()
            for food in foods:
                await cache_service.set_ingredient(food)

            return foods

    @handle_usda_errors
    async def search_by_criteria(self, criteria: FoodsByCriteria, url: str | None = None, include_brands: bool = False) -> list[dict]:
        """
        Search for ingredients with query-cache-first strategy.

        Flow:
        1. Check Redis search cache by query string — return immediately on hit
        2. Query Elasticsearch for any already-indexed matching FDC IDs (supplemental)
        3. Query USDA API for canonical search results
        4. Cache individual ingredients in Redis by FDC ID
        5. Publish new ingredients to Kafka for ES indexing
        6. Cache the full result set by query string
        7. Return merged results

        Args:
            criteria: FoodsByCriteria with search query and filters
            url: for error handling context
            include_brands: Include Branded items in search

        Returns:
            List of food items matching search criteria with full nutrient data

        Raises:
            USDAAPIError: If the API call fails
        """
        data_types = ["Foundation", "SR Legacy"]
        if include_brands:
            data_types.append("Branded")

        # Step 1: Check search query cache
        cached = await cache_service.get_search_results(criteria.query)
        if cached is not None:
            logger.info(f"[SEARCH] Query cache HIT for '{criteria.query}' — returning {len(cached)} cached results, skipping ES + USDA")
            return cached

        logger.info(f"[SEARCH] Query cache MISS for '{criteria.query}' — proceeding to ES + USDA")

        # Step 2: Query Elasticsearch for supplemental results (best-effort, sparse index)
        es_results = await elasticsearch_service.search_ingredients(criteria.query, data_types, criteria.page_size or 20)
        logger.info(f"[SEARCH] ES returned {len(es_results)} candidate(s) for '{criteria.query}'")

        results, missing_fdc_ids = await self.intersect_results(es_results)
        logger.info(f"[SEARCH] ES candidates — {len(results)} found in ingredient cache, {len(missing_fdc_ids)} not cached")

        # Step 3: Always query USDA for the canonical search results
        if url is None:
            url = f"{self.base_url}{self.USDA_FOODS_SEARCH_ENDPOINT}"

        logger.info(f"[SEARCH] Querying USDA at {url} for '{criteria.query}'")
        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            request_body = criteria.model_dump(by_alias=True, exclude_none=True)
            response = await client.post(
                url,
                json=request_body,
                params=self.get_api_params(),
            )
            response.raise_for_status()

            result_dict = response.json()
            usda_food_count = len(result_dict.get("foods", []))
            logger.info(f"[SEARCH] USDA returned {usda_food_count} result(s) for '{criteria.query}'")
            search_result = SearchResult.model_validate(result_dict)

            existing_fdc_ids = {r.get("fdcId") for r in results}
            for food in search_result.foods:
                food_dict = food.model_dump(by_alias=True, exclude_none=True)

                if food_dict["fdcId"] not in existing_fdc_ids:
                    # Step 4: Cache individual ingredient by FDC ID
                    await cache_service.set_ingredient(food_dict)
                    logger.debug(f"[SEARCH] Cached ingredient fdcId={food_dict['fdcId']} ({food_dict.get('description', '?')})")

                    # Step 5: Publish to Kafka for ES indexing
                    try:
                        await kafka_producer.publish_ingredient_cached(
                            IngredientCached(fdc_id=food_dict["fdcId"], data=food_dict, cached_at=datetime.now(timezone.utc))
                        )
                        logger.debug(f"[SEARCH] Published fdcId={food_dict['fdcId']} to Kafka for ES indexing")
                    except Exception as e:
                        logger.warning(f"[SEARCH] Failed to publish fdcId={food_dict['fdcId']} to Kafka: {e}")

                    results.append(food_dict)
                    existing_fdc_ids.add(food_dict["fdcId"])

        # Step 6: Cache the full result set by query string
        await cache_service.set_search_results(criteria.query, results)
        logger.info(f"[SEARCH] Cached {len(results)} result(s) under query '{criteria.query}'")

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
        criteria = FoodsByFdcID(fdcIds=[fdc_id], format="full")

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                url,
                json=criteria.model_dump(by_alias=True, exclude_none=True),
                params=self.get_api_params(),
            )
            response.raise_for_status()

            # USDA returns a list, extract the first item
            results: list[dict[Any, Any]] = response.json()
            if results:
                return results[0]
            raise USDAAPIError(url=url, detail=f"Ingredient {fdc_id} not found", status_code=404)

    def get_api_params(self):
        return {self.API_KEY: self.usda_api_key}


usda_service = USDAService()
