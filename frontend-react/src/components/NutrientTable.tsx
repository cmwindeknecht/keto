import { Nutrient } from "@/store/api/recipesApi";

interface NutrientTableProps {
  readonly nutrients: Nutrient[];
  readonly quantityGrams: number;
}

const NUTRIENT_MAP: Record<number, { label: string; unit: string }> = {
  1008: { label: "Calories", unit: "kcal" },
  1004: { label: "Fat", unit: "g" },
  1005: { label: "Carbs", unit: "g" },
  1079: { label: "Fiber", unit: "g" },
  1093: { label: "Sodium", unit: "mg" },
  1092: { label: "Potassium", unit: "mg" },
  1090: { label: "Magnesium", unit: "mg" },
};

const PRIMARY_NUTRIENTS = [1008, 1004, 1005, 1079, 1093, 1092, 1090];

function getNutrientValue(nutrients: Nutrient[], nutrientId: number): number {
  const nutrient = nutrients.find(
    (n) => Number.parseInt(n.nutrient.number) === nutrientId,
  );
  return nutrient ? nutrient.amount : 0;
}

function scaleNutrient(per100g: number, quantityGrams: number): number {
  return (per100g * quantityGrams) / 100;
}

export function NutrientTable({
  nutrients,
  quantityGrams,
}: NutrientTableProps) {
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

  return (
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
              <td
                key={col.id}
                className="px-3 py-1 text-center font-semibold whitespace-nowrap"
              >
                {col.value}
              </td>
            ))}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
