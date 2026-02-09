from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.schemas import FetchGameRequest, FetchGameResponse
from app.services.game_service import game_service

router = APIRouter(prefix="/internal/games", tags=["internal", "games"])


@router.post(
    "/fetch",
    response_model=FetchGameResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch game from Steam API",
    description="Internal endpoint to fetch game data from Steam API and store in database",
)
async def fetch_game(
    request: FetchGameRequest,
    session: AsyncSession = Depends(get_db),
) -> FetchGameResponse:
    """
    Fetch game data from Steam API and create/update in database.

    Args:
        request: Request containing Steam app ID
        session: Database session

    Returns:
        Response with success status and game ID if successful
    """
    result = await game_service.fetch_and_create_game(session, request.steam_app_id)

    return FetchGameResponse(
        success=result["success"],
        game_id=result.get("game_id"),
        error=result.get("error"),
    )
