from fastapi import HTTPException, status


class GameNotFoundError(HTTPException):
    """Raised when a game is not found."""

    def __init__(self, detail: str = "Game not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class SteamAPIError(HTTPException):
    """Raised when Steam API returns an error."""

    def __init__(self, detail: str = "Error communicating with Steam API"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class DatabaseError(HTTPException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
