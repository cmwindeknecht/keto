"""Service for interacting with USDA FoodData Central API."""

import httpx

from app.core.config import settings
from app.core.exceptions import USDAAPIError
from .models.requests import FoodsCriteria, FoodListCriteria, FoodSearchCriteria
from .models.responses import (
    AbridgedFoodItem,
    BrandedFoodItem,
    FoundationFoodItem,
    SRLegacyFoodItem,
    SurveyFoodItem,
    SearchResult,
)


class USDAService:
    """Service for interacting with USDA FoodData Central API."""

    USDA_SEARCH_ENDPOINT = "/v1/foods/search"
    USDA_FOOD_BY_ID_ENDPOINT = "/v1/food"
    USDA_FOODS_BY_IDS_ENDPOINT = "/v1/foods"
    USDA_FOODS_LIST_ENDPOINT = "/v1/foods/list"

    def __init__(self):
        self.base_url = settings.USDA_API_BASE_URL
        self.api_key = settings.USDA_API_KEY

    async def search_single_detail(
        self, fdc_id: int, format: str = "full", nutrients: list[int] | None = None
    ) -> AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem:
        """
        Get detailed information for a single food by FDC ID.

        Args:
            fdc_id: USDA FoodData Central ID
            format: 'abridged' or 'full' (default)
            nutrients: Optional list of nutrient numbers to include

        Returns:
            Food item with detailed information

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_FOOD_BY_ID_ENDPOINT}/{fdc_id}"
        params = {"api_key": self.api_key, "format": format}

        if nutrients:
            params["nutrients"] = ",".join(map(str, nutrients))

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API single food detail error: {str(e)}")

    async def search_multi_detail(
        self, criteria: FoodsCriteria
    ) -> list[AbridgedFoodItem | BrandedFoodItem | FoundationFoodItem | SRLegacyFoodItem | SurveyFoodItem]:
        """
        Get detailed information for multiple foods by FDC IDs.

        Args:
            criteria: FoodsCriteria with fdcIds and optional format/nutrients

        Returns:
            List of food items with detailed information

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_FOODS_BY_IDS_ENDPOINT}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    url,
                    json=criteria.model_dump(by_alias=True, exclude_none=True),
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API multi-food detail error: {str(e)}")

    async def list_all_foods(self, criteria: FoodListCriteria | None = None) -> list[AbridgedFoodItem]:
        """
        Get a paged list of foods in abridged format.

        Args:
            criteria: Optional FoodListCriteria for filtering and pagination

        Returns:
            List of abridged food items

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_FOODS_LIST_ENDPOINT}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if criteria:
                    response = await client.post(
                        url,
                        json=criteria.model_dump(by_alias=True, exclude_none=True),
                        params={"api_key": self.api_key},
                    )
                else:
                    response = await client.get(url, params={"api_key": self.api_key})

                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API list foods error: {str(e)}")

    async def search(self, criteria: FoodSearchCriteria | None = None, query: str | None = None) -> SearchResult:
        """
        Search for foods by keywords.

        Args:
            criteria: Optional FoodSearchCriteria for POST request with complex filters
            query: Simple search query for GET request (if criteria is None)

        Returns:
            SearchResult with paginated food items

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_SEARCH_ENDPOINT}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if criteria:
                    response = await client.post(
                        url,
                        json=criteria.model_dump(by_alias=True, exclude_none=True),
                        params={"api_key": self.api_key},
                    )
                elif query:
                    response = await client.get(
                        url,
                        params={
                            "query": query,
                            "api_key": self.api_key,
                        },
                    )
                else:
                    raise USDAAPIError("Either criteria or query must be provided")

                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API search error: {str(e)}")

    async def search_ingredients(self, query: str, limit: int = 20) -> list[dict]:
        """
        Search for ingredients in USDA FoodData Central.

        Args:
            query: Search term (ingredient name or keyword)
            limit: Maximum number of results to return

        Returns:
            List of ingredient data dictionaries from USDA API

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_SEARCH_ENDPOINT}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={
                        "query": query,
                        "pageSize": limit,
                        "api_key": self.api_key,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return data.get("foods", [])
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API search error: {str(e)}")

    async def get_ingredient_details(self, fdc_id: str) -> dict:
        """
        Get detailed nutrition information for a specific ingredient from USDA.

        Args:
            fdc_id: USDA FoodData Central ID for the ingredient

        Returns:
            Detailed ingredient data dictionary from USDA API

        Raises:
            USDAAPIError: If the API call fails
        """
        if not self.api_key:
            raise USDAAPIError("USDA API key not configured")

        url = f"{self.base_url}{self.USDA_FOOD_BY_ID_ENDPOINT}/{fdc_id}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={"api_key": self.api_key},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise USDAAPIError(f"USDA API detail error: {str(e)}")


usda_service = USDAService()
