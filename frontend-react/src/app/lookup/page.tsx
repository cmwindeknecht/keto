"use client";

import { useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useSearchMutation } from "@/store/api/usdaApi";

export const dynamic = "force-dynamic";
import { selectFood, setQuantity, setUnit, clearSelection } from "@/store/slices/lookupSlice";
import { NutrientTable } from "@/components/NutrientTable";
import type { RootState } from "@/store";
import type { UnitType } from "@/store/slices/lookupSlice";

const UNIT_CONVERSIONS: Record<UnitType, number> = {
  g: 1,
  oz: 28.3495,
  lb: 453.592,
};

export default function LookupPage() {
  const dispatch = useDispatch();
  const { selectedFood, quantity, unit } = useSelector((state: RootState) => state.lookup);
  const [searchUSDA, { isLoading: isSearching }] = useSearchMutation();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    try {
      const result = await searchUSDA({ query: searchQuery }).unwrap();
      setSearchResults(result.foods);
    } catch (err) {
      console.error("Error searching USDA:", err);
    }
  };

  const handleSelectFood = (food: any) => {
    dispatch(selectFood(food));
    setSearchResults([]);
    setSearchQuery("");
  };

  const handleQuantityChange = (newQuantity: number) => {
    dispatch(setQuantity(newQuantity));
  };

  const handleUnitChange = (newUnit: UnitType) => {
    dispatch(setUnit(newUnit));
  };

  const handleClearSelection = () => {
    dispatch(clearSelection());
    setSearchResults([]);
    setSearchQuery("");
  };

  // Convert quantity to grams
  const quantityInGrams = quantity * UNIT_CONVERSIONS[unit];

  return (
    <div>
      <h1 className="text-4xl font-bold mb-6">Quick Lookup</h1>

      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <label className="block text-sm font-medium mb-2">Search USDA Database</label>
        <div className="flex gap-2 mb-4">
          <input
            type="text"
            placeholder="Search for foods (e.g., cabbage, chicken breast)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1 px-4 py-2 border rounded-lg"
          />
          <button
            onClick={handleSearch}
            disabled={isSearching}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {isSearching ? "Searching..." : "Search"}
          </button>
        </div>

        {searchResults.length > 0 && !selectedFood && (
          <div>
            <label className="block text-sm font-medium mb-2">Results</label>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {searchResults.map((food) => (
                <button
                  key={food.fdc_id}
                  onClick={() => handleSelectFood(food)}
                  className="w-full text-left p-3 border rounded hover:bg-blue-50"
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
      </div>

      {selectedFood && (
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-semibold">{selectedFood.description}</h2>
              <p className="text-gray-600">
                Type: {selectedFood.data_type}
                {selectedFood.brand_name && ` | Brand: ${selectedFood.brand_name}`}
              </p>
            </div>
            <button
              onClick={handleClearSelection}
              className="text-gray-600 hover:text-gray-900"
            >
              ✕
            </button>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <label className="block text-sm font-medium mb-3">Amount</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={quantity}
                onChange={(e) => handleQuantityChange(parseFloat(e.target.value))}
                className="flex-1 px-4 py-2 border rounded-lg"
                step="0.1"
              />
              <select
                value={unit}
                onChange={(e) => handleUnitChange(e.target.value as UnitType)}
                className="px-4 py-2 border rounded-lg"
              >
                <option value="g">grams (g)</option>
                <option value="oz">ounces (oz)</option>
                <option value="lb">pounds (lb)</option>
              </select>
            </div>
            <p className="text-sm text-gray-600 mt-2">
              {quantityInGrams.toFixed(1)}g
            </p>
          </div>

          <NutrientTable nutrients={selectedFood.foodNutrients} quantityGrams={quantityInGrams} />
        </div>
      )}
    </div>
  );
}
