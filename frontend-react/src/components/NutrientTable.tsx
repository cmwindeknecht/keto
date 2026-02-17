import { Nutrient } from "@/store/api/recipesApi";

interface NutrientTableProps {
  nutrients: Nutrient[];
  quantityGrams: number;
}

const NUTRIENT_MAP: Record<number, { label: string; unit: string }> = {
  1008: { label: "Calories", unit: "kcal" },
  1004: { label: "Fat", unit: "g" },
  1005: { label: "Carbohydrates", unit: "g" },
  1079: { label: "Fiber", unit: "g" },
  1093: { label: "Sodium", unit: "mg" },
  1092: { label: "Potassium", unit: "mg" },
  1090: { label: "Magnesium", unit: "mg" },
};

const PRIMARY_NUTRIENTS = [1008, 1004, 1005, 1079, 1093, 1092, 1090];

function getNutrientValue(nutrients: Nutrient[], nutrientId: number): number {
  const nutrient = nutrients.find((n) => parseInt(n.nutrient.number) === nutrientId);
  return nutrient ? nutrient.amount : 0;
}

function scaleNutrient(per100g: number, quantityGrams: number): number {
  return (per100g * quantityGrams) / 100;
}

export function NutrientTable({ nutrients, quantityGrams }: NutrientTableProps) {
  const getDisplayValue = (nutrientId: number) => {
    const per100g = getNutrientValue(nutrients, nutrientId);
    return scaleNutrient(per100g, quantityGrams);
  };

  const netCarbs = getDisplayValue(1005) - getDisplayValue(1079);

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 border-b">
            <th className="text-left p-3">Nutrient</th>
            <th className="text-right p-3">Amount</th>
          </tr>
        </thead>
        <tbody>
          {PRIMARY_NUTRIENTS.map((nutrientId) => {
            const meta = NUTRIENT_MAP[nutrientId];
            if (!meta) return null;

            const value = getDisplayValue(nutrientId);
            const isHighlight =
              nutrientId === 1008 ||
              nutrientId === 1004 ||
              nutrientId === 1005 ||
              nutrientId === 1079 ||
              nutrientId === 1093 ||
              nutrientId === 1092 ||
              nutrientId === 1090;

            return (
              <tr
                key={nutrientId}
                className={`border-b ${isHighlight ? "bg-blue-50" : ""}`}
              >
                <td className="p-3">{meta.label}</td>
                <td className="text-right p-3">
                  {value.toFixed(2)} {meta.unit}
                </td>
              </tr>
            );
          })}
          <tr className="bg-green-50 border-b">
            <td className="p-3 font-semibold">Net Carbs</td>
            <td className="text-right p-3 font-semibold">
              {netCarbs.toFixed(2)} g
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
