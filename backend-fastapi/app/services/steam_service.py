import httpx

from app.core.config import settings
from app.core.exceptions import SteamAPIError


class SteamService:
    """Service for interacting with the Steam API."""

    def __init__(self):
        self.base_url = settings.STEAM_API_BASE_URL
        self.api_key = settings.STEAM_API_KEY

    async def get_app_details(self, app_id: int) -> dict:
        """
        Fetch app details from Steam API.

        Args:
            app_id: Steam application ID

        Returns:
            Dictionary with app details

        Raises:
            SteamAPIError: If the API request fails
        """
        if not self.api_key:
            raise SteamAPIError("Steam API key not configured")

        url = f"{self.base_url}/ISteamApps/GetAppList/v2/"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url,
                    params={"key": self.api_key, "appids": app_id},
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise SteamAPIError(f"Steam API error: {str(e)}")

    async def search_apps(self, query: str) -> list[dict]:
        """
        Search for Steam apps by name.

        Args:
            query: Search query string

        Returns:
            List of matching app details

        Raises:
            SteamAPIError: If the API request fails
        """
        url = f"{self.base_url}/ISteamApps/GetAppList/v2/"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                # Filter apps by query (basic in-memory search)
                apps = data.get("applist", {}).get("apps", [])
                query_lower = query.lower()
                return [app for app in apps if query_lower in app.get("name", "").lower()]
        except httpx.HTTPError as e:
            raise SteamAPIError(f"Steam API error: {str(e)}")


steam_service = SteamService()
