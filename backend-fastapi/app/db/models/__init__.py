from datetime import datetime
from enum import Enum

from sqlalchemy import JSON, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class Cuisine(str, Enum):
    """Cuisine types for recipes. Serializes cleanly to JSON."""

    MEXICAN = "MEXICAN"
    AMERICAN = "AMERICAN"
    ITALIAN = "ITALIAN"
    ASIAN = "ASIAN"
    INDIAN = "INDIAN"
    MEDITERRANEAN = "MEDITERRANEAN"
    THAI = "THAI"
    JAPANESE = "JAPANESE"
    FRENCH = "FRENCH"
    GREEK = "GREEK"
    MIDDLE_EASTERN = "MIDDLE_EASTERN"
    CARIBBEAN = "CARIBBEAN"
    AFRICAN = "AFRICAN"
    OTHER = "OTHER"


class Recipe(Base):
    """
    Recipe model for storing user-created recipes.

    Ingredients are referenced by USDA FDC ID, with nutrition data fetched from Redis cache.
    Nutrients are calculated on-the-fly from cached ingredient data:
    - Get all recipe_ingredients (with usda_fdc_id and quantity_grams)
    - Look up each ingredient from Redis (30-day TTL)
    - Multiply nutrient values by (quantity_grams / 100) to get contribution
    - Sum for recipe totals
    - Divide by servings for per-serving values
    """

    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    cuisine = Column(SQLEnum(Cuisine), nullable=False, default=Cuisine.OTHER)
    description = Column(String, nullable=True)
    servings = Column(Integer, nullable=False, default=1)
    rating = Column(Integer, nullable=False, default=0)  # 0-100 keto rating
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan", lazy="selectin")


class RecipeIngredient(Base):
    """
    Junction table linking recipes to ingredients (by USDA FDC ID) with quantity information.

    Stores usda_fdc_id directly instead of a foreign key, since ingredient data
    is cached in Redis, not persisted in the database.

    quantity_grams is always in grams (standardized).
    To calculate ingredient contribution to recipe:
    - Fetch ingredient from Redis by usda_fdc_id
    - nutrient_contribution = ingredient_nutrient_per_100g * (quantity_grams / 100)
    """

    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    usda_fdc_id = Column(Integer, nullable=False)  # Reference to USDA FoodData Central ID
    quantity_grams = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recipe = relationship("Recipe", back_populates="recipe_ingredients")

    __table_args__ = (UniqueConstraint("recipe_id", "usda_fdc_id", name="unique_recipe_ingredient"),)
