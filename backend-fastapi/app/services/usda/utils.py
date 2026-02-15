"""Utilities for extracting and calculating nutrients from USDA data."""

import json
import logging

logger = logging.getLogger(__name__)


def extract_all_nutrients(usda_data: dict) -> list[dict]:
    """
    Extract all nutrients from raw USDA response.

    Args:
        usda_data: Raw USDA API response dictionary

    Returns:
        List of nutrients: [{"name": "Protein", "amount": 5.2, "unit": "g"}, ...]
    """
    food_nutrients = usda_data.get("foodNutrients", [])
    logger.info(f"extract_all_nutrients: Processing {len(food_nutrients)} nutrients for fdcId={usda_data.get('fdcId')}")

    if food_nutrients:
        logger.debug(f"First nutrient structure: {json.dumps(food_nutrients[0], indent=2, default=str)}")

    nutrients = []

    for i, food_nutrient in enumerate(food_nutrients):
        # Handle both nested (nutrient object) and flat (direct fields) structures
        if "nutrient" in food_nutrient and isinstance(food_nutrient["nutrient"], dict):
            # Nested structure (full FoodNutrient format)
            nutrient = food_nutrient.get("nutrient", {})
            nutrient_name = nutrient.get("name")
            unit_name = nutrient.get("unitName", "")
            amount = food_nutrient.get("amount")
        else:
            # Flat structure (search/list response format)
            nutrient_name = food_nutrient.get("nutrientName")
            unit_name = food_nutrient.get("unitName", "")
            amount = food_nutrient.get("value")

        if nutrient_name and amount is not None:
            nutrients.append({
                "name": nutrient_name,
                "amount": float(amount),
                "unit": unit_name
            })
        else:
            if i < 3:
                logger.debug(f"Skipped nutrient #{i}: name={nutrient_name}, amount={amount}, structure={json.dumps(food_nutrient, indent=2, default=str)}")
                

    logger.info(f"Extracted {len(nutrients)} valid nutrients from {len(food_nutrients)} total")
    return nutrients


def calculate_proportional_nutrients(
    nutrients: list[dict],
    quantity_grams: float
) -> list[dict]:
    """
    Scale nutrients from per-100g to actual quantity.

    Args:
        nutrients: Per-100g nutrient list
        quantity_grams: Actual ingredient quantity in grams

    Returns:
        Scaled nutrient list
    """
    ratio = quantity_grams / 100
    return [
        {
            "name": n["name"],
            "amount": n["amount"] * ratio,
            "unit": n["unit"]
        }
        for n in nutrients
    ]


def sum_nutrients(nutrient_lists: list[list[dict]]) -> list[dict]:
    """
    Sum nutrients across multiple ingredients.

    Args:
        nutrient_lists: List of nutrient lists from different ingredients

    Returns:
        Combined nutrient totals
    """
    totals = {}
    for nutrients in nutrient_lists:
        for nutrient in nutrients:
            name = nutrient["name"]
            if name in totals:
                totals[name]["amount"] += nutrient["amount"]
            else:
                totals[name] = {
                    "name": name,
                    "amount": nutrient["amount"],
                    "unit": nutrient["unit"]
                }

    return list(totals.values())
