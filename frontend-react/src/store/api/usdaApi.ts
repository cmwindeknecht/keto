import { baseApi } from "./baseApi";

export interface USDASearchRequest {
  readonly query: string;
  readonly dataType?: string[];
  readonly pageSize?: number;
  readonly brandOwner?: string;
}

export interface USDANutrient {
  readonly nutrientId: number;
  readonly nutrientNumber: string;
  readonly nutrientName: string;
  readonly value: number;
  readonly unitName: string;
}

export interface FoodPortion {
  readonly id?: number;
  readonly amount?: number;
  readonly gramWeight?: number;
  readonly portionDescription?: string;
  readonly modifier?: string;
  readonly measureUnit?: {
    readonly id?: number;
    readonly name?: string;
    readonly abbreviation?: string;
  };
}

export interface USDAFood {
  readonly fdcId: number;
  readonly description: string;
  readonly dataType?: string;
  readonly brandOwner?: string;
  readonly foodNutrients: USDANutrient[];
  readonly foodPortions?: FoodPortion[];
  readonly servingSize?: number;
  readonly servingSizeUnit?: string;
  readonly householdServingFullText?: string;
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
    getFoodDetails: builder.mutation<USDAFood[], { readonly fdcIds: number[] }>({
      query: (body) => ({
        url: "/usda/foods",
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useSearchMutation, useGetFoodDetailsMutation } = usdaApi;
