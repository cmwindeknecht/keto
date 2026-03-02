"use client";

import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  useSearchMutation,
  useGetFoodDetailsMutation,
  type USDASearchRequest,
  type FoodPortion,
} from "@/store/api/usdaApi";
import { buildPortions, portionLabel } from "@/lib/portions";
import {
  selectFood,
  setQuantity,
  setUnit,
  clearSelection,
  type UnitType,
} from "@/store/slices/lookupSlice";
import { NutrientTable } from "@/components/NutrientTable";
import { QuantityInput } from "@/components/QuantityInput";
import type { RootState } from "@/store";

export const dynamic = "force-dynamic";

enum DATA_TYPE {
  PRODUCE_MEAT = "Produce/Meat",
  COMMERCIAL_PRODUCT = "Commerical Product", // 1
  MEAL = "Meal",
}

const DATA_TYPES: Record<string, string[]> = {
  [DATA_TYPE.PRODUCE_MEAT]: ["Foundation", "SR Legacy"],
  [DATA_TYPE.COMMERCIAL_PRODUCT]: ["Branded"],
  [DATA_TYPE.MEAL]: ["Survey (FNDDS)"],
};

export default function LookupPage() {
  const dispatch = useDispatch();
  const { selectedFood, quantity, unit } = useSelector((state: RootState) => state.lookup);
  const [searchUSDA, { isLoading: isSearching }] = useSearchMutation();
  const [getFoodDetails] = useGetFoodDetailsMutation();
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [dataType, setDataType] = useState<string[] | null>(null);
  const [brandOwner, setBrandOwner] = useState("");
  const [foodSearchError, setFoodSearchError] = useState("");
  const [portions, setPortions] = useState<FoodPortion[]>([]);
  const [activePortion, setActivePortion] = useState<FoodPortion | null>(null);

  useEffect(() => {
    setFoodSearchError("");
  }, [searchQuery, dataType, brandOwner]);

  useEffect(() => {
    setSearchResults([]);
    setSearchQuery("");
    setBrandOwner("");
  }, [dataType]);

  const handleSearch = async () => {
    try {
      if (searchQuery.length === 0) {
        setFoodSearchError("Search is empty, please search for a value");
        return;
      }

      const request: USDASearchRequest = {
        query: searchQuery,
        dataType: dataType ?? Object.values(DATA_TYPES).flat(),
        ...(brandOwner.length > 0 && { brandOwner }),
      };

      const result = await searchUSDA(request).unwrap();
      setSearchResults(result);
    } catch (err) {
      console.error("Error searching USDA:", err);
      setFoodSearchError("Failed to retrieve data, please try again later.");
    }
  };

  const handleSelectFood = async (food: any) => {
    dispatch(selectFood(food));
    setSearchResults([]);
    setSearchQuery("");
    setBrandOwner("");
    setPortions([]);
    setActivePortion(null);
    try {
      const results = await getFoodDetails({ fdcIds: [food.fdcId] }).unwrap();
      if (results.length > 0) setPortions(buildPortions(results[0]));
    } catch {
      // Portions are supplemental — silently fail
    }
  };

  const handleClearSelection = () => {
    dispatch(clearSelection());
    setSearchResults([]);
    setSearchQuery("");
    setBrandOwner("");
    setDataType(null);
    setPortions([]);
    setActivePortion(null);
  };

  // Convert quantity to grams (quantity is always stored as grams when dispatched from QuantityInput)
  const quantityInGrams = quantity * (unit === "g" ? 1 : unit === "oz" ? 28.3495 : 453.592);

  return (
    <div>
      <h1 className="text-4xl font-bold mb-6">Quick Lookup</h1>
      <div className="bg-white p-6 rounded-lg shadow-md mb-6">
        <div className="flex flex-col gap-2 mb-4">
          {/* Search Bar */}
          <label htmlFor="food-search" className="block text-sm font-medium">
            Search USDA Database
          </label>
          <div className="flex w-full gap-2">
            <input
              id="food-search"
              type="text"
              placeholder="Search for foods (e.g., cabbage, chicken breast)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            {JSON.stringify(dataType) ===
              JSON.stringify(DATA_TYPES[DATA_TYPE.COMMERCIAL_PRODUCT]) && (
              <input
                id="brand-search"
                type="text"
                placeholder="Search Brand (e.g., Frank's RedHot, Mission)"
                value={brandOwner}
                onChange={(e) => setBrandOwner(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="flex-1 px-4 py-2 border rounded-lg"
              />
            )}
            <button
              onClick={handleSearch}
              disabled={isSearching}
              className="relative shrink-0 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
            >
              <span className="invisible">Searching...</span>
              <span className="absolute inset-0 flex items-center justify-center">
                {isSearching ? "Searching..." : "Search"}
              </span>
            </button>
          </div>

          {/* Data Type Radio Buttons */}
          <div className="flex flex-row gap-4">
            {Object.entries(DATA_TYPES).map(([readableType, usdaType]) => (
              <label key={readableType} className="flex items-center gap-1 cursor-pointer">
                <input
                  type="radio"
                  name="dataType"
                  value={usdaType}
                  checked={JSON.stringify(dataType) === JSON.stringify(usdaType)}
                  onChange={() => setDataType(usdaType)}
                />{" "}
                <span>{readableType}</span>
              </label>
            ))}
            <label className="flex items-center gap-1 cursor-pointer">
              <input
                type="radio"
                name="dataType"
                value=""
                checked={dataType === null}
                onChange={() => setDataType(null)}
              />{" "}
              <span>Any</span>
            </label>
            {foodSearchError.length > 0 && (
              <div className="text-sm text-red-600">{foodSearchError}</div>
            )}
          </div>
        </div>

        {searchResults.length > 0 && (
          <div>
            <p className="block text-sm font-medium mb-2">Results</p>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {searchResults.map((food) => (
                <button
                  key={food.fdcId}
                  onClick={() => handleSelectFood(food)}
                  className="w-full text-left p-3 border rounded hover:bg-blue-50"
                >
                  <div className="font-medium">{food.description}</div>
                  <div className="text-sm text-gray-600">
                    {food.brandOwner && `| Brand: ${food.brandOwner}`}
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
              {selectedFood.brandOwner && (
                <p className="text-gray-600">Brand: {selectedFood.brandOwner}</p>
              )}
            </div>
            <button onClick={handleClearSelection} className="text-gray-600 hover:text-gray-900">
              ✕
            </button>
          </div>

          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            {portions.length > 0 && (
              <div className="mb-3">
                <label htmlFor="portion-select" className="block text-sm font-medium mb-1">
                  Serving size
                </label>
                <select
                  id="portion-select"
                  defaultValue="-1"
                  onChange={(e) => {
                    const idx = Number.parseInt(e.target.value);
                    if (idx >= 0) {
                      const portion = portions[idx];
                      setActivePortion(portion);
                      dispatch(setQuantity(portion.gramWeight ?? 100));
                      dispatch(setUnit("g"));
                    } else {
                      setActivePortion(null);
                    }
                  }}
                  className="px-3 py-2 border rounded-lg text-sm"
                >
                  <option value="-1">Custom</option>
                  {portions.map((p, i) => (
                    <option key={p.id ?? i} value={i}>
                      {portionLabel(p)}
                    </option>
                  ))}
                </select>
              </div>
            )}
            <label htmlFor="quantity-input" className="block text-sm font-medium mb-3">
              Amount
            </label>
            <QuantityInput
              inputId="quantity-input"
              value={quantityInGrams}
              onChange={(g) => {
                dispatch(setQuantity(g));
                dispatch(setUnit("g" as UnitType));
              }}
              servingGrams={activePortion?.gramWeight}
              servingLabel={activePortion ? portionLabel(activePortion) : undefined}
              inputClassName="flex-1 px-4 py-2 border rounded-lg"
            />
            {activePortion && (
              <p className="text-sm text-gray-600 mt-2">{quantityInGrams.toFixed(1)}g</p>
            )}
          </div>

          <NutrientTable
            nutrients={selectedFood.foodNutrients.map((n: any) => ({
              nutrient: {
                id: n.nutrientId,
                number: String(n.nutrientId),
                name: n.nutrientName,
                unitName: n.unitName,
              },
              amount: n.value,
            }))}
            quantityGrams={quantityInGrams}
          />
        </div>
      )}
    </div>
  );
}
