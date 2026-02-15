"""Transformers to convert USDA API responses into cached ingredient models."""

from .models import CachedIngredient, CachedNutrient


def to_cached_ingredient(usda_data: dict) -> CachedIngredient:
    """
    Transform a USDA API response into a CachedIngredient.

    USDA responses include foodNutrients as a list with nutrientNumber, value, unitName.
    We extract the relevant nutrients for keto tracking.

    Args:
        usda_data: Raw USDA API response dictionary

    Returns:
        CachedIngredient with normalized per-100g nutrient data
    """
    fdc_id = usda_data.get("fdcId")
    name = usda_data.get("description", "Unknown")
    data_type = usda_data.get("dataType", "Unknown")
    brand_owner = usda_data.get("brandOwner")

    # Extract nutrients from USDA response
    # USDA provides: {"foodNutrients": [{"nutrient": {"name": "...", "unitName": "..."}, "value": ...}, ...]}
    nutrients = []
    food_nutrients = usda_data.get("foodNutrients", [])

    # Map USDA nutrient numbers to our nutrient types
    nutrient_mapping = {
        "Energy": "calories",
        "Protein": "protein",
        "Total lipid (fat)": "fat",
        "Carbohydrate, by difference": "carbs",
        "Fiber, total dietary": "fiber",
        "Sodium, Na": "sodium",
        "Potassium, K": "potassium",
        "Calcium, Ca": "calcium",
        "Iron, Fe": "iron",
        "Magnesium, Mg": "magnesium",
        "Zinc, Zn": "zinc",
        "Vitamin A, RAE": "vitamin_a",
        "Vitamin B12 (cyanocobalamin)": "vitamin_b12",
        "Vitamin D (D2 + D3)": "vitamin_d",
        "Vitamin K (phylloquinone)": "vitamin_k",
    }

    for food_nutrient in food_nutrients:
        nutrient_info = food_nutrient.get("nutrient", {})
        nutrient_name = nutrient_info.get("name", "")
        nutrient_number = nutrient_info.get("number")

        # Check if this is a nutrient we care about
        if nutrient_name in nutrient_mapping:
            nutrient_type = nutrient_mapping[nutrient_name]
            value = food_nutrient.get("value")
            unit_name = nutrient_info.get("unitName", "")

            if value is not None:
                # Normalize unit names
                unit = normalize_unit(unit_name)
                nutrients.append(
                    CachedNutrient(
                        nutrient_type=nutrient_type,
                        amount=value,
                        unit=unit
                    )
                )

    return CachedIngredient(
        fdc_id=fdc_id,
        name=name,
        nutrients=nutrients,
        brand_owner=brand_owner,
        data_type=data_type
    )


def normalize_unit(unit: str) -> str:
    """
    Normalize USDA unit names to standard abbreviations.

    Args:
        unit: Raw unit name from USDA

    Returns:
        Normalized unit abbreviation
    """
    unit = unit.lower().strip()

    unit_mapping = {
        "g": "g",
        "gram": "g",
        "grams": "g",
        "mg": "mg",
        "milligram": "mg",
        "milligrams": "mg",
        "ug": "ug",
        "micrograms": "ug",
        "kcal": "kcal",
        "kj": "kj",
        "iu": "iu",
    }

    return unit_mapping.get(unit, unit)
