from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import RecipeNotFoundError, IngredientNotFoundError, DatabaseError
from app.db.models import Recipe, Ingredient, RecipeIngredient
from app.routes.models.requests import RecipeCreate, RecipeUpdate, RecipeIngredientInput
from app.routes.models.responses import RecipeResponse, RecipeIngredientResponse, IngredientResponse
from app.services.usda_service import usda_service


class RecipeService:
    """Service for recipe business logic and orchestration."""

    async def create_recipe(self, session: AsyncSession, recipe_data: RecipeCreate) -> RecipeResponse:
        """
        Create a new recipe with ingredients.

        Args:
            session: Database session
            recipe_data: Recipe creation data

        Returns:
            Created recipe response

        Raises:
            DatabaseError: If creation fails
            IngredientNotFoundError: If an ingredient doesn't exist in database
        """
        try:
            # Create recipe record
            recipe = Recipe(
                name=recipe_data.name,
                cuisine=recipe_data.cuisine,
                description=recipe_data.description,
            )
            session.add(recipe)
            await session.flush()

            # Add ingredients to recipe
            for ingredient_input in recipe_data.ingredients:
                ingredient = await self._get_or_create_ingredient(session, ingredient_input.usda_fdc_id)
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    ingredient_id=ingredient.id,
                    quantity_grams=ingredient_input.quantity_grams,
                )
                session.add(recipe_ingredient)

            await session.commit()
            await session.refresh(recipe, ["recipe_ingredients"])
            return await self._recipe_to_response(recipe)
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to create recipe: {str(e)}")

    async def get_recipe(self, session: AsyncSession, recipe_id: int) -> RecipeResponse:
        """
        Get a recipe by ID with all ingredients and nutrition calculated.

        Args:
            session: Database session
            recipe_id: ID of recipe to retrieve

        Returns:
            Recipe response with ingredients and totals

        Raises:
            RecipeNotFoundError: If recipe not found
        """
        stmt = select(Recipe).where(Recipe.id == recipe_id).options(selectinload(Recipe.recipe_ingredients))
        result = await session.execute(stmt)
        recipe = result.scalar_one_or_none()

        if not recipe:
            raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

        return await self._recipe_to_response(recipe)

    async def update_recipe(self, session: AsyncSession, recipe_id: int, recipe_data: RecipeUpdate) -> RecipeResponse:
        """
        Update recipe details.

        Args:
            session: Database session
            recipe_id: ID of recipe to update
            recipe_data: Update data

        Returns:
            Updated recipe response

        Raises:
            RecipeNotFoundError: If recipe not found
            DatabaseError: If update fails
        """
        try:
            stmt = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

            if recipe_data.name is not None:
                recipe.name = recipe_data.name
            if recipe_data.cuisine is not None:
                recipe.cuisine = recipe_data.cuisine
            if recipe_data.description is not None:
                recipe.description = recipe_data.description

            await session.commit()
            await session.refresh(recipe, ["recipe_ingredients"])
            return await self._recipe_to_response(recipe)
        except RecipeNotFoundError:
            raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to update recipe: {str(e)}")

    async def delete_recipe(self, session: AsyncSession, recipe_id: int) -> None:
        """
        Delete a recipe and its ingredients.

        Args:
            session: Database session
            recipe_id: ID of recipe to delete

        Raises:
            RecipeNotFoundError: If recipe not found
            DatabaseError: If deletion fails
        """
        try:
            stmt = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

            await session.delete(recipe)
            await session.commit()
        except RecipeNotFoundError:
            raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to delete recipe: {str(e)}")

    async def list_recipes(self, session: AsyncSession, cuisine: str | None = None) -> list[RecipeResponse]:
        """
        List all recipes, optionally filtered by cuisine.

        Args:
            session: Database session
            cuisine: Optional cuisine to filter by

        Returns:
            List of recipe responses

        Raises:
            DatabaseError: If query fails
        """
        try:
            stmt = select(Recipe).options(selectinload(Recipe.recipe_ingredients))
            if cuisine:
                stmt = stmt.where(Recipe.cuisine == cuisine)
            result = await session.execute(stmt)
            recipes = result.scalars().all()
            return [await self._recipe_to_response(recipe) for recipe in recipes]
        except Exception as e:
            raise DatabaseError(f"Failed to list recipes: {str(e)}")

    async def add_ingredient_to_recipe(
        self, session: AsyncSession, recipe_id: int, ingredient_input: RecipeIngredientInput
    ) -> RecipeResponse:
        """
        Add an ingredient to an existing recipe.

        Args:
            session: Database session
            recipe_id: ID of recipe to add ingredient to
            ingredient_input: Ingredient and quantity

        Returns:
            Updated recipe response

        Raises:
            RecipeNotFoundError: If recipe not found
            DatabaseError: If operation fails
        """
        try:
            stmt = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

            ingredient = await self._get_or_create_ingredient(session, ingredient_input.usda_fdc_id)
            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe_id,
                ingredient_id=ingredient.id,
                quantity_grams=ingredient_input.quantity_grams,
            )
            session.add(recipe_ingredient)
            await session.commit()
            await session.refresh(recipe, ["recipe_ingredients"])
            return await self._recipe_to_response(recipe)
        except RecipeNotFoundError:
            raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to add ingredient: {str(e)}")

    async def remove_ingredient_from_recipe(
        self, session: AsyncSession, recipe_id: int, ingredient_id: int
    ) -> RecipeResponse:
        """
        Remove an ingredient from a recipe.

        Args:
            session: Database session
            recipe_id: ID of recipe
            ingredient_id: ID of ingredient to remove

        Returns:
            Updated recipe response

        Raises:
            RecipeNotFoundError: If recipe not found
            DatabaseError: If operation fails
        """
        try:
            stmt = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

            stmt = select(RecipeIngredient).where(
                (RecipeIngredient.recipe_id == recipe_id) & (RecipeIngredient.ingredient_id == ingredient_id)
            )
            result = await session.execute(stmt)
            recipe_ingredient = result.scalar_one_or_none()

            if not recipe_ingredient:
                raise IngredientNotFoundError(f"Ingredient {ingredient_id} not in recipe {recipe_id}")

            await session.delete(recipe_ingredient)
            await session.commit()
            await session.refresh(recipe, ["recipe_ingredients"])
            return await self._recipe_to_response(recipe)
        except (RecipeNotFoundError, IngredientNotFoundError):
            raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to remove ingredient: {str(e)}")

    async def _get_or_create_ingredient(self, session: AsyncSession, usda_fdc_id: str) -> Ingredient:
        """
        Get ingredient from database or create it by fetching from USDA API.

        Args:
            session: Database session
            usda_fdc_id: USDA FoodData Central ID

        Returns:
            Ingredient model

        Raises:
            IngredientNotFoundError: If USDA API fails to find ingredient
            DatabaseError: If database operation fails
        """
        # Check if ingredient already exists
        stmt = select(Ingredient).where(Ingredient.usda_fdc_id == usda_fdc_id)
        result = await session.execute(stmt)
        ingredient = result.scalar_one_or_none()

        if ingredient:
            return ingredient

        # Fetch from USDA API
        usda_data = await usda_service.get_ingredient_details(usda_fdc_id)

        # Extract nutrition data from USDA response
        nutrients = {nutrient["nutrientId"]: nutrient.get("value", 0) for nutrient in usda_data.get("foodNutrients", [])}

        # USDA nutrient IDs:
        # 1008 = Energy (kcal)
        # 1003 = Protein (g)
        # 1004 = Total lipid (fat) (g)
        # 1005 = Carbohydrates (g)
        # 1079 = Fiber (g)
        ingredient = Ingredient(
            usda_fdc_id=usda_fdc_id,
            name=usda_data.get("description", "Unknown"),
            calories_per_100g=nutrients.get(1008, 0),
            protein_per_100g=nutrients.get(1003, 0),
            fat_per_100g=nutrients.get(1004, 0),
            carbs_per_100g=nutrients.get(1005, 0),
            fiber_per_100g=nutrients.get(1079, 0),
        )
        session.add(ingredient)
        await session.flush()
        return ingredient

    async def _recipe_to_response(self, recipe: Recipe) -> RecipeResponse:
        """
        Convert Recipe ORM model to RecipeResponse with calculated nutrition totals.

        Args:
            recipe: Recipe ORM model

        Returns:
            Recipe response with ingredients and nutrition totals
        """
        recipe_ingredients = []
        total_calories = 0
        total_protein = 0
        total_fat = 0
        total_carbs = 0
        total_fiber = 0

        for recipe_ingredient in recipe.recipe_ingredients:
            ingredient = recipe_ingredient.ingredient
            quantity_grams = recipe_ingredient.quantity_grams
            ratio = quantity_grams / 100

            calories = ingredient.calories_per_100g * ratio
            protein = ingredient.protein_per_100g * ratio
            fat = ingredient.fat_per_100g * ratio
            carbs = ingredient.carbs_per_100g * ratio
            fiber = ingredient.fiber_per_100g * ratio

            total_calories += calories
            total_protein += protein
            total_fat += fat
            total_carbs += carbs
            total_fiber += fiber

            recipe_ingredients.append(
                RecipeIngredientResponse(
                    ingredient=IngredientResponse(
                        id=ingredient.id,
                        usda_fdc_id=ingredient.usda_fdc_id,
                        name=ingredient.name,
                        calories_per_100g=ingredient.calories_per_100g,
                        protein_per_100g=ingredient.protein_per_100g,
                        fat_per_100g=ingredient.fat_per_100g,
                        carbs_per_100g=ingredient.carbs_per_100g,
                        fiber_per_100g=ingredient.fiber_per_100g,
                    ),
                    quantity_grams=quantity_grams,
                    calories=calories,
                    protein=protein,
                    fat=fat,
                    carbs=carbs,
                    fiber=fiber,
                )
            )

        return RecipeResponse(
            id=recipe.id,
            name=recipe.name,
            cuisine=recipe.cuisine,
            description=recipe.description,
            ingredients=recipe_ingredients,
            total_calories=total_calories,
            total_protein=total_protein,
            total_fat=total_fat,
            total_carbs=total_carbs,
            total_fiber=total_fiber,
            created_at=recipe.created_at,
            updated_at=recipe.updated_at,
        )


recipe_service = RecipeService()
