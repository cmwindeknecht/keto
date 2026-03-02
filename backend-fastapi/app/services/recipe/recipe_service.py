"""Service for recipe business logic and orchestration."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import DatabaseError, IngredientNotFoundError, RecipeNotFoundError
from app.db.models import Recipe, RecipeIngredient
from app.services.recipe.models.requests import RecipeCreate, RecipeIngredientInput, RecipeUpdate
from app.services.recipe.models.responses import IngredientResponse, NutrientInfo, RecipeIngredientResponse, RecipeResponse
from app.services.usda.models.requests import FoodsByFdcID
from app.services.usda.usda_service import usda_service
from app.services.usda.utils import calculate_proportional_nutrients, extract_all_nutrients, sum_nutrients

logger = logging.getLogger(__name__)


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
            # Initialize the relationship collection to avoid lazy-load issues
            recipe.recipe_ingredients = []
            session.add(recipe)
            await session.flush()

            # Add ingredients to recipe (referenced by USDA FDC ID)
            for ingredient_input in recipe_data.ingredients:
                recipe_ingredient = RecipeIngredient(
                    recipe_id=recipe.id,
                    usda_fdc_id=ingredient_input.usda_fdc_id,
                    quantity_grams=ingredient_input.quantity_grams,
                )
                recipe.recipe_ingredients.append(recipe_ingredient)

            await session.flush()
            await session.commit()
            logger.info(f"Created recipe with ID {recipe.id} and name '{recipe.name}'")
            return await self._recipe_to_response(recipe)
        except IngredientNotFoundError:
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create recipe with name '{recipe_data.name}': {e}")
            raise DatabaseError(f"Failed: {str(e)}") from e

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
            logger.warning(f"Recipe with ID {recipe_id} not found")
            raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

        logger.info(f"Retrieved recipe with ID {recipe_id} and name '{recipe.name}'")
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
                recipe.name = recipe_data.name  # type: ignore[assignment]
            if recipe_data.cuisine is not None:
                recipe.cuisine = recipe_data.cuisine
            if recipe_data.description is not None:
                recipe.description = recipe_data.description  # type: ignore[assignment]

            await session.commit()
            await session.refresh(recipe, ["recipe_ingredients"])
            logger.info(f"Updated recipe with ID {recipe_id} and name '{recipe.name}'")
            return await self._recipe_to_response(recipe)
        except (RecipeNotFoundError, IngredientNotFoundError):
            logger.warning(f"Recipe with ID {recipe_id} not found for update or ingredients not found")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update recipe with ID {recipe_id}: {e}")
            raise DatabaseError(f"Failed to update recipe: {str(e)}") from e

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
            logger.info(f"Deleted recipe with ID {recipe_id} and name '{recipe.name}'")
        except RecipeNotFoundError:
            logger.warning(f"Recipe with ID {recipe_id} not found for deletion")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to delete recipe with ID {recipe_id}: {e}")
            raise DatabaseError(f"Failed to delete recipe: {str(e)}") from e

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
            logger.info(f"Listed {len(recipes)} recipes with cuisine filter '{cuisine}'")
            return [await self._recipe_to_response(recipe) for recipe in recipes]
        except Exception as e:
            logger.error(f"Failed to list recipes with cuisine filter '{cuisine}': {e}")
            raise DatabaseError(f"Failed to list recipes: {str(e)}") from e

    async def add_ingredient_to_recipe(self, session: AsyncSession, recipe_id: int, ingredient_input: RecipeIngredientInput) -> RecipeResponse:
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
            recipe.recipe_ingredients.append(recipe_ingredient)
            await session.flush()
            await session.commit()
            logger.info(f"Added ingredient with USDA FDC ID {ingredient_input.usda_fdc_id} to recipe ID {recipe_id}")
            return await self._recipe_to_response(recipe)
        except (RecipeNotFoundError, IngredientNotFoundError):
            await session.rollback()
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to add ingredient to recipe {recipe_id}: {e}")
            raise DatabaseError(f"Failed to add ingredient: {str(e)}") from e

    async def update_ingredient_in_recipe(
        self, session: AsyncSession, recipe_id: int, ingredient_id: int, ingredient_input: RecipeIngredientInput
    ) -> RecipeResponse:
        """
        Update an ingredient's quantity in a recipe.

        Args:
            session: Database session
            recipe_id: ID of recipe
            ingredient_id: ID of recipe_ingredient to update (from RecipeIngredient.id)
            ingredient_input: Updated ingredient quantity

        Returns:
            Updated recipe response

        Raises:
            RecipeNotFoundError: If recipe not found
            IngredientNotFoundError: If ingredient not in recipe
            DatabaseError: If operation fails
        """
        try:
            stmt = select(Recipe).where(Recipe.id == recipe_id)
            result = await session.execute(stmt)
            recipe = result.scalar_one_or_none()

            if not recipe:
                raise RecipeNotFoundError(f"Recipe with ID {recipe_id} not found")

            stmt = select(RecipeIngredient).where((RecipeIngredient.recipe_id == recipe_id) & (RecipeIngredient.id == ingredient_id))
            result = await session.execute(stmt)
            recipe_ingredient = result.scalar_one_or_none()

            if not recipe_ingredient:
                raise IngredientNotFoundError(f"Ingredient {ingredient_id} not in recipe {recipe_id}")

            recipe_ingredient.quantity_grams = ingredient_input.quantity_grams
            await session.flush()
            await session.commit()
            logger.info(f"Updated ingredient with ID {ingredient_id} in recipe ID {recipe_id} to {ingredient_input.quantity_grams}g")
            return await self._recipe_to_response(recipe)
        except (RecipeNotFoundError, IngredientNotFoundError):
            logger.warning(f"Recipe with ID {recipe_id} or ingredient with ID {ingredient_id} not found for update")
            raise
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update ingredient {ingredient_id} in recipe {recipe_id}: {e}")
            raise DatabaseError(f"Failed to update ingredient: {str(e)}") from e

    async def remove_ingredient_from_recipe(self, session: AsyncSession, recipe_id: int, ingredient_id: int) -> RecipeResponse:
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

            stmt = select(RecipeIngredient).where((RecipeIngredient.recipe_id == recipe_id) & (RecipeIngredient.id == ingredient_id))
            result = await session.execute(stmt)
            recipe_ingredient = result.scalar_one_or_none()

            if not recipe_ingredient:
                raise IngredientNotFoundError(f"Ingredient {ingredient_id} not in recipe {recipe_id}")

            recipe.recipe_ingredients.remove(recipe_ingredient)
            await session.flush()
            await session.commit()
            logger.info(f"Removed ingredient with ID {ingredient_id} from recipe ID {recipe_id}")
        except (RecipeNotFoundError, IngredientNotFoundError):
            logger.warning(f"Recipe with ID {recipe_id} or ingredient with ID {ingredient_id} not found for removal")
            raise
        except Exception as e:
            logger.error(f"Failed to remove ingredient {ingredient_id} from recipe {recipe_id}: {e}")
            await session.rollback()
            raise DatabaseError(f"Failed to remove ingredient: {str(e)}") from e

        return await self._recipe_to_response(recipe)

    async def _recipe_to_response(self, recipe: Recipe) -> RecipeResponse:
        """
        Convert Recipe ORM model to RecipeResponse with calculated nutrition totals.

        Fetches ingredient data from cache/USDA, extracts nutrients, and calculates totals on-the-fly.

        Args:
            recipe: Recipe ORM model

        Returns:
            Recipe response with ingredients and complete nutrient breakdown
        """
        # Fetch ingredient data from cache/USDA
        fdc_ids = [ri.usda_fdc_id for ri in recipe.recipe_ingredients]
        if not fdc_ids:
            response_dict = {
                "id": recipe.id,
                "name": recipe.name,
                "cuisine": recipe.cuisine,
                "description": recipe.description,
                "ingredients": [],
                "nutrients": [],
                "created_at": recipe.created_at,
                "updated_at": recipe.updated_at,
            }
            return RecipeResponse.model_validate(response_dict)

        criteria = FoodsByFdcID(fdcIds=fdc_ids, format="full")
        usda_results = await usda_service.search_by_fdcids(criteria)

        # Map results by FDC ID
        usda_map = {item["fdcId"]: item for item in usda_results}

        # Validate all ingredients were found in cache/USDA
        missing_fdc_ids = [fdc_id for fdc_id in fdc_ids if fdc_id not in usda_map]
        if missing_fdc_ids:
            raise IngredientNotFoundError(f"Ingredients not found in cache or USDA database: {missing_fdc_ids}")

        recipe_ingredients = []
        all_nutrients = []

        for recipe_ingredient in recipe.recipe_ingredients:
            usda_fdc_id = recipe_ingredient.usda_fdc_id
            quantity_grams = recipe_ingredient.quantity_grams

            usda_data = usda_map.get(usda_fdc_id)
            if not usda_data:
                continue

            # Extract per-100g nutrients
            per_100g_nutrients = extract_all_nutrients(usda_data)

            # Scale to actual quantity
            scaled_nutrients = calculate_proportional_nutrients(per_100g_nutrients, quantity_grams)

            # Add to total
            all_nutrients.append(scaled_nutrients)

            # Convert dicts to NutrientInfo objects
            per_100g_nutrient_info = [NutrientInfo(**n) for n in per_100g_nutrients]
            scaled_nutrient_info = [NutrientInfo(**n) for n in scaled_nutrients]

            # Build response
            ingredient_resp = IngredientResponse(
                usda_fdc_id=usda_fdc_id,
                name=usda_data.get("description", "Unknown"),
                data_type=usda_data.get("dataType"),
                brand_owner=usda_data.get("brandOwner"),
                nutrients=per_100g_nutrient_info,
            )
            recipe_ingredient_resp = RecipeIngredientResponse(
                id=recipe_ingredient.id,
                ingredient=ingredient_resp,
                quantity_grams=quantity_grams,
                nutrients=scaled_nutrient_info,
            )
            recipe_ingredients.append(recipe_ingredient_resp)

        # Sum nutrients across all ingredients
        total_nutrients = sum_nutrients(all_nutrients)
        nutrient_info_list = [NutrientInfo(**nutrient) for nutrient in total_nutrients]

        # Build response dict from ORM object
        response_dict = {
            "id": recipe.id,
            "name": recipe.name,
            "cuisine": recipe.cuisine,
            "description": recipe.description,
            "ingredients": recipe_ingredients,
            "nutrients": nutrient_info_list,
            "created_at": recipe.created_at,
            "updated_at": recipe.updated_at,
        }
        return RecipeResponse.model_validate(response_dict)


recipe_service = RecipeService()
