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

export interface USDAFood {
  readonly fdcId: number;
  readonly description: string;
  readonly dataType?: string;
  readonly brandOwner?: string;
  readonly foodNutrients: USDANutrient[];
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
