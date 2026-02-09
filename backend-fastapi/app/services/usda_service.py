import httpx

from app.core.config import settings
from app.core.exceptions import USDAAPIError


class USDAService:
    """Service for interacting with USDA FoodData Central API."""

    def __init__(self):
        self.base_url = settings.USDA_API_BASE_URL
        self.api_key = settings.USDA_API_KEY

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

        url = f"{self.base_url}/search"
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

        url = f"{self.base_url}/{fdc_id}"
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
