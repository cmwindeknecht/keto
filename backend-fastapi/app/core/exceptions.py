from fastapi import HTTPException, status


class RecipeNotFoundError(HTTPException):
    """Raised when a recipe is not found."""

    def __init__(self, detail: str = "Recipe not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class IngredientNotFoundError(HTTPException):
    """Raised when an ingredient is not found."""

    def __init__(self, detail: str = "Ingredient not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class USDAAPIError(HTTPException):
    """Raised when USDA FoodData Central API returns an error."""

    def __init__(self, detail: str = "Error communicating with USDA API"):
        # Try to extract HTTP status code from error message
        # e.g., "Client error '404 '" or "Client error '403 Forbidden'"
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        if "404" in detail:
            status_code = status.HTTP_404_NOT_FOUND
        elif "403" in detail:
            status_code = status.HTTP_403_FORBIDDEN
        elif "401" in detail:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif "400" in detail:
            status_code = status.HTTP_400_BAD_REQUEST

        super().__init__(status_code=status_code, detail=detail)


class DatabaseError(HTTPException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
