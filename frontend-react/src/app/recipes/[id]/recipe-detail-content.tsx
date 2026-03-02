"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  useGetRecipeQuery,
  useUpdateRecipeMutation,
  useDeleteRecipeMutation,
  useAddIngredientMutation,
  useUpdateIngredientMutation,
  useRemoveIngredientMutation,
  type RecipeIngredient,
  type NutrientInfo,
  type Nutrient,
} from "@/store/api/recipesApi";
import { useGetFoodDetailsMutation, type USDAFood, type FoodPortion } from "@/store/api/usdaApi";
import { IngredientSearch } from "@/components/IngredientSearch";
import { QuantityInput } from "@/components/QuantityInput";
import { NutrientTable } from "@/components/NutrientTable";
import { formatAllUnits } from "@/lib/units";
import { buildPortions, portionLabel } from "@/lib/portions";

const NUTRIENT_NAME_TO_ID: Record<string, number> = {
  Energy: 1008,
  "Total lipid (fat)": 1004,
  "Carbohydrate, by difference": 1005,
  "Fiber, total dietary": 1079,
  "Sodium, Na": 1093,
  "Potassium, K": 1092,
  "Magnesium, Mg": 1090,
};

function toNutrient(info: NutrientInfo): Nutrient {
  const id = NUTRIENT_NAME_TO_ID[info.name] ?? 0;
  return {
    nutrient: { id, number: String(id), name: info.name, unitName: info.unit },
    amount: info.amount,
  };
}

interface RecipeDetailContentProps {
  readonly id: string;
}

