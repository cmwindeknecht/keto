from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DatabaseError
from app.routes.models.requests import GameCreate
from app.routes.models.responses import GameResponse
from app.services.steam_service import steam_service


"""External Facing Service for managing game data."""
class GameService:
    

    async def create_game(self, session: AsyncSession, game_data: GameCreate) -> GameResponse:
        """
        Create a new game in the database.

        Args:
            session: Database session
            game_data: Game creation data

        Returns:
            Created game response

        Raises:
            DatabaseError: If creation fails
        """
        try:
            # This is a placeholder - replace with actual ORM model once created
            # For now, returning a mock response to show the structure
            return GameResponse(
                id=1,
                steam_app_id=game_data.steam_app_id,
                name=game_data.name,
                description=game_data.description,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        except Exception as e:
            raise DatabaseError(f"Failed to create game: {str(e)}")

    async def fetch_and_create_game(self, session: AsyncSession, steam_app_id: int) -> dict:
        """
        Fetch game data from Steam API and create in database.

        Args:
            session: Database session
            steam_app_id: Steam application ID to fetch

        Returns:
            Dictionary with success status and game_id or error

        Raises:
            DatabaseError: If database operation fails
        """
        try:
            # Fetch from Steam API
            steam_data = await steam_service.get_app_details(steam_app_id)

            # Extract game info (adjust based on actual Steam API response structure)
            app_info = steam_data.get("applist", {}).get("apps", [{}])[0]
            game_name = app_info.get("name", f"App {steam_app_id}")

            # Create game in database
            game_create = GameCreate(
                steam_app_id=steam_app_id,
                name=game_name,
            )

            game = await self.create_game(session, game_create)

            return {
                "success": True,
                "game_id": game.id,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


game_service = GameService()
