from fastapi import HTTPException, status


class USDAAPIError(HTTPException):
    """Raised when USDA FoodData Central API returns an error."""

    def __init__(self, url: str, detail: str = "Error communicating with USDA API", status_code: int = None):
        if status_code is None:
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        super().__init__(status_code=status_code, detail=detail, headers={"X-URL": url})


class RecipeNotFoundError(HTTPException):
    """Raised when a recipe is not found."""

    def __init__(self, detail: str = "Recipe not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class IngredientNotFoundError(HTTPException):
    """Raised when an ingredient is not found."""

    def __init__(self, detail: str = "Ingredient not found"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class DatabaseError(HTTPException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
