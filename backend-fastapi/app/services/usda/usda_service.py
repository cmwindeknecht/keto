"""Service for interacting with USDA FoodData Central API."""

from functools import wraps
from datetime import datetime
import httpx

from app.core.config import settings
from app.core.exceptions import USDAAPIError
from app.services.cache.cache_service import cache_service
from app.services.elasticsearch.es_service import elasticsearch_service
from app.services.kafka.producer import kafka_producer
from app.services.kafka.models import IngredientCached
from .models.requests import FoodsByFdcID, FoodsByCriteria
from .models.responses import SearchResult


def handle_usda_errors(func):
      """Decorator to handle USDA API errors consistently."""
      @wraps(func)
      async def wrapper(*args, **kwargs):
          self = args[0]
          url = kwargs.get("url")
          
          if not self.api_key:
              raise USDAAPIError("USDA API key not configured", url=url, status_code=None)
          
          try:
              return await func(*args, **kwargs)
          except httpx.HTTPStatusError as e:
              raise USDAAPIError(f"USDA API error: {str(e)}", url=url, status_code=e.response.status_code)
          except httpx.HTTPError as e:
              raise USDAAPIError(f"USDA API error: {str(e)}", url=url, status_code=None)
      return wrapper


class USDAService:
    """Service for interacting with USDA FoodData Central API."""

    USDA_FOODS_SEARCH_ENDPOINT = "/v1/foods/search"
    USDA_FOODS_BY_IDS_ENDPOINT = "/v1/foods"
    
    API_KEY = "api_key"
    DEFAULT_TIMEOUT = 10.0  # seconds

    def __init__(self):
        self.base_url = settings.USDA_API_BASE_URL
        self.api_key = settings.USDA_API_KEY
        
    @handle_usda_errors
    async def search_by_fdcids(self, criteria: FoodsByFdcID, url: str = None) -> list[dict]:
        """
        Used to get recipe details with stored FdcIDs for ingredients in the recipe

        Args:
        - criteria: FoodsByFdcID with fdcIds and optional format/nutrients
        - url: for error handling context

        @Returns: List of food items with detailed information

        @Raises: USDAAPIError: If the API call fails
        """
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
            return cached_ingredients
        
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
    async def search_by_criteria(self, criteria: FoodsByCriteria, url: str = None) -> list[dict]:
        """
        Used to get food/ingredient details by user search criteria when FdcID is unknown
        
        Args:
        - criteria: FoodsByCriteria for POST request with complex filters
        - url: for error handling context

        @Returns: list[dict] of food items matching search criteria with detailed information
    
        @Raises: USDAAPIError: If the API call fails
        """
        url = f"{self.base_url}{self.USDA_FOODS_SEARCH_ENDPOINT}"

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                    url,
                    json=criteria.model_dump(by_alias=True, exclude_none=True),
                    params=self.get_api_params(),
                )

            response.raise_for_status()
            
            result_dict = response.json()
            search_result = SearchResult.model_validate(result_dict)
            for food in search_result.foods:
                await cache_service.set_ingredient(food.model_dump(by_alias=True, exclude_none=True))
                
            return result_dict['foods']

    async def search_ingredients(
        self,
        query: str,
        limit: int = 20,
        include_brands: bool = False
    ) -> list[dict]:
        """
        Search for ingredients with Elasticsearch-first strategy.

        Flow:
        1. Query Elasticsearch to get matching FDC IDs
        2. Check cache for those IDs (returns full nutrient data)
        3. For missing IDs, query USDA API by query
        4. Cache new results in Redis
        5. Publish to Kafka for ES indexing
        6. Return merged results with full nutrient data

        Args:
            query: Search query string
            limit: Maximum number of results
            include_brands: Include Branded items in search

        Returns:
            List of full ingredient dictionaries with complete nutrient data
        """
        # Determine data types to search
        data_types = ["Foundation", "SR Legacy"]
        if include_brands:
            data_types.append("Branded")

        # Step 1: Query Elasticsearch for matching ingredient IDs
        es_results = await elasticsearch_service.search_ingredients(
            query,
            data_types,
            limit
        )

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

        # If all results found in cache, return early
        if not missing_fdc_ids:
            return results[:limit]

        # Step 3: Query USDA for missing ingredients
        criteria = FoodsByCriteria(
            query=query,
            dataType=data_types,
            pageSize=limit
        )

        try:
            usda_results = await self.search_by_criteria(criteria)

            # Cache and publish each new result
            for item in usda_results:
                if item["fdcId"] not in [r.get("fdcId") for r in results]:
                    # Cache in Redis
                    await cache_service.set_ingredient(item)

                    # Publish to Kafka (fire-and-forget)
                    try:
                        await kafka_producer.publish_ingredient_cached(
                            IngredientCached(
                                fdc_id=item["fdcId"],
                                data=item,
                                cached_at=datetime.utcnow()
                            )
                        )
                    except Exception as e:
                        print(f"⚠ Failed to publish ingredient {item['fdcId']} to Kafka: {e}")

                    results.append(item)

        except Exception as e:
            print(f"⚠ USDA search failed for query '{query}': {e}")

        return results[:limit]

    def get_api_params(self):
        return {self.API_KEY: self.api_key}

usda_service = USDAService()
