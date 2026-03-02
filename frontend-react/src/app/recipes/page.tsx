"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useListRecipesQuery, useCreateRecipeMutation, type Recipe } from "@/store/api/recipesApi";
import { useGetFoodDetailsMutation, type USDAFood, type FoodPortion } from "@/store/api/usdaApi";
import { IngredientSearch } from "@/components/IngredientSearch";
import { QuantityInput } from "@/components/QuantityInput";
import { buildPortions, portionLabel } from "@/lib/portions";

export const dynamic = "force-dynamic";

const CUISINES = [
  "AMERICAN",
  "MEXICAN",
  "ITALIAN",
  "ASIAN",
  "INDIAN",
  "MEDITERRANEAN",
  "THAI",
  "JAPANESE",
  "FRENCH",
  "GREEK",
  "MIDDLE_EASTERN",
  "CARIBBEAN",
  "AFRICAN",
  "OTHER",
];

interface IngredientEntry {
  readonly fdcId: number;
  readonly description: string;
  readonly quantity_grams: number;
}

export default function RecipesPage() {
  const router = useRouter();
  const { data: recipes = [], isLoading, error } = useListRecipesQuery();
  const [createRecipe, { isLoading: isCreating }] = useCreateRecipeMutation();
  const [getFoodDetails] = useGetFoodDetailsMutation();

  const [searchTerm, setSearchTerm] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    cuisine: "AMERICAN",
    description: "",
  });
  const [ingredients, setIngredients] = useState<IngredientEntry[]>([]);
  const [ingredientPortions, setIngredientPortions] = useState<Record<number, FoodPortion[]>>({});
  const [activePortionPerIngredient, setActivePortionPerIngredient] = useState<
    Record<number, FoodPortion | null>
  >({});

  const filteredRecipes = recipes.filter(
    (recipe) =>
      recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (recipe.cuisine?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
  );

  const handleAddIngredient = async (food: USDAFood) => {
    if (ingredients.some((i) => i.fdcId === food.fdcId)) return;
    setIngredients((prev) => [
      ...prev,
      { fdcId: food.fdcId, description: food.description, quantity_grams: 100 },
    ]);
    try {
      const results = await getFoodDetails({ fdcIds: [food.fdcId] }).unwrap();
      if (results.length > 0) {
        const portions = buildPortions(results[0]);
        if (portions.length > 0) {
          setIngredientPortions((prev) => ({ ...prev, [food.fdcId]: portions }));
        }
      }
    } catch {
      // Portions are supplemental
    }
  };

  const handleRemoveIngredient = (fdcId: number) => {
    setIngredients(ingredients.filter((i) => i.fdcId !== fdcId));
  };

  const handleQuantityChange = (fdcId: number, quantity_grams: number) => {
    setIngredients(ingredients.map((i) => (i.fdcId === fdcId ? { ...i, quantity_grams } : i)));
  };

  const handleSubmit = async () => {
    if (ingredients.length === 0) {
      alert("Add at least one ingredient.");
      return;
    }
    try {
      const result = await createRecipe({
        name: formData.name,
        cuisine: formData.cuisine,
        description: formData.description || undefined,
        ingredients: ingredients.map((i) => ({
          usda_fdc_id: i.fdcId,
          quantity_grams: i.quantity_grams,
        })),
      }).unwrap();
      router.push(`/recipes/${result.id}`);
    } catch (err) {
      console.error("Error creating recipe:", err);
    }
  };

  if (isLoading) return <div className="text-center py-8">Loading recipes...</div>;
  if (error) console.error("Recipe query error:", error);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-4xl font-bold">Recipes</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          {showForm ? "Cancel" : "Create Recipe"}
        </button>
      </div>

      {showForm && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-2xl font-semibold mb-4">New Recipe</h2>
          <form className="space-y-4">
            <div>
              <label htmlFor="recipe-name" className="block text-sm font-medium mb-1">
                Name *
              </label>
              <input
                id="recipe-name"
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label htmlFor="recipe-cuisine" className="block text-sm font-medium mb-1">
                Cuisine *
              </label>
              <select
                id="recipe-cuisine"
                required
                value={formData.cuisine}
                onChange={(e) => setFormData({ ...formData, cuisine: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                {CUISINES.map((c) => (
                  <option key={c} value={c}>
                    {c.replace("_", " ")}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="recipe-description" className="block text-sm font-medium mb-1">
                Description
              </label>
              <textarea
                id="recipe-description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>

            <div>
              <p className="block text-sm font-medium mb-2">Ingredients</p>
              <IngredientSearch
                onSelect={handleAddIngredient}
                placeholder="Search USDA for an ingredient..."
              />

              {ingredients.length > 0 && (
                <div className="space-y-2 mt-3">
                  {ingredients.map((ing) => (
                    <div
                      key={ing.fdcId}
                      className="flex items-center gap-2 bg-gray-50 px-3 py-2 rounded-lg"
                    >
                      <span className="flex-1 text-sm">{ing.description}</span>
                      {ingredientPortions[ing.fdcId] && (
                        <select
                          defaultValue="-1"
                          onChange={(e) => {
                            const idx = Number.parseInt(e.target.value);
                            if (idx >= 0) {
                              const portion = ingredientPortions[ing.fdcId][idx];
                              setActivePortionPerIngredient((prev) => ({
                                ...prev,
                                [ing.fdcId]: portion,
                              }));
                              handleQuantityChange(ing.fdcId, portion.gramWeight ?? 100);
                            } else {
                              setActivePortionPerIngredient((prev) => ({
                                ...prev,
                                [ing.fdcId]: null,
                              }));
                            }
                          }}
                          className="px-2 py-1 border rounded text-xs"
                        >
                          <option value="-1">Custom</option>
                          {ingredientPortions[ing.fdcId].map((p, i) => (
                            <option key={p.id ?? i} value={i}>
                              {portionLabel(p)}
                            </option>
                          ))}
                        </select>
                      )}
                      <QuantityInput
                        value={ing.quantity_grams}
                        onChange={(grams) => handleQuantityChange(ing.fdcId, grams)}
                        servingGrams={activePortionPerIngredient[ing.fdcId]?.gramWeight}
                        servingLabel={
                          activePortionPerIngredient[ing.fdcId]
                            ? portionLabel(activePortionPerIngredient[ing.fdcId]!)
                            : undefined
                        }
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveIngredient(ing.fdcId)}
                        className="text-red-500 hover:text-red-700 text-sm"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={isCreating}
              className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50"
            >
              {isCreating ? "Creating..." : "Create"}
            </button>
          </form>
        </div>
      )}

      <div className="mb-6">
        <input
          type="text"
          placeholder="Search recipes by name or cuisine..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full px-4 py-2 border rounded-lg"
        />
      </div>

      {filteredRecipes.length === 0 ? (
        <div className="text-center py-8 text-gray-600">No recipes found</div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {filteredRecipes.map((recipe: Recipe) => (
            <Link href={`/recipes/${recipe.id}`} key={recipe.id}>
              <div className="bg-white p-4 rounded-lg shadow-md hover:shadow-lg transition cursor-pointer">
                <h2 className="text-xl font-semibold">{recipe.name}</h2>
                {recipe.cuisine && <p className="text-gray-600">{recipe.cuisine}</p>}
                {recipe.description && (
                  <p className="text-gray-700 text-sm mt-2">{recipe.description}</p>
                )}
                <p className="text-gray-500 text-sm mt-2">
                  {recipe.ingredients?.length || 0} ingredients
                </p>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
