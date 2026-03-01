"use client";

import { useState } from "react";
import { GRAMS_PER_UNIT, UNIT_LABELS, gramsToUnit } from "@/lib/units";
import type { WeightUnit } from "@/lib/units";

interface QuantityInputProps {
  /** Current value, always in grams */
  readonly value: number;
  readonly onChange: (grams: number) => void;
  readonly inputClassName?: string;
  readonly inputId?: string;
}

export function QuantityInput({
  value,
  onChange,
  inputClassName = "w-20 px-2 py-1 border rounded text-sm",
  inputId,
}: QuantityInputProps) {
  const [unit, setUnit] = useState<WeightUnit>("g");
  // Keep raw input string so the user can type freely without rounding interference
  const [inputValue, setInputValue] = useState(() =>
    String(Number.parseFloat(gramsToUnit(value, "g").toFixed(1))),
  );

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    const num = Number.parseFloat(e.target.value);
    if (!Number.isNaN(num) && num > 0) {
      onChange(num * GRAMS_PER_UNIT[unit]);
    }
  };

  const handleUnitChange = (newUnit: WeightUnit) => {
    const converted = Number.parseFloat(gramsToUnit(value, newUnit).toFixed(3));
    setInputValue(String(converted));
    setUnit(newUnit);
  };

  return (
    <div className="flex items-center gap-1">
      <input
        id={inputId}
        type="number"
        value={inputValue}
        onChange={handleValueChange}
        className={inputClassName}
        min="0.001"
        step="any"
      />
      <select
        value={unit}
        onChange={(e) => handleUnitChange(e.target.value as WeightUnit)}
        className="px-2 py-1 border rounded text-sm"
      >
        {(Object.keys(GRAMS_PER_UNIT) as WeightUnit[]).map((u) => (
          <option key={u} value={u}>
            {UNIT_LABELS[u]}
          </option>
        ))}
      </select>
    </div>
  );
}