export function RecipeDetailContent({ id }: RecipeDetailContentProps) {
  const router = useRouter();
  const { data: recipe, isLoading, error } = useGetRecipeQuery(id);
  const [updateRecipe, { isLoading: isUpdating }] = useUpdateRecipeMutation();
  const [deleteRecipe, { isLoading: isDeleting }] = useDeleteRecipeMutation();
  const [addIngredient, { isLoading: isAddingIngredient }] = useAddIngredientMutation();
  const [updateIngredient] = useUpdateIngredientMutation();
  const [removeIngredient, { isLoading: isRemovingIngredient }] = useRemoveIngredientMutation();
  const [getFoodDetails] = useGetFoodDetailsMutation();

  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({
    name: recipe?.name || "",
    cuisine: recipe?.cuisine || "",
    description: recipe?.description || "",
  });
  const [showAddIngredient, setShowAddIngredient] = useState(false);
  const [selectedUSDAFood, setSelectedUSDAFood] = useState<USDAFood | null>(null);
  const [ingredientQuantity, setIngredientQuantity] = useState(100);
  const [addPortions, setAddPortions] = useState<FoodPortion[]>([]);
  const [addActivePortion, setAddActivePortion] = useState<FoodPortion | null>(null);

  // Inline quantity editing
  const [editingIngredientId, setEditingIngredientId] = useState<string | null>(null);
  const [editingQuantity, setEditingQuantity] = useState(0);
  const [editingPortions, setEditingPortions] = useState<FoodPortion[]>([]);
  const [editingActivePortion, setEditingActivePortion] = useState<FoodPortion | null>(null);

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

  const handleAddIngredient = async () => {
    if (!selectedUSDAFood) return;
    try {
      await addIngredient({
        id,
        body: {
          usda_fdc_id: selectedUSDAFood.fdcId,
          quantity_grams: ingredientQuantity,
        },
      }).unwrap();
      setSelectedUSDAFood(null);
      setIngredientQuantity(100);
      setAddPortions([]);
      setAddActivePortion(null);
      setShowAddIngredient(false);
    } catch (err) {
      console.error("Error adding ingredient:", err);
    }
  };

  const handleStartEditQuantity = async (ingredient: RecipeIngredient) => {
    setEditingIngredientId(ingredient.id);
    setEditingQuantity(ingredient.quantity_grams);
    setEditingPortions([]);
    setEditingActivePortion(null);
    try {
      const results = await getFoodDetails({
        fdcIds: [ingredient.ingredient.usda_fdc_id],
      }).unwrap();
      if (results.length > 0) setEditingPortions(buildPortions(results[0]));
    } catch {
      // Portions are supplemental
    }
  };

  const handleSaveQuantity = async (ingredient: RecipeIngredient) => {
    try {
      await updateIngredient({
        recipeId: id,
        ingredientId: ingredient.id,
        body: {
          usda_fdc_id: ingredient.ingredient.usda_fdc_id,
          quantity_grams: editingQuantity,
        },
      }).unwrap();
      setEditingIngredientId(null);
    } catch (err) {
      console.error("Error updating ingredient:", err);
    }
  };

  const handleRemoveIngredient = async (ingredientId: string) => {
    if (confirm("Remove this ingredient?")) {
      try {
        await removeIngredient({ recipeId: id, ingredientId }).unwrap();
      } catch (err) {
        console.error("Error removing ingredient:", err);
      }
    }
  };

  if (isLoading) return <div className="text-center py-8">Loading recipe...</div>;
  if (error || !recipe)
    return <div className="text-center py-8 text-red-600">Recipe not found</div>;

  const aggregateNutrients: Nutrient[] = (recipe.nutrients ?? []).map(toNutrient);

  return (
    <div>
      <Link href="/recipes" className="text-blue-600 hover:underline mb-4 inline-block">
        ← Back to Recipes
      </Link>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        {editMode ? (
          <div className="space-y-4">
            <div>
              <label htmlFor="edit-name" className="block text-sm font-medium mb-1">
                Name
              </label>
              <input
                id="edit-name"
                type="text"
                value={editData.name}
                onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label htmlFor="edit-cuisine" className="block text-sm font-medium mb-1">
                Cuisine
              </label>
              <input
                id="edit-cuisine"
                type="text"
                value={editData.cuisine}
                onChange={(e) => setEditData({ ...editData, cuisine: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label htmlFor="edit-description" className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                id="edit-description"
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
                {recipe.description && <p className="text-gray-700 mt-2">{recipe.description}</p>}
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

      {recipe.ingredients && recipe.ingredients.length > 0 && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-2xl font-semibold mb-4">Recipe Totals</h2>
          <NutrientTable nutrients={aggregateNutrients} quantityGrams={100} />
        </div>
      )}

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-semibold">Ingredients</h2>
          <button
            onClick={() => {
              setShowAddIngredient(!showAddIngredient);
              setSelectedUSDAFood(null);
              setIngredientQuantity(100);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            {showAddIngredient ? "Cancel" : "Add Ingredient"}
          </button>
        </div>

        {showAddIngredient && (
          <div className="bg-gray-50 p-4 rounded mb-4 space-y-3">
            {selectedUSDAFood ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <span className="font-medium">{selectedUSDAFood.description}</span>
                  <button
                    onClick={() => setSelectedUSDAFood(null)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Change
                  </button>
                </div>
                <div>
                  {addPortions.length > 0 && (
                    <div className="mb-2">
                      <label
                        htmlFor="add-portion-select"
                        className="block text-sm font-medium mb-1"
                      >
                        Serving size
                      </label>
                      <select
                        id="add-portion-select"
                        defaultValue="-1"
                        onChange={(e) => {
                          const idx = Number.parseInt(e.target.value);
                          if (idx >= 0) {
                            const portion = addPortions[idx];
                            setAddActivePortion(portion);
                            setIngredientQuantity(portion.gramWeight ?? 100);
                          } else {
                            setAddActivePortion(null);
                          }
                        }}
                        className="px-3 py-2 border rounded-lg text-sm"
                      >
                        <option value="-1">Custom</option>
                        {addPortions.map((p, i) => (
                          <option key={p.id ?? i} value={i}>
                            {portionLabel(p)}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}
                  <label htmlFor="ingredient-quantity" className="block text-sm font-medium mb-1">
                    Quantity
                  </label>
                  <QuantityInput
                    inputId="ingredient-quantity"
                    value={ingredientQuantity}
                    onChange={setIngredientQuantity}
                    inputClassName="w-28 px-3 py-2 border rounded-lg text-sm"
                    servingGrams={addActivePortion?.gramWeight}
                    servingLabel={addActivePortion ? portionLabel(addActivePortion) : undefined}
                  />
                </div>
                <button
                  onClick={handleAddIngredient}
                  disabled={isAddingIngredient}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
                >
                  {isAddingIngredient ? "Adding..." : "Add to Recipe"}
                </button>
              </div>
            ) : (
              <IngredientSearch
                onSelect={async (food) => {
                  setSelectedUSDAFood(food);
                  setIngredientQuantity(100);
                  setAddPortions([]);
                  setAddActivePortion(null);
                  try {
                    const results = await getFoodDetails({ fdcIds: [food.fdcId] }).unwrap();
                    if (results.length > 0) setAddPortions(buildPortions(results[0]));
                  } catch {
                    // Portions are supplemental
                  }
                }}
                placeholder="Search USDA for an ingredient..."
              />
            )}
          </div>
        )}

        {!recipe.ingredients || recipe.ingredients.length === 0 ? (
          <p className="text-gray-600">No ingredients added yet</p>
        ) : (
          <div className="space-y-4">
            {recipe.ingredients.map((ingredient: RecipeIngredient) => (
              <div key={ingredient.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                  <div>
                    <h3 className="text-lg font-semibold">{ingredient.ingredient.name}</h3>
                    {ingredient.ingredient.brand_owner && (
                      <p className="text-sm text-gray-500">{ingredient.ingredient.brand_owner}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {editingIngredientId === ingredient.id ? (
                      <>
                        {editingPortions.length > 0 && (
                          <select
                            defaultValue="-1"
                            onChange={(e) => {
                              const idx = Number.parseInt(e.target.value);
                              if (idx >= 0) {
                                const portion = editingPortions[idx];
                                setEditingActivePortion(portion);
                                setEditingQuantity(portion.gramWeight ?? 100);
                              } else {
                                setEditingActivePortion(null);
                              }
                            }}
                            className="px-2 py-1 border rounded text-sm"
                          >
                            <option value="-1">Custom</option>
                            {editingPortions.map((p, i) => (
                              <option key={p.id ?? i} value={i}>
                                {portionLabel(p)}
                              </option>
                            ))}
                          </select>
                        )}
                        <QuantityInput
                          value={editingQuantity}
                          onChange={setEditingQuantity}
                          servingGrams={editingActivePortion?.gramWeight}
                          servingLabel={
                            editingActivePortion ? portionLabel(editingActivePortion) : undefined
                          }
                        />
                        <button
                          onClick={() => handleSaveQuantity(ingredient)}
                          className="text-green-600 hover:text-green-800 text-sm font-medium"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => setEditingIngredientId(null)}
                          className="text-gray-500 hover:text-gray-700 text-sm"
                        >
                          Cancel
                        </button>
                      </>
                    ) : (
                      <>
                        <span className="text-gray-500 text-sm cursor-pointer hover:text-blue-600">
                          {formatAllUnits(ingredient.quantity_grams)}
                        </span>
                        <button
                          onClick={() => handleStartEditQuantity(ingredient)}
                          className="text-blue-500 hover:text-blue-700 text-sm"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleRemoveIngredient(ingredient.id)}
                          disabled={isRemovingIngredient}
                          className="text-red-600 hover:text-red-800 text-sm disabled:opacity-50"
                        >
                          Remove
                        </button>
                      </>
                    )}
                  </div>
                </div>
                <NutrientTable
                  nutrients={ingredient.nutrients.map(toNutrient)}
                  quantityGrams={100}
                />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
