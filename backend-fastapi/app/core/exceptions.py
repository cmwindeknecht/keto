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
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=detail)


class DatabaseError(HTTPException):
    """Raised when a database operation fails."""

    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
