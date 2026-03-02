"use client";

import { useState } from "react";
import type { Nutrient } from "@/store/api/recipesApi";

interface NutrientTableProps {
  readonly nutrients: Nutrient[];
  readonly quantityGrams: number;
}

const NUTRIENT_MAP: Record<number, { label: string; unit: string }> = {
  1008: { label: "Calories", unit: "kcal" },
  1003: { label: "Protein", unit: "g" },
  1004: { label: "Fat", unit: "g" },
  1005: { label: "Carbs", unit: "g" },
  1079: { label: "Fiber", unit: "g" },
  1093: { label: "Sodium", unit: "mg" },
  1092: { label: "Potassium", unit: "mg" },
  1090: { label: "Magnesium", unit: "mg" },
};

const PRIMARY_NUTRIENTS = [1008, 1003, 1004, 1005, 1079, 1093, 1092, 1090];

function getNutrientValue(nutrients: Nutrient[], nutrientId: number): number {
  const nutrient = nutrients.find((n) => Number.parseInt(n.nutrient.number) === nutrientId);
  return nutrient ? nutrient.amount : 0;
}

function scaleNutrient(per100g: number, quantityGrams: number): number {
  return (per100g * quantityGrams) / 100;
}

export function NutrientTable({ nutrients, quantityGrams }: NutrientTableProps) {
  const [showAll, setShowAll] = useState(false);
  const [nutrientFilter, setNutrientFilter] = useState("");

  const getDisplayValue = (nutrientId: number) => {
    const per100g = getNutrientValue(nutrients, nutrientId);
    return scaleNutrient(per100g, quantityGrams);
  };

  const netCarbs = getDisplayValue(1005) - getDisplayValue(1079);
  const columns = [
    ...PRIMARY_NUTRIENTS.map((id) => ({
      id,
      label: NUTRIENT_MAP[id].label,
      value: `${getDisplayValue(id).toFixed(1)} ${NUTRIENT_MAP[id].unit}`,
    })),
    { id: -1, label: "Net Carbs", value: `${netCarbs.toFixed(1)} g` },
  ];

  const primaryIds = new Set(PRIMARY_NUTRIENTS);
  const allOtherNutrients = nutrients
    .filter((n) => !primaryIds.has(n.nutrient.id))
    .map((n) => ({
      id: n.nutrient.id,
      name: n.nutrient.name,
      unit: n.nutrient.unitName,
      scaled: scaleNutrient(n.amount, quantityGrams),
    }))
    .sort((a, b) => a.name.localeCompare(b.name));

  const query = nutrientFilter.toLowerCase();
  const matches = query
    ? allOtherNutrients.filter((n) => n.name.toLowerCase().startsWith(query))
    : allOtherNutrients;
  const nonMatches = query
    ? allOtherNutrients.filter((n) => !n.name.toLowerCase().startsWith(query))
    : [];

  return (
    <div>
      <div className="overflow-x-auto">
        <table className="text-sm border-collapse">
          <thead>
            <tr>
              {columns.map((col) => (
                <th
                  key={col.id}
                  className="px-3 py-1 text-center text-gray-500 font-medium whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr>
              {columns.map((col) => (
                <td key={col.id} className="px-3 py-1 text-center font-semibold whitespace-nowrap">
                  {col.value}
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {allOtherNutrients.length > 0 && (
        <div className="mt-3">
          <button
            onClick={() => setShowAll(!showAll)}
            className="text-sm text-blue-600 hover:underline"
          >
            {showAll ? "Show less ▲" : `All nutrients (${allOtherNutrients.length}) ▼`}
          </button>
          {showAll && (
            <div className="mt-2">
              <input
                type="text"
                placeholder="Filter nutrients..."
                value={nutrientFilter}
                onChange={(e) => setNutrientFilter(e.target.value)}
                className="px-2 py-1 border rounded text-sm mb-2 w-full max-w-sm"
              />
              <table className="text-sm border-collapse w-full max-w-sm">
                <tbody>
                  {matches.map((n) => (
                    <tr key={n.name} className="border-b border-gray-100 last:border-0">
                      <td className="py-1 pr-6 text-gray-600">{n.name}</td>
                      <td className="py-1 text-right font-medium whitespace-nowrap">
                        {n.scaled.toFixed(2)} {n.unit}
                      </td>
                    </tr>
                  ))}
                  {query && nonMatches.length > 0 && (
                    <tr>
                      <td colSpan={2} className="py-1">
                        <hr className="border-gray-300" />
                      </td>
                    </tr>
                  )}
                  {nonMatches.map((n) => (
                    <tr key={n.name} className="border-b border-gray-100 last:border-0 opacity-40">
                      <td className="py-1 pr-6">{n.name}</td>
                      <td className="py-1 text-right whitespace-nowrap">
                        {n.scaled.toFixed(2)} {n.unit}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
