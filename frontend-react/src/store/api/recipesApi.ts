import { baseApi } from "./baseApi";

export interface Nutrient {
  readonly nutrient: {
    readonly id: number;
    readonly number: string;
    readonly name: string;
    readonly unitName: string;
  };
  readonly amount: number;
  readonly dataPoints?: number;
  readonly derivationCode?: string;
}

export interface NutrientInfo {
  readonly name: string;
  readonly amount: number;
  readonly unit: string;
}

export interface IngredientDetail {
  readonly usda_fdc_id: number;
  readonly name: string;
  readonly data_type?: string;
  readonly brand_owner?: string;
  readonly nutrients: NutrientInfo[];
}

export interface RecipeIngredient {
  readonly id: string;
  readonly ingredient: IngredientDetail;
  readonly quantity_grams: number;
  readonly nutrients: NutrientInfo[];
}

export interface Recipe {
  readonly id: string;
  readonly name: string;
  readonly cuisine?: string;
  readonly description?: string;
  readonly ingredients: RecipeIngredient[];
  readonly nutrients: NutrientInfo[];
  readonly created_at?: string;
  readonly updated_at?: string;
}

export interface RecipeIngredientInput {
  readonly usda_fdc_id: number;
  readonly quantity_grams: number;
}

export interface CreateRecipeRequest {
  readonly name: string;
  readonly cuisine: string;
  readonly description?: string;
  readonly ingredients?: RecipeIngredientInput[];
}

export interface UpdateRecipeRequest {
  readonly name?: string;
  readonly cuisine?: string;
  readonly description?: string;
}

export interface AddIngredientRequest {
  readonly usda_fdc_id: number;
  readonly quantity_grams: number;
}

export const recipesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    listRecipes: builder.query<Recipe[], void>({
      query: () => "/recipes",
      providesTags: [{ type: "Recipe", id: "LIST" }],
    }),

    getRecipe: builder.query<Recipe, string>({
      query: (id) => `/recipes/${id}`,
      providesTags: (_result, _error, id) => [{ type: "Recipe", id }],
    }),

    createRecipe: builder.mutation<Recipe, CreateRecipeRequest>({
      query: (body) => ({
        url: "/recipes",
        method: "POST",
        body,
      }),
      invalidatesTags: [{ type: "Recipe", id: "LIST" }],
    }),

    updateRecipe: builder.mutation<Recipe, { id: string; body: UpdateRecipeRequest }>({
      query: ({ id, body }) => ({
        url: `/recipes/${id}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Recipe", id },
        { type: "Recipe", id: "LIST" },
      ],
    }),

    deleteRecipe: builder.mutation<void, string>({
      query: (id) => ({
        url: `/recipes/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: [{ type: "Recipe", id: "LIST" }],
    }),

    addIngredient: builder.mutation<Recipe, { id: string; body: AddIngredientRequest }>({
      query: ({ id, body }) => ({
        url: `/recipes/${id}/ingredients`,
        method: "POST",
        body,
      }),
      invalidatesTags: (_result, _error, { id }) => [
        { type: "Recipe", id },
        { type: "Recipe", id: "LIST" },
      ],
    }),

    updateIngredient: builder.mutation<
      Recipe,
      { recipeId: string; ingredientId: string; body: AddIngredientRequest }
    >({
      query: ({ recipeId, ingredientId, body }) => ({
        url: `/recipes/${recipeId}/ingredients/${ingredientId}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (_result, _error, { recipeId }) => [
        { type: "Recipe", id: recipeId },
        { type: "Recipe", id: "LIST" },
      ],
    }),

    removeIngredient: builder.mutation<Recipe, { recipeId: string; ingredientId: string }>({
      query: ({ recipeId, ingredientId }) => ({
        url: `/recipes/${recipeId}/ingredients/${ingredientId}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { recipeId }) => [
        { type: "Recipe", id: recipeId },
        { type: "Recipe", id: "LIST" },
      ],
    }),
  }),
});

export const {
  useListRecipesQuery,
  useGetRecipeQuery,
  useCreateRecipeMutation,
  useUpdateRecipeMutation,
  useDeleteRecipeMutation,
  useAddIngredientMutation,
  useUpdateIngredientMutation,
  useRemoveIngredientMutation,
} = recipesApi;
