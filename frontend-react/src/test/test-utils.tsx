import type { ReactElement } from "react";
import { render, type RenderOptions } from "@testing-library/react";
import { configureStore } from "@reduxjs/toolkit";
import { Provider } from "react-redux";
import { baseApi } from "@/store/api/baseApi";
import lookupReducer from "@/store/slices/lookupSlice";

export function createTestStore() {
  return configureStore({
    reducer: {
      [baseApi.reducerPath]: baseApi.reducer,
      lookup: lookupReducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware().concat(baseApi.middleware),
  });
}

export function renderWithStore(ui: ReactElement, options?: RenderOptions) {
  const store = createTestStore();
  return render(<Provider store={store}>{ui}</Provider>, options);
}

export * from "@testing-library/react";
