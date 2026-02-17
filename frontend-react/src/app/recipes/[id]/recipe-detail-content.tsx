"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  useGetRecipeQuery,
  useUpdateRecipeMutation,
  useDeleteRecipeMutation,
  useAddIngredientMutation,
  useRemoveIngredientMutation,
} from "@/store/api/recipesApi";
import { useSearchMutation } from "@/store/api/usdaApi";
import { NutrientTable } from "@/components/NutrientTable";
import type { Ingredient, Nutrient } from "@/store/api/recipesApi";

interface RecipeDetailContentProps {
  id: string;
}

export function RecipeDetailContent({ id }: RecipeDetailContentProps) {
  const router = useRouter();
  const { data: recipe, isLoading, error } = useGetRecipeQuery(id);
  const [updateRecipe, { isLoading: isUpdating }] = useUpdateRecipeMutation();
  const [deleteRecipe, { isLoading: isDeleting }] = useDeleteRecipeMutation();
  const [addIngredient, { isLoading: isAddingIngredient }] = useAddIngredientMutation();
  const [removeIngredient, { isLoading: isRemovingIngredient }] = useRemoveIngredientMutation();
  const [searchUSDA, { isLoading: isSearching }] = useSearchMutation();

  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({
    name: recipe?.name || "",
    cuisine: recipe?.cuisine || "",
    description: recipe?.description || "",
  });
  const [showAddIngredient, setShowAddIngredient] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedUSDAFood, setSelectedUSDAFood] = useState<any>(null);
  const [ingredientQuantity, setIngredientQuantity] = useState(100);

  const handleUpdateRecipe = async () => {
    try {
      await updateRecipe({
        id,
        body: {
          name: editData.name,
          cuisine: editData.cuisine,
          description: editData.description,
        },
      }).unwrap();
      setEditMode(false);
    } catch (err) {
      console.error("Error updating recipe:", err);
    }
  };

  const handleDeleteRecipe = async () => {
    if (confirm("Are you sure you want to delete this recipe?")) {
      try {
        await deleteRecipe(id).unwrap();
        router.push("/recipes");
      } catch (err) {
        console.error("Error deleting recipe:", err);
      }
    }
  };

  const handleSearchUSDA = async () => {
    if (!searchQuery.trim()) return;
    try {
      const result = await searchUSDA({ query: searchQuery }).unwrap();
      setSearchResults(result.foods);
    } catch (err) {
      console.error("Error searching USDA:", err);
    }
  };

  const handleAddIngredient = async () => {
    if (!selectedUSDAFood) return;
    try {
      await addIngredient({
        id,
        body: {
          fdc_id: selectedUSDAFood.fdc_id,
          name: selectedUSDAFood.description,
          quantity_grams: ingredientQuantity,
          foodNutrients: selectedUSDAFood.foodNutrients,
        },
      }).unwrap();
      setSelectedUSDAFood(null);
      setSearchQuery("");
      setSearchResults([]);
      setIngredientQuantity(100);
      setShowAddIngredient(false);
    } catch (err) {
      console.error("Error adding ingredient:", err);
    }
  };

  const handleRemoveIngredient = async (ingredientId: string) => {
    if (confirm("Remove this ingredient?")) {
      try {
        await removeIngredient({
          recipeId: id,
          ingredientId,
        }).unwrap();
      } catch (err) {
        console.error("Error removing ingredient:", err);
      }
    }
  };

  if (isLoading) return <div className="text-center py-8">Loading recipe...</div>;
  if (error || !recipe) return <div className="text-center py-8 text-red-600">Recipe not found</div>;

  // Calculate aggregate nutrients
  const aggregateNutrients: Nutrient[] = [];
  const nutrientMap = new Map<number, Nutrient>();

  recipe.ingredients?.forEach((ingredient: Ingredient) => {
    ingredient.foodNutrients?.forEach((nutrient: Nutrient) => {
      const nutrientId = parseInt(nutrient.nutrient.number);
      const scaledAmount = (nutrient.amount * ingredient.quantity_grams) / 100;

      if (nutrientMap.has(nutrientId)) {
        const existing = nutrientMap.get(nutrientId)!;
        existing.amount += scaledAmount;
      } else {
        nutrientMap.set(nutrientId, {
          ...nutrient,
          amount: scaledAmount,
        });
      }
    });
  });

  aggregateNutrients.push(...nutrientMap.values());

  return (
    <div>
      <Link href="/recipes" className="text-blue-600 hover:underline mb-4 inline-block">
        ← Back to Recipes
      </Link>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        {editMode ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name</label>
              <input
                type="text"
                value={editData.name}
                onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cuisine</label>
              <input
                type="text"
                value={editData.cuisine}
                onChange={(e) => setEditData({ ...editData, cuisine: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={editData.description}
                onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleUpdateRecipe}
                disabled={isUpdating}
                className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
              >
                {isUpdating ? "Saving..." : "Save"}
              </button>
              <button
                onClick={() => setEditMode(false)}
                className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex justify-between items-start">
              <div>
                <h1 className="text-4xl font-bold">{recipe.name}</h1>
                {recipe.cuisine && <p className="text-gray-600 text-lg">{recipe.cuisine}</p>}
                {recipe.description && (
                  <p className="text-gray-700 mt-2">{recipe.description}</p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setEditData({
                      name: recipe.name,
                      cuisine: recipe.cuisine || "",
                      description: recipe.description || "",
                    });
                    setEditMode(true);
                  }}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Edit
                </button>
                <button
                  onClick={handleDeleteRecipe}
                  disabled={isDeleting}
                  className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 disabled:opacity-50"
                >
                  {isDeleting ? "Deleting..." : "Delete"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">Ingredients</h2>
          <button
            onClick={() => setShowAddIngredient(!showAddIngredient)}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {showAddIngredient ? "Cancel" : "Add Ingredient"}
          </button>
        </div>

        {showAddIngredient && (
          <div className="bg-gray-50 p-4 rounded mb-4 space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">Search USDA Database</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="e.g., cabbage, chicken breast..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSearchUSDA()}
                  className="flex-1 px-3 py-2 border rounded-lg"
                />
                <button
                  onClick={handleSearchUSDA}
                  disabled={isSearching}
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700 disabled:opacity-50"
                >
                  {isSearching ? "Searching..." : "Search"}
                </button>
              </div>
            </div>

            {searchResults.length > 0 && !selectedUSDAFood && (
              <div>
                <label className="block text-sm font-medium mb-2">Results</label>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {searchResults.map((food) => (
                    <button
                      key={food.fdc_id}
                      onClick={() => setSelectedUSDAFood(food)}
                      className="w-full text-left p-2 border rounded hover:bg-blue-50"
                    >
                      <div className="font-medium">{food.description}</div>
                      <div className="text-sm text-gray-600">
                        Type: {food.data_type} {food.brand_name && `| Brand: ${food.brand_name}`}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {selectedUSDAFood && (
              <div>
                <div className="p-2 bg-blue-50 rounded mb-3">
                  <div className="font-medium">{selectedUSDAFood.description}</div>
                  <button
                    onClick={() => setSelectedUSDAFood(null)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Change selection
                  </button>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">Quantity (grams)</label>
                  <input
                    type="number"
                    value={ingredientQuantity}
                    onChange={(e) => setIngredientQuantity(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border rounded-lg"
                  />
                </div>
                <button
                  onClick={handleAddIngredient}
                  disabled={isAddingIngredient}
                  className="mt-3 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {isAddingIngredient ? "Adding..." : "Add to Recipe"}
                </button>
              </div>
            )}
          </div>
        )}

        {(!recipe.ingredients || recipe.ingredients.length === 0) ? (
          <p className="text-gray-600">No ingredients added yet</p>
        ) : (
          <div className="space-y-4">
            {recipe.ingredients.map((ingredient: Ingredient) => (
              <div key={ingredient.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-lg font-semibold">{ingredient.name}</h3>
                    <p className="text-gray-600">{ingredient.quantity_grams}g</p>
                  </div>
                  <button
                    onClick={() => handleRemoveIngredient(ingredient.id)}
                    disabled={isRemovingIngredient}
                    className="text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    Remove
                  </button>
                </div>
                <NutrientTable nutrients={ingredient.foodNutrients} quantityGrams={ingredient.quantity_grams} />
              </div>
            ))}
          </div>
        )}
      </div>

      {recipe.ingredients && recipe.ingredients.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-2xl font-semibold mb-4">Recipe Totals</h2>
          <NutrientTable nutrients={aggregateNutrients} quantityGrams={100} />
        </div>
      )}
    </div>
  );
}
