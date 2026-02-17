"""Unit tests for USDA utilities."""

import pytest

from app.services.usda.utils import calculate_proportional_nutrients, extract_all_nutrients, sum_nutrients


@pytest.fixture
def sample_usda_data():
    """Sample USDA API response data."""
    return {
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
    }


def test_extract_all_nutrients_with_nested_structure():
    """Test extracting nutrients from nested structure."""
    usda_data = {
        "foodNutrients": [
            {
                "amount": 10.5,
                "nutrient": {
                    "name": "Protein",
                    "unitName": "g",
                },
            },
            {
                "amount": 5.2,
                "nutrient": {
                    "name": "Fat",
                    "unitName": "g",
                },
            },
        ]
    }

    nutrients = extract_all_nutrients(usda_data)

    assert len(nutrients) == 2
    assert nutrients[0]["name"] == "Protein"
    assert nutrients[0]["amount"] == 10.5
    assert nutrients[1]["name"] == "Fat"


def test_extract_all_nutrients_with_flat_structure():
    """Test extracting nutrients from flat structure."""
    usda_data = {
        "foodNutrients": [
            {
                "nutrientId": 1003,
                "nutrientName": "Protein",
                "value": 0.961,
                "unitName": "G",
            },
            {
                "nutrientId": 1004,
                "nutrientName": "Fat",
                "value": 0.228,
                "unitName": "G",
            },
        ]
    }

    nutrients = extract_all_nutrients(usda_data)

    assert len(nutrients) == 2
    assert nutrients[0]["name"] == "Protein"
    assert nutrients[0]["amount"] == 0.961
    assert nutrients[1]["name"] == "Fat"


def test_extract_all_nutrients_empty():
    """Test extracting when no nutrients."""
    usda_data: dict = {"foodNutrients": []}

    nutrients = extract_all_nutrients(usda_data)

    assert nutrients == []


def test_calculate_proportional_nutrients():
    """Test scaling nutrients to quantity."""
    nutrients = [
        {"name": "Protein", "amount": 1.0, "unit": "g"},
        {"name": "Fat", "amount": 2.0, "unit": "g"},
        {"name": "Carbs", "amount": 5.0, "unit": "g"},
    ]

    # Scale 100g data to 200g (2x)
    scaled = calculate_proportional_nutrients(nutrients, 200)

    assert len(scaled) == 3
    assert scaled[0]["amount"] == 2.0
    assert scaled[1]["amount"] == 4.0
    assert scaled[2]["amount"] == 10.0


def test_calculate_proportional_nutrients_half():
    """Test scaling nutrients to half quantity."""
    nutrients = [
        {"name": "Protein", "amount": 10.0, "unit": "g"},
        {"name": "Fat", "amount": 5.0, "unit": "g"},
    ]

    # Scale 100g data to 50g (0.5x)
    scaled = calculate_proportional_nutrients(nutrients, 50)

    assert scaled[0]["amount"] == 5.0
    assert scaled[1]["amount"] == 2.5


def test_sum_nutrients_single_ingredient():
    """Test summing nutrients from single ingredient."""
    nutrient_lists = [
        [
            {"name": "Protein", "amount": 5.0, "unit": "g"},
            {"name": "Fat", "amount": 2.0, "unit": "g"},
        ]
    ]

    totals = sum_nutrients(nutrient_lists)

    assert len(totals) == 2
    assert totals[0]["amount"] == 5.0
    assert totals[1]["amount"] == 2.0


def test_sum_nutrients_multiple_ingredients():
    """Test summing nutrients from multiple ingredients."""
    nutrient_lists = [
        [
            {"name": "Protein", "amount": 5.0, "unit": "g"},
            {"name": "Fat", "amount": 2.0, "unit": "g"},
        ],
        [
            {"name": "Protein", "amount": 3.0, "unit": "g"},
            {"name": "Fat", "amount": 1.5, "unit": "g"},
            {"name": "Carbs", "amount": 10.0, "unit": "g"},
        ],
    ]

    totals = sum_nutrients(nutrient_lists)

    # Should have 3 unique nutrients
    assert len(totals) == 3

    # Check totals
    protein_total = next(n for n in totals if n["name"] == "Protein")
    fat_total = next(n for n in totals if n["name"] == "Fat")
    carbs_total = next(n for n in totals if n["name"] == "Carbs")

    assert protein_total["amount"] == 8.0
    assert fat_total["amount"] == 3.5
    assert carbs_total["amount"] == 10.0


def test_sum_nutrients_empty():
    """Test summing empty nutrient lists."""
    totals = sum_nutrients([])
    assert totals == []


def test_sum_nutrients_preserves_units():
    """Test that units are preserved during summation."""
    nutrient_lists = [
        [
            {"name": "Protein", "amount": 5.0, "unit": "g"},
            {"name": "Iron", "amount": 2.5, "unit": "mg"},
        ],
        [
            {"name": "Protein", "amount": 3.0, "unit": "g"},
            {"name": "Iron", "amount": 1.5, "unit": "mg"},
        ],
    ]

    totals = sum_nutrients(nutrient_lists)

    protein = next(n for n in totals if n["name"] == "Protein")
    iron = next(n for n in totals if n["name"] == "Iron")

    assert protein["unit"] == "g"
    assert iron["unit"] == "mg"
