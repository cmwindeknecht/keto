from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GameBase(BaseModel):
    """Base game model with common fields."""

    steam_app_id: int = Field(..., description="Steam application ID")
    name: str = Field(..., description="Game name")
    description: Optional[str] = Field(None, description="Game description")


class GameCreate(GameBase):
    """Game creation request model."""

    pass


class GameUpdate(BaseModel):
    """Game update request model."""

    name: Optional[str] = None
    description: Optional[str] = None


class GameResponse(GameBase):
    """Game response model."""

    id: int = Field(..., description="Database ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class FetchGameRequest(BaseModel):
    """Request to fetch game from Steam API."""

    steam_app_id: int = Field(..., description="Steam application ID to fetch")


class FetchGameResponse(BaseModel):
    """Response from fetching game from Steam API."""

    success: bool = Field(..., description="Whether fetch was successful")
    game_id: Optional[int] = Field(None, description="Resulting game ID in database")
    error: Optional[str] = Field(None, description="Error message if fetch failed")
