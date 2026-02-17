import { configureStore } from "@reduxjs/toolkit";
import { baseApi } from "./api/baseApi";
import lookupReducer from "./slices/lookupSlice";

export const store = configureStore({
  reducer: {
    [baseApi.reducerPath]: baseApi.reducer,
    lookup: lookupReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(baseApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
