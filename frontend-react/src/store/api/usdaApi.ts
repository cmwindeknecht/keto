import { baseApi } from "./baseApi";

export interface USDASearchRequest {
  query: string;
  dataType?: string[];
  pageSize?: number;
  brandOwner?: string;
}

export interface USDANutrient {
  nutrientId: number;
  nutrientNumber: string;
  nutrientName: string;
  value: number;
  unitName: string;
}

export interface USDAFood {
  fdcId: number;
  description: string;
  dataType?: string;
  brandOwner?: string;
  foodNutrients: USDANutrient[];
}

export const usdaApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    search: builder.mutation<USDAFood[], USDASearchRequest>({
      query: (body) => ({
        url: "/usda/search",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useSearchMutation } = usdaApi;
