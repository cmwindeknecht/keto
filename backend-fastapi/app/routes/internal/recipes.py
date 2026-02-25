from typing import Optional

from fastapi import APIRouter, Body, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.routes.models.requests import RecipeCreate as RouteRecipeCreate
from app.routes.models.requests import RecipeIngredientInput as RouteRecipeIngredientInput
from app.routes.models.requests import RecipeUpdate as RouteRecipeUpdate
from app.routes.models.responses import RecipeResponse as RouteRecipeResponse
from app.services.recipe.models.requests import RecipeCreate as ServiceRecipeCreate
from app.services.recipe.models.requests import RecipeIngredientInput as ServiceRecipeIngredientInput
from app.services.recipe.models.requests import RecipeUpdate as ServiceRecipeUpdate
from app.services.recipe.recipe_service import recipe_service

router = APIRouter(
    prefix="/internal/recipes",
    tags=["recipes"],
)


@router.post(
    "",
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new recipe",
)
async def create_recipe(
    request: RouteRecipeCreate = Body(
        ...,
        examples={
            "default": {
                "summary": "Example recipe",
                "value": {
                    "name": "Cabbage",
                    "cuisine": "MEXICAN",
                    "description": "A bunch of cabbage",
                    "ingredients": [{"usda_fdc_id": 2346407, "quantity_grams": 200}],
                },
            }
        },
    ),
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Create a new recipe with ingredients."""
    service_request = ServiceRecipeCreate.model_validate(request.model_dump())
    service_response = await recipe_service.create_recipe(session, service_request)
    return RouteRecipeResponse.model_validate(service_response.model_dump())


@router.get(
    "/{recipe_id}",
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get recipe by ID",
)
async def get_recipe(
    recipe_id: int,
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Get a recipe by ID with all ingredients and nutrition calculated."""
    service_response = await recipe_service.get_recipe(session, recipe_id)
    return RouteRecipeResponse.model_validate(service_response.model_dump())


@router.get(
    "",
    response_model=list[RouteRecipeResponse],
    status_code=status.HTTP_200_OK,
    summary="List recipes",
)
async def list_recipes(
    cuisine: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
) -> list[RouteRecipeResponse]:
    """List all recipes, optionally filtered by cuisine."""
    service_responses = await recipe_service.list_recipes(session, cuisine)
    return [RouteRecipeResponse.model_validate(item.model_dump()) for item in service_responses]


@router.put(
    "/{recipe_id}",
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update recipe",
)
async def update_recipe(
    recipe_id: int,
    request: RouteRecipeUpdate,
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Update recipe details (name, cuisine, description)."""
    service_request = ServiceRecipeUpdate.model_validate(request.model_dump())
    service_response = await recipe_service.update_recipe(session, recipe_id, service_request)
    return RouteRecipeResponse.model_validate(service_response.model_dump())


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
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Add ingredient to recipe",
)
async def add_ingredient_to_recipe(
    recipe_id: int,
    request: RouteRecipeIngredientInput,
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Add an ingredient to an existing recipe."""
    service_request = ServiceRecipeIngredientInput.model_validate(request.model_dump())
    service_response = await recipe_service.add_ingredient_to_recipe(session, recipe_id, service_request)
    return RouteRecipeResponse.model_validate(service_response.model_dump())


@router.put(
    "/{recipe_id}/ingredients/{ingredient_id}",
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Update ingredient quantity in recipe",
)
async def update_ingredient_in_recipe(
    recipe_id: int,
    ingredient_id: int,
    request: RouteRecipeIngredientInput,
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Update an ingredient's quantity in a recipe."""
    service_request = ServiceRecipeIngredientInput.model_validate(request.model_dump())
    service_response = await recipe_service.update_ingredient_in_recipe(session, recipe_id, ingredient_id, service_request)
    return RouteRecipeResponse.model_validate(service_response.model_dump())


@router.delete(
    "/{recipe_id}/ingredients/{ingredient_id}",
    response_model=RouteRecipeResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove ingredient from recipe",
)
async def remove_ingredient_from_recipe(
    recipe_id: int,
    ingredient_id: int,
    session: AsyncSession = Depends(get_db),
) -> RouteRecipeResponse:
    """Remove an ingredient from a recipe."""
    service_response = await recipe_service.remove_ingredient_from_recipe(session, recipe_id, ingredient_id)
    return RouteRecipeResponse.model_validate(service_response.model_dump())
