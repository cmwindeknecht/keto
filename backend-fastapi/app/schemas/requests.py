from typing import Optional

from pydantic import BaseModel, Field


## TODO These are not great --- but its a fine start so I can do it properly later
class GameCreate(BaseModel):
    """Request to create a new game."""

    steam_app_id: int = Field(..., description="Steam application ID")
    name: str = Field(..., description="Game name")
    description: Optional[str] = Field(None, description="Game description")


class GameUpdate(BaseModel):
    """Request to update an existing game."""

    name: Optional[str] = Field(None, description="Game name")
    description: Optional[str] = Field(None, description="Game description")


class FetchGameRequest(BaseModel):
    """Request to fetch game from Steam API."""

    steam_app_id: int = Field(..., description="Steam application ID to fetch")
