"use client";

import { useState } from "react";
import { useSearchMutation } from "@/store/api/usdaApi";
import type { USDAFood, USDASearchRequest } from "@/store/api/usdaApi";

const DATA_TYPES: Record<string, string[]> = {
  "Produce/Meat": ["Foundation", "SR Legacy"],
  "Commercial Product": ["Branded"],
  Meal: ["Survey (FNDDS)"],
};

const ALL_DATA_TYPES = Object.values(DATA_TYPES).flat();

interface IngredientSearchProps {
  readonly onSelect: (food: USDAFood) => void;
  readonly placeholder?: string;
}

export function IngredientSearch({
  onSelect,
  placeholder = "Search USDA database...",
}: IngredientSearchProps) {
  const [searchUSDA, { isLoading }] = useSearchMutation();
  const [query, setQuery] = useState("");
  const [dataType, setDataType] = useState<string[] | null>(null);
  const [brandOwner, setBrandOwner] = useState("");
  const [results, setResults] = useState<USDAFood[]>([]);
  const [error, setError] = useState("");

  const isCommercial =
    JSON.stringify(dataType) ===
    JSON.stringify(DATA_TYPES["Commercial Product"]);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError("Please enter a search term.");
      return;
    }
    setError("");
    const request: USDASearchRequest = {
      query,
      dataType: dataType ?? ALL_DATA_TYPES,
      ...(brandOwner.length > 0 && {brandOwner})
    };

    try {
      const foods = await searchUSDA(request).unwrap();
      setResults(foods);
    } catch {
      setError("Search failed. Please try again.");
    }
  };

  const handleSelect = (food: USDAFood) => {
    onSelect(food);
    setQuery("");
    setBrandOwner("");
    setDataType(null);
    setResults([]);
    setError("");
  };

  const handleDataTypeChange = (types: string[] | null) => {
    setDataType(types);
    setResults([]);
    setQuery("");
    setBrandOwner("");
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <input
          type="text"
          placeholder={placeholder}
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setError("");
          }}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="flex-1 px-3 py-2 border rounded-lg"
        />
        {isCommercial && (
          <input
            type="text"
            placeholder="Brand (e.g. Frank's RedHot)"
            value={brandOwner}
            onChange={(e) => setBrandOwner(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="flex-1 px-3 py-2 border rounded-lg"
          />
        )}
        <button
          type="button"
          onClick={handleSearch}
          disabled={isLoading}
          className="relative shrink-0 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          <span className="invisible">Searching...</span>
          <span className="absolute inset-0 flex items-center justify-center">
            {isLoading ? "Searching..." : "Search"}
          </span>
        </button>
      </div>

      <div className="flex flex-row flex-wrap gap-4">
        {Object.entries(DATA_TYPES).map(([label, types]) => (
          <label key={label} className="flex items-center gap-1 cursor-pointer">
            <input
              type="radio"
              name="ingredientDataType"
              checked={JSON.stringify(dataType) === JSON.stringify(types)}
              onChange={() => handleDataTypeChange(types)}
            />
            <span>{label}</span>
          </label>
        ))}
        <label className="flex items-center gap-1 cursor-pointer">
          <input
            type="radio"
            name="ingredientDataType"
            checked={dataType === null}
            onChange={() => handleDataTypeChange(null)}
          />
          <span>Any</span>
        </label>
        {error && <span className="text-sm text-red-600">{error}</span>}
      </div>

      {results.length > 0 && (
        <div className="border rounded-lg max-h-64 overflow-y-auto">
          {results.map((food) => (
            <button
              key={food.fdcId}
              type="button"
              onClick={() => handleSelect(food)}
              className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b last:border-0"
            >
              <div className="font-medium">{food.description}</div>
              {food.brandOwner && (
                <div className="text-sm text-gray-500">
                  Brand: {food.brandOwner}
                </div>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
