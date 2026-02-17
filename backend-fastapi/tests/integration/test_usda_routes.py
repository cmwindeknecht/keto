"""Integration tests for USDA routes."""

from unittest.mock import AsyncMock, patch

import pytest


@pytest.fixture
def sample_search_result():
    """Sample USDA search result."""
    return [
        {
            "fdcId": 2346407,
            "dataType": "Foundation",
            "description": "Cabbage, green, raw",
            "foodNutrients": [
                {
                    "nutrientId": 1003,
                    "nutrientNumber": "203",
                    "nutrientName": "Protein",
                    "value": 0.961,
                    "unitName": "G",
                    "derivationCode": "NC",
                    "derivationDescription": "Calculated",
                },
                {
                    "nutrientId": 1004,
                    "nutrientNumber": "204",
                    "nutrientName": "Total lipid (fat)",
                    "value": 0.228,
                    "unitName": "G",
                    "derivationCode": "A",
                    "derivationDescription": "Analytical",
                },
            ],
            "publicationDate": None,
            "brandOwner": None,
            "gtinUpc": None,
            "ingredients": None,
            "ndbNumber": 11109,
            "score": 675.59,
        },
    ]


def test_get_multiple_foods_success(test_client, sample_search_result):
    """Test getting multiple foods by FDC IDs."""
    with patch("app.services.usda.usda_service.usda_service.search_by_fdcids", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "fdcIds": [2346407],
            "format": "full",
        }

        response = test_client.post("/internal/usda/foods", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["fdcId"] == 2346407


def test_get_multiple_foods_validation_error(test_client):
    """Test validation error for missing required fields."""
    payload = {
        "fdcIds": [],  # Empty list not allowed
        "format": "full",
    }

    response = test_client.post("/internal/usda/foods", json=payload)

    assert response.status_code == 422  # Validation error


def test_get_multiple_foods_too_many_ids(test_client):
    """Test validation error for too many FDC IDs."""
    payload = {
        "fdcIds": list(range(21)),  # Max is 20
        "format": "full",
    }

    response = test_client.post("/internal/usda/foods", json=payload)

    assert response.status_code == 422


def test_search_foods_by_criteria_success(test_client, sample_search_result):
    """Test searching foods by criteria."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "query": "cabbage",
            "dataType": ["Foundation"],
            "pageSize": 10,
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert "cabbage" in data[0]["description"].lower()


def test_search_foods_minimal_payload(test_client, sample_search_result):
    """Test search with minimal required fields."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "query": "apple",
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200


def test_search_foods_validation_error(test_client):
    """Test search validation error."""
    payload = {
        "query": "",  # Empty query not allowed
    }

    response = test_client.post("/internal/usda/search", json=payload)

    assert response.status_code == 422


def test_search_foods_with_brand_owner_filter(test_client, sample_search_result):
    """Test search with brand owner filter."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "query": "cheese",
            "brandOwner": "Kraft",
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200


def test_search_foods_with_sorting(test_client, sample_search_result):
    """Test search with sorting parameters."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "query": "chicken",
            "sortBy": "fdcId",
            "sortOrder": "asc",
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200


def test_search_foods_response_structure(test_client, sample_search_result):
    """Test that search response has correct structure."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "query": "cabbage",
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        food = data[0]
        assert "fdcId" in food
        assert "dataType" in food
        assert "description" in food
        assert "foodNutrients" in food


def test_get_foods_response_includes_nutrients(test_client, sample_search_result):
    """Test that foods response includes complete nutrient data."""
    with patch("app.services.usda.usda_service.usda_service.search_by_fdcids", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = sample_search_result

        payload = {
            "fdcIds": [2346407],
        }

        response = test_client.post("/internal/usda/foods", json=payload)

        assert response.status_code == 200
        data = response.json()

        food = data[0]
        assert food["foodNutrients"] is not None
        assert len(food["foodNutrients"]) > 0

        # Check nutrient structure
        nutrient = food["foodNutrients"][0]
        assert "nutrientName" in nutrient
        assert "value" in nutrient
        assert "unitName" in nutrient


def test_empty_search_results(test_client):
    """Test handling of empty search results."""
    with patch("app.services.usda.usda_service.usda_service.search_by_criteria", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = []

        payload = {
            "query": "xyznonexistent",
        }

        response = test_client.post("/internal/usda/search", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
