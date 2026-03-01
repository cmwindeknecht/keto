import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { USDAFood } from "../api/usdaApi";

export type UnitType = "g" | "oz" | "lb";

interface LookupState {
  selectedFood: USDAFood | null;
  quantity: number;
  unit: UnitType;
}

const initialState: LookupState = {
  selectedFood: null,
  quantity: 100,
  unit: "g",
};

const lookupSlice = createSlice({
  name: "lookup",
  initialState,
  reducers: {
    selectFood(state, action: PayloadAction<USDAFood>) {
      state.selectedFood = action.payload;
    },
    setQuantity(state, action: PayloadAction<number>) {
      state.quantity = action.payload;
    },
    setUnit(state, action: PayloadAction<UnitType>) {
      state.unit = action.payload;
    },
    clearSelection(state) {
      state.selectedFood = null;
      state.quantity = 100;
      state.unit = "g";
    },
  },
});

export const { selectFood, setQuantity, setUnit, clearSelection } = lookupSlice.actions;
export default lookupSlice.reducer;
