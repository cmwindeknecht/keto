"""Integration tests for recipe routes."""

import json
from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def sample_usda_response():
    """Sample USDA API response."""
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
                {
                    "nutrientId": 1004,
                    "nutrientName": "Total lipid (fat)",
                    "value": 0.228,
                    "unitName": "G",
                },
            ],
        },
    ]


def test_create_recipe_success(test_client, sample_usda_response):
    """Test creating a recipe via API."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        payload = {
            "name": "Test Recipe",
            "cuisine": "AMERICAN",
            "description": "Test description",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }

        response = test_client.post("/internal/recipes", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Recipe"
        assert data["cuisine"] == "AMERICAN"
        assert len(data["ingredients"]) == 1


def test_create_recipe_validation_error(test_client):
    """Test recipe creation with invalid data."""
    payload = {
        "name": "",  # Empty name not allowed
        "cuisine": "AMERICAN",
        "ingredients": [],
    }

    response = test_client.post("/internal/recipes", json=payload)

    assert response.status_code == 422  # Validation error


def test_get_recipe(test_client, sample_usda_response):
    """Test retrieving a recipe."""
    # Create recipe first
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        create_payload = {
            "name": "Test Recipe",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }

        create_response = test_client.post("/internal/recipes", json=create_payload)
        recipe_id = create_response.json()["id"]

    # Get recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = test_client.get(f"/internal/recipes/{recipe_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == recipe_id
        assert data["name"] == "Test Recipe"


def test_get_recipe_not_found(test_client):
    """Test retrieving non-existent recipe."""
    response = test_client.get("/internal/recipes/9999")

    assert response.status_code == 404


def test_list_recipes(test_client, sample_usda_response):
    """Test listing recipes."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        # Create recipe
        payload = {
            "name": "Test Recipe",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }
        test_client.post("/internal/recipes", json=payload)

    # List recipes
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = test_client.get("/internal/recipes")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


def test_list_recipes_by_cuisine(test_client, sample_usda_response):
    """Test listing recipes filtered by cuisine."""
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        # Create recipe
        payload = {
            "name": "American Recipe",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }
        test_client.post("/internal/recipes", json=payload)

    # List by cuisine
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        response = test_client.get("/internal/recipes?cuisine=AMERICAN")

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


def test_update_recipe(test_client, sample_usda_response):
    """Test updating a recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        create_payload = {
            "name": "Original Name",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }

        create_response = test_client.post("/internal/recipes", json=create_payload)
        recipe_id = create_response.json()["id"]

    # Update recipe
    update_payload = {
        "name": "Updated Name",
    }

    response = test_client.put(f"/internal/recipes/{recipe_id}", json=update_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"


def test_delete_recipe(test_client, sample_usda_response):
    """Test deleting a recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        create_payload = {
            "name": "Recipe to Delete",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }

        create_response = test_client.post("/internal/recipes", json=create_payload)
        recipe_id = create_response.json()["id"]

    # Delete recipe
    response = test_client.delete(f"/internal/recipes/{recipe_id}")

    assert response.status_code == 204

    # Verify it's deleted
    get_response = test_client.get(f"/internal/recipes/{recipe_id}")
    assert get_response.status_code == 404


def test_add_ingredient_to_recipe(test_client, sample_usda_response):
    """Test adding ingredient to recipe."""
    # Create recipe
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        create_payload = {
            "name": "Test Recipe",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
            ],
        }

        create_response = test_client.post("/internal/recipes", json=create_payload)
        recipe_id = create_response.json()["id"]

    # Add ingredient
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(return_value=sample_usda_response)

        ingredient_payload = {
            "usda_fdc_id": 2346407,
            "quantity_grams": 75,
        }

        response = test_client.post(
            f"/internal/recipes/{recipe_id}/ingredients",
            json=ingredient_payload,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) > 1


def test_remove_ingredient_from_recipe(test_client, sample_usda_response):
    """Test removing ingredient from recipe."""
    # Create recipe with 2 ingredients
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(
            return_value=sample_usda_response
            + [
                {
                    "fdcId": 2346408,
                    "dataType": "Foundation",
                    "description": "Cabbage, red, raw",
                    "foodNutrients": [
                        {"nutrientId": 1003, "nutrientName": "Protein", "value": 1.0, "unitName": "G"},
                    ],
                }
            ]
        )

        create_payload = {
            "name": "Test Recipe",
            "cuisine": "AMERICAN",
            "ingredients": [
                {"usda_fdc_id": 2346407, "quantity_grams": 100},
                {"usda_fdc_id": 2346408, "quantity_grams": 50},
            ],
        }

        create_response = test_client.post("/internal/recipes", json=create_payload)
        recipe = create_response.json()
        recipe_id = recipe["id"]
        ingredient_id = recipe["ingredients"][0]["id"]

    # Remove ingredient
    with patch("app.services.recipe.recipe_service.usda_service") as mock_usda:
        mock_usda.search_by_fdcids = AsyncMock(
            return_value=sample_usda_response
            + [
                {
                    "fdcId": 2346408,
                    "dataType": "Foundation",
                    "description": "Cabbage, red, raw",
                    "foodNutrients": [
                        {"nutrientId": 1003, "nutrientName": "Protein", "value": 1.0, "unitName": "G"},
                    ],
                }
            ]
        )

        response = test_client.delete(
            f"/internal/recipes/{recipe_id}/ingredients/{ingredient_id}",
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["ingredients"]) == 1
