import { describe, it, expect } from "vitest";
import lookupReducer, { selectFood, setQuantity, setUnit, clearSelection } from "../lookupSlice";
import type { USDAFood } from "@/store/api/usdaApi";

const mockFood: USDAFood = {
  fdcId: 12345,
  description: "Chicken Breast, raw",
  dataType: "Foundation",
  foodNutrients: [
    {
      nutrientId: 1008,
      nutrientNumber: "208",
      nutrientName: "Energy",
      value: 120,
      unitName: "kcal",
    },
  ],
};

describe("lookupSlice", () => {
  const initialState = { selectedFood: null, quantity: 100, unit: "g" as const };

  describe("initial state", () => {
    it("returns the initial state when called with undefined", () => {
      expect(lookupReducer(undefined, { type: "@@INIT" })).toEqual(initialState);
    });

    it("starts with no selected food", () => {
      const state = lookupReducer(undefined, { type: "@@INIT" });
      expect(state.selectedFood).toBeNull();
    });

    it("starts with quantity 100", () => {
      const state = lookupReducer(undefined, { type: "@@INIT" });
      expect(state.quantity).toBe(100);
    });

    it("starts with unit 'g'", () => {
      const state = lookupReducer(undefined, { type: "@@INIT" });
      expect(state.unit).toBe("g");
    });
  });

  describe("selectFood", () => {
    it("sets the selected food", () => {
      const state = lookupReducer(initialState, selectFood(mockFood));
      expect(state.selectedFood).toEqual(mockFood);
    });

    it("replaces any previously selected food", () => {
      const otherFood: USDAFood = { fdcId: 999, description: "Broccoli", foodNutrients: [] };
      const withFood = lookupReducer(initialState, selectFood(mockFood));
      const replaced = lookupReducer(withFood, selectFood(otherFood));
      expect(replaced.selectedFood?.fdcId).toBe(999);
    });

    it("does not affect quantity or unit", () => {
      const state = lookupReducer(initialState, selectFood(mockFood));
      expect(state.quantity).toBe(initialState.quantity);
      expect(state.unit).toBe(initialState.unit);
    });
  });

  describe("setQuantity", () => {
    it("updates the quantity", () => {
      const state = lookupReducer(initialState, setQuantity(250));
      expect(state.quantity).toBe(250);
    });

    it("accepts 0", () => {
      const state = lookupReducer(initialState, setQuantity(0));
      expect(state.quantity).toBe(0);
    });

    it("accepts decimal values", () => {
      const state = lookupReducer(initialState, setQuantity(28.35));
      expect(state.quantity).toBe(28.35);
    });

    it("does not affect selectedFood or unit", () => {
      const withFood = { ...initialState, selectedFood: mockFood };
      const state = lookupReducer(withFood, setQuantity(200));
      expect(state.selectedFood).toEqual(mockFood);
      expect(state.unit).toBe("g");
    });
  });

  describe("setUnit", () => {
    it("sets unit to oz", () => {
      const state = lookupReducer(initialState, setUnit("oz"));
      expect(state.unit).toBe("oz");
    });

    it("sets unit to lb", () => {
      const state = lookupReducer(initialState, setUnit("lb"));
      expect(state.unit).toBe("lb");
    });

    it("sets unit back to g", () => {
      const withOz = { ...initialState, unit: "oz" as const };
      const state = lookupReducer(withOz, setUnit("g"));
      expect(state.unit).toBe("g");
    });

    it("does not affect selectedFood or quantity", () => {
      const withFood = { ...initialState, selectedFood: mockFood, quantity: 250 };
      const state = lookupReducer(withFood, setUnit("oz"));
      expect(state.selectedFood).toEqual(mockFood);
      expect(state.quantity).toBe(250);
    });
  });

  describe("clearSelection", () => {
    it("resets all state to initial values", () => {
      const populated = { selectedFood: mockFood, quantity: 500, unit: "lb" as const };
      expect(lookupReducer(populated, clearSelection())).toEqual(initialState);
    });

    it("clears selectedFood to null", () => {
      const withFood = { ...initialState, selectedFood: mockFood };
      const state = lookupReducer(withFood, clearSelection());
      expect(state.selectedFood).toBeNull();
    });

    it("resets quantity to 100", () => {
      const withQty = { ...initialState, quantity: 999 };
      expect(lookupReducer(withQty, clearSelection()).quantity).toBe(100);
    });

    it("resets unit to 'g'", () => {
      const withUnit = { ...initialState, unit: "lb" as const };
      expect(lookupReducer(withUnit, clearSelection()).unit).toBe("g");
    });
  });
});
