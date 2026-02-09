from typing import Optional

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.routes.models.requests import RecipeCreate, RecipeUpdate, SearchIngredientsRequest, RecipeIngredientInput
from app.routes.models.responses import RecipeResponse, SearchIngredientsResponse, IngredientResponse
from app.services.recipe_service import recipe_service
from app.services.usda_service import usda_service

router = APIRouter(
    prefix="/internal/recipes",
    tags=["recipes"],
)


@router.post(
    "/",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recipe",
)
async def create_recipe(
    request: RecipeCreate,
    session: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Create a new recipe with ingredients."""
    return await recipe_service.create_recipe(session, request)


@router.get(
    "/{recipe_id}",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recipe by ID",
)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Get a recipe by ID with all ingredients and nutrition calculated."""
    return await recipe_service.get_recipe(session, recipe_id)


@router.get(
    "/",
    response_model=list[RecipeResponse],
    status_code=status.HTTP_200_OK,
    summary="List recipes",
)
async def list_recipes(
    cuisine: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> list[RecipeResponse]:
    """List all recipes, optionally filtered by cuisine."""
    return await recipe_service.list_recipes(session, cuisine)


@router.put(
    "/{recipe_id}",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update recipe",
)
async def update_recipe(
    recipe_id: int,
    request: RecipeUpdate,
    session: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Update recipe details (name, cuisine, description)."""
    return await recipe_service.update_recipe(session, recipe_id, request)


@router.delete(
    "/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete recipe",
)
async def delete_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_db),
) -> None:
    """Delete a recipe and all its ingredients."""
    await recipe_service.delete_recipe(session, recipe_id)


@router.post(
    "/{recipe_id}/ingredients",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Add ingredient to recipe",
)
async def add_ingredient_to_recipe(
    recipe_id: int,
    request: RecipeIngredientInput,
    session: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Add an ingredient to an existing recipe."""
    return await recipe_service.add_ingredient_to_recipe(session, recipe_id, request)


@router.delete(
    "/{recipe_id}/ingredients/{ingredient_id}",
    response_model=RecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove ingredient from recipe",
)
async def remove_ingredient_from_recipe(
    recipe_id: int,
    ingredient_id: int,
    session: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    """Remove an ingredient from a recipe."""
    return await recipe_service.remove_ingredient_from_recipe(session, recipe_id, ingredient_id)


@router.post(
    "/search-ingredients",
    response_model=SearchIngredientsResponse,
    status_code=status.HTTP_200_OK,
    summary="Search USDA for ingredients",
)
async def search_ingredients(
    request: SearchIngredientsRequest,
) -> SearchIngredientsResponse:
    """Search for ingredients in USDA FoodData Central database."""
    results = await usda_service.search_ingredients(request.query, request.limit)
    ingredients = []
    for result in results:
        # Map USDA API response to IngredientResponse
        nutrients = {nutrient.get("nutrientId"): nutrient.get("value", 0) for nutrient in result.get("foodNutrients", [])}
        ingredients.append(
            IngredientResponse(
                id=0,  # Not yet in database
                usda_fdc_id=result.get("fdcId", ""),
                name=result.get("description", "Unknown"),
                calories_per_100g=nutrients.get(1008, 0),
                protein_per_100g=nutrients.get(1003, 0),
                fat_per_100g=nutrients.get(1004, 0),
                carbs_per_100g=nutrients.get(1005, 0),
                fiber_per_100g=nutrients.get(1079, 0),
            )
        )
    return SearchIngredientsResponse(results=ingredients, total=len(ingredients))
