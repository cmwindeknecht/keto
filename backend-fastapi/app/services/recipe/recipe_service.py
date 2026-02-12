"""Service for recipe business logic and orchestration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import RecipeNotFoundError, IngredientNotFoundError, DatabaseError
from app.db.models import Recipe, RecipeIngredient
from app.routes.models.requests import RecipeCreate, RecipeUpdate, RecipeIngredientInput
from app.routes.models.responses import RecipeResponse, RecipeIngredientResponse, IngredientResponse
from app.services.usda.usda_service import usda_service


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

            # Add ingredients to recipe (referenced by USDA FDC ID)
            for ingredient_input in recipe_data.ingredients:
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    usda_fdc_id=ingredient_input.usda_fdc_id,
                    quantity_grams=ingredient_input.quantity_grams,
                )
                session.add(recipe_ingredient)

            await session.refresh(recipe, ["recipe_ingredients"])
            await session.commit()
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
            ingredient_input: Ingredient (by USDA FDC ID) and quantity

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

            recipe_ingredient = RecipeIngredient(
                recipe_id=recipe_id,
                usda_fdc_id=ingredient_input.usda_fdc_id,
                quantity_grams=ingredient_input.quantity_grams,
            )
            session.add(recipe_ingredient)
            await session.refresh(recipe, ["recipe_ingredients"])
            await session.commit()
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
            ingredient_id: ID of recipe_ingredient to remove (from RecipeIngredient.id)

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
                (RecipeIngredient.recipe_id == recipe_id) & (RecipeIngredient.id == ingredient_id)
            )
            result = await session.execute(stmt)
            recipe_ingredient = result.scalar_one_or_none()

            if not recipe_ingredient:
                raise IngredientNotFoundError(f"Ingredient {ingredient_id} not in recipe {recipe_id}")

            await session.delete(recipe_ingredient)
            await session.refresh(recipe, ["recipe_ingredients"])
            await session.commit()
            return await self._recipe_to_response(recipe)
        except (RecipeNotFoundError, IngredientNotFoundError):
            raise
        except Exception as e:
            await session.rollback()
            raise DatabaseError(f"Failed to remove ingredient: {str(e)}")

    async def _recipe_to_response(self, recipe: Recipe) -> RecipeResponse:
        """
        Convert Recipe ORM model to RecipeResponse with calculated nutrition totals.

        Fetches ingredient data from Redis cache for each recipe ingredient.

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
            usda_fdc_id = recipe_ingredient.usda_fdc_id
            quantity_grams = recipe_ingredient.quantity_grams

            # Fetch ingredient from cache
            cached_ingredient = await usda_service.get_ingredient_with_cache(usda_fdc_id)

            # Extract nutrients from cached data
            nutrients_dict = {n.nutrient_type: n.amount for n in cached_ingredient.nutrients}
            calories = nutrients_dict.get("calories", 0)
            protein = nutrients_dict.get("protein", 0)
            fat = nutrients_dict.get("fat", 0)
            carbs = nutrients_dict.get("carbs", 0)
            fiber = nutrients_dict.get("fiber", 0)

            # Calculate contribution based on quantity
            ratio = quantity_grams / 100
            calories *= ratio
            protein *= ratio
            fat *= ratio
            carbs *= ratio
            fiber *= ratio

            total_calories += calories
            total_protein += protein
            total_fat += fat
            total_carbs += carbs
            total_fiber += fiber

            recipe_ingredients.append(
                RecipeIngredientResponse(
                    id=recipe_ingredient.id,
                    ingredient=IngredientResponse(
                        usda_fdc_id=usda_fdc_id,
                        name=cached_ingredient.name,
                        calories_per_100g=nutrients_dict.get("calories", 0),
                        protein_per_100g=nutrients_dict.get("protein", 0),
                        fat_per_100g=nutrients_dict.get("fat", 0),
                        carbs_per_100g=nutrients_dict.get("carbs", 0),
                        fiber_per_100g=nutrients_dict.get("fiber", 0),
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
