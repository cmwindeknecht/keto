import { baseApi } from "./baseApi";
import { Nutrient } from "./recipesApi";

export interface USDASearchRequest {
  query: string;
  pageSize?: number;
}

export interface USDAFood {
  fdc_id: string;
  description: string;
  data_type: string;
  brand_name?: string;
  foodNutrients: Nutrient[];
}

export interface USDASearchResponse {
  foods: USDAFood[];
}

export const usdaApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    search: builder.mutation<USDASearchResponse, USDASearchRequest>({
      query: (body) => ({
        url: "/usda/search",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useSearchMutation } = usdaApi;
