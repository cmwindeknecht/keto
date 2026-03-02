"use client";

import { useState, useEffect, useRef } from "react";
import { GRAMS_PER_UNIT, UNIT_LABELS, gramsToUnit, type WeightUnit } from "@/lib/units";

interface QuantityInputProps {
  /** Current value, always in grams */
  readonly value: number;
  readonly onChange: (grams: number) => void;
  readonly inputClassName?: string;
  readonly inputId?: string;
  /** When set, switches to serving mode: input is a count, unit label is fixed */
  readonly servingGrams?: number;
  readonly servingLabel?: string;
}

export function QuantityInput({
  value,
  onChange,
  inputClassName = "w-20 px-2 py-1 border rounded text-sm",
  inputId,
  servingGrams,
  servingLabel,
}: QuantityInputProps) {
  const [unit, setUnit] = useState<WeightUnit>("g");

  const [inputValue, setInputValue] = useState(() => {
    if (servingGrams && servingGrams > 0) {
      return String(Number.parseFloat((value / servingGrams).toFixed(2)));
    }
    return String(Number.parseFloat(gramsToUnit(value, "g").toFixed(1)));
  });

  const lastSentGrams = useRef(value);
  const prevServingGrams = useRef(servingGrams);

  useEffect(() => {
    const modeChanged = prevServingGrams.current !== servingGrams;
    prevServingGrams.current = servingGrams;

    if (Math.abs(value - lastSentGrams.current) > 0.01 || modeChanged) {
      lastSentGrams.current = value;
      if (servingGrams && servingGrams > 0) {
        setInputValue(String(Number.parseFloat((value / servingGrams).toFixed(2))));
      } else {
        setUnit("g");
        setInputValue(String(Number.parseFloat(value.toFixed(2))));
      }
    }
  }, [value, servingGrams]);

  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    const num = Number.parseFloat(e.target.value);
    if (!Number.isNaN(num) && num > 0) {
      const grams =
        servingGrams && servingGrams > 0 ? num * servingGrams : num * GRAMS_PER_UNIT[unit];
      lastSentGrams.current = grams;
      onChange(grams);
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
      {servingGrams && servingGrams > 0 ? (
        <span className="px-2 py-1 border rounded text-sm bg-gray-50 text-gray-600 whitespace-nowrap">
          {servingLabel ?? "serving"}
        </span>
      ) : (
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
      )}
    </div>
  );
}
