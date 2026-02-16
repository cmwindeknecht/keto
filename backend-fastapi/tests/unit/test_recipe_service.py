"""Unit tests for recipe service."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import IngredientNotFoundError, RecipeNotFoundError
from app.db.models import Cuisine, Recipe, RecipeIngredient
from app.services.recipe.models.requests import RecipeCreate, RecipeIngredientInput
from app.services.recipe.recipe_service import recipe_service


@pytest.fixture
def sample_recipe_create():
    """Sample recipe creation request."""
    return RecipeCreate(
        name="Test Recipe",
        cuisine=Cuisine.AMERICAN,
        description="A test recipe",
        ingredients=[
            RecipeIngredientInput(usda_fdc_id=2346407, quantity_grams=100),
            RecipeIngredientInput(usda_fdc_id=2346408, quantity_grams=50),
        ],
    )


@pytest.fixture
def sample_usda_response():
    """Sample USDA service response."""
    return [
        {
            "fdcId": 2346407,
            "dataType": "Foundation",
            "description": "Cabbage, green, raw",
            "foodNutrients": [
                {
                    "nutrientId": 1003,
                    "nutrientName": "Protein",
                    "value": 0.961,
                    "unitName": "G",
                },
            ],
        },
        {
            "fdcId": 2346408,
            "dataType": "Foundation",
            "description": "Cabbage, red, raw",
            "foodNutrients": [
                {
                    "nutrientId": 1003,
                    "nutrientName": "Protein",
                    "value": 1.0,
                    "unitName": "G",
                },
            ],
        },
    ]


@pytest.mark.asyncio
async def test_create_recipe_success(test_db_session, sample_recipe_create, sample_usda_response):
    """Test successful recipe creation."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = await recipe_service.create_recipe(test_db_session, sample_recipe_create)

        assert response.name == "Test Recipe"
        assert response.cuisine == Cuisine.AMERICAN
        assert len(response.ingredients) == 2
        assert len(response.nutrients) > 0


@pytest.mark.asyncio
async def test_create_recipe_ingredient_not_found(test_db_session, sample_recipe_create):
    """Test recipe creation with missing ingredient."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        # Return empty list for ingredients not found
        mock_usda.search_by_fdcids = AsyncMock(return_value=[])

        with pytest.raises(IngredientNotFoundError):
            await recipe_service.create_recipe(test_db_session, sample_recipe_create)


@pytest.mark.asyncio
async def test_get_recipe_success(test_db_session, sample_recipe_create, sample_usda_response):
    """Test retrieving a recipe."""
    # First create a recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        created = await recipe_service.create_recipe(test_db_session, sample_recipe_create)
        recipe_id = created.id

    # Now retrieve it
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = await recipe_service.get_recipe(test_db_session, recipe_id)

        assert response.id == recipe_id
        assert response.name == "Test Recipe"


@pytest.mark.asyncio
async def test_get_recipe_not_found(test_db_session):
    """Test retrieving non-existent recipe."""
    with pytest.raises(RecipeNotFoundError):
        await recipe_service.get_recipe(test_db_session, 9999)


@pytest.mark.asyncio
async def test_list_recipes(test_db_session, sample_recipe_create, sample_usda_response):
    """Test listing recipes."""
    # Create a recipe first
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        await recipe_service.create_recipe(test_db_session, sample_recipe_create)

    # List recipes
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        recipes = await recipe_service.list_recipes(test_db_session)

        assert len(recipes) > 0
        assert recipes[0].name == "Test Recipe"


@pytest.mark.asyncio
async def test_list_recipes_by_cuisine(test_db_session, sample_recipe_create, sample_usda_response):
    """Test listing recipes filtered by cuisine."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        await recipe_service.create_recipe(test_db_session, sample_recipe_create)

    # List by cuisine
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        recipes = await recipe_service.list_recipes(test_db_session, cuisine="AMERICAN")

        assert len(recipes) > 0


@pytest.mark.asyncio
async def test_delete_recipe_success(test_db_session, sample_recipe_create, sample_usda_response):
    """Test deleting a recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        created = await recipe_service.create_recipe(test_db_session, sample_recipe_create)
        recipe_id = created.id

    # Delete it
    await recipe_service.delete_recipe(test_db_session, recipe_id)

    # Verify it's gone
    with pytest.raises(RecipeNotFoundError):
        await recipe_service.get_recipe(test_db_session, recipe_id)


@pytest.mark.asyncio
async def test_delete_recipe_not_found(test_db_session):
    """Test deleting non-existent recipe."""
    with pytest.raises(RecipeNotFoundError):
        await recipe_service.delete_recipe(test_db_session, 9999)


@pytest.mark.asyncio
async def test_update_recipe_success(test_db_session, sample_recipe_create, sample_usda_response):
    """Test updating a recipe."""
    from app.services.recipe.models.requests import RecipeUpdate

    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        created = await recipe_service.create_recipe(test_db_session, sample_recipe_create)
        recipe_id = created.id

    # Update it
    update_data = RecipeUpdate(name="Updated Recipe")
    response = await recipe_service.update_recipe(test_db_session, recipe_id, update_data)

    assert response.name == "Updated Recipe"


@pytest.mark.asyncio
async def test_add_ingredient_to_recipe(test_db_session, sample_recipe_create, sample_usda_response):
    """Test adding ingredient to recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        created = await recipe_service.create_recipe(test_db_session, sample_recipe_create)
        recipe_id = created.id
        initial_count = len(created.ingredients)

    # Add ingredient
    new_ingredient = RecipeIngredientInput(usda_fdc_id=2346407, quantity_grams=75)
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = await recipe_service.add_ingredient_to_recipe(test_db_session, recipe_id, new_ingredient)

        assert len(response.ingredients) == initial_count + 1


@pytest.mark.asyncio
async def test_remove_ingredient_from_recipe(test_db_session, sample_recipe_create, sample_usda_response):
    """Test removing ingredient from recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        created = await recipe_service.create_recipe(test_db_session, sample_recipe_create)
        recipe_id = created.id
        ingredient_id = created.ingredients[0].id

    # Remove ingredient
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = await recipe_service.remove_ingredient_from_recipe(test_db_session, recipe_id, ingredient_id)

        assert len(response.ingredients) < 2
