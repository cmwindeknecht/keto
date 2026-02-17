"use client";

import { useState } from "react";
import Link from "next/link";
import { useListRecipesQuery, useCreateRecipeMutation } from "@/store/api/recipesApi";

export const dynamic = "force-dynamic";
import type { Recipe } from "@/store/api/recipesApi";

export default function RecipesPage() {
  const { data: recipes = [], isLoading, error } = useListRecipesQuery();
  const [createRecipe, { isLoading: isCreating }] = useCreateRecipeMutation();
  const [searchTerm, setSearchTerm] = useState("");
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    cuisine: "",
    description: "",
  });

  const filteredRecipes = recipes.filter(
    (recipe) =>
      recipe.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (recipe.cuisine?.toLowerCase().includes(searchTerm.toLowerCase()) ?? false)
  );

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createRecipe({
        name: formData.name,
        cuisine: formData.cuisine,
        description: formData.description,
      }).unwrap();
      setFormData({ name: "", cuisine: "", description: "" });
      setShowForm(false);
    } catch (err) {
      console.error("Error creating recipe:", err);
    }
  };

  if (isLoading) return <div className="text-center py-8">Loading recipes...</div>;
  if (error) return <div className="text-center py-8 text-red-600">Error loading recipes</div>;

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
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">Name *</label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Cuisine</label>
              <input
                type="text"
                value={formData.cuisine}
                onChange={(e) => setFormData({ ...formData, cuisine: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Description</label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <button
              type="submit"
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
