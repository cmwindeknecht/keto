"""Service for interacting with USDA FoodData Central API."""

from functools import wraps 
import httpx

from app.core.config import settings
from app.core.exceptions import USDAAPIError
from app.services.cache.cache_service import cache_service
from app.services.cache.models import CachedIngredient
from app.services.cache.transformers import to_cached_ingredient
from .models.requests import FoodsByFdcID, FoodsByCriteria
from .models.responses import (
    AbridgedFoodItem,
    BrandedFoodItem,
    FoundationFoodItem,
    SRLegacyFoodItem,
    SurveyFoodItem,
    SearchResult,
)


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
    async def search_by_fdcids(
        self, criteria: FoodsByFdcID, url: str = None
    ) -> list[AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem]:
        """
        Used to get recipe details with stored FdcIDs for ingredients in the recipe

        Args:
        - criteria: FoodsCriteria with fdcIds and optional format/nutrients

        @Returns: List of food items with detailed information

        @Raises: USDAAPIError: If the API call fails
        """

        url = f"{self.base_url}{self.USDA_FOODS_BY_IDS_ENDPOINT}"
        
        cached_ingredients: list[CachedIngredient] = []
        missing_fdc_ids: list[int] = []
        for fdc_id in criteria.fdc_ids:
            cached = await cache_service.get_ingredient(fdc_id)
            if cached is not None:
                # TODO - should transform to proper model --- should be one of AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem
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
                
                # TODO - cache the ingredients that were fetched from USDA API 
                # TODO combine with cached ingredients and transform to proper models --- should be one of AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem
                return response.json()

    @handle_usda_errors
    async def search_by_criteria(self, criteria: FoodsByCriteria, url: str = None) -> SearchResult:
        """
        Used to get food/ingredient details by user search criteria when FdcID is unknown
        
        Args:
        - criteria: Optional FoodSearchCriteria for POST request with complex filters
        - url: for error handling context

        @Returns: SearchResult with paginated food items

        @Raises: USDAAPIError: If the API call fails
        """

        url = f"{self.base_url}{self.USDA_FOODS_SEARCH_ENDPOINT}"
        
        # TODO make the redis cache have keys of (query, fdcid) so we can use the cache first

        async with httpx.AsyncClient(timeout=self.DEFAULT_TIMEOUT) as client:
            response = await client.post(
                    url,
                    json=criteria.model_dump(by_alias=True, exclude_none=True),
                    params=self.get_api_params(),
                )

            # TODO cache the search results in Redis with keys of (query, fdcid) so we can use the cache first for future searches
            response.raise_for_status()
            return response.json()

    def get_api_params(self):
        return {self.API_KEY: self.api_key}

usda_service = USDAService()
