from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Float, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


class Cuisine(str, Enum):
    """Cuisine types for recipes."""
    MEXICAN = "Mexican"
    AMERICAN = "American"
    ITALIAN = "Italian"
    ASIAN = "Asian"
    INDIAN = "Indian"
    MEDITERRANEAN = "Mediterranean"
    THAI = "Thai"
    JAPANESE = "Japanese"
    FRENCH = "French"
    GREEK = "Greek"
    MIDDLE_EASTERN = "Middle Eastern"
    CARIBBEAN = "Caribbean"
    AFRICAN = "African"
    OTHER = "Other"


class Recipe(Base):
    """Recipe model for storing user-created recipes."""
    __tablename__ = "recipes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    cuisine = Column(String, nullable=False, default=Cuisine.OTHER)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    recipe_ingredients = relationship("RecipeIngredient", back_populates="recipe", cascade="all, delete-orphan")


class Ingredient(Base):
    """Ingredient model storing nutrition data from USDA FoodData Central."""
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    usda_fdc_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False, index=True)
    calories_per_100g = Column(Float, nullable=False)
    protein_per_100g = Column(Float, nullable=False)
    fat_per_100g = Column(Float, nullable=False)
    carbs_per_100g = Column(Float, nullable=False)
    fiber_per_100g = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    recipe_ingredients = relationship("RecipeIngredient", back_populates="ingredient", cascade="all, delete-orphan")


class RecipeIngredient(Base):
    """Junction table for recipes and ingredients with quantity information."""
    __tablename__ = "recipe_ingredients"

    id = Column(Integer, primary_key=True, index=True)
    recipe_id = Column(Integer, ForeignKey("recipes.id"), nullable=False)
    ingredient_id = Column(Integer, ForeignKey("ingredients.id"), nullable=False)
    quantity_grams = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    recipe = relationship("Recipe", back_populates="recipe_ingredients")
    ingredient = relationship("Ingredient", back_populates="recipe_ingredients")

    __table_args__ = (UniqueConstraint("recipe_id", "ingredient_id", name="unique_recipe_ingredient"),)
