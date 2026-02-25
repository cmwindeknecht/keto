import { baseApi } from "./baseApi";

export interface Nutrient {
  nutrient: {
    id: number;
    number: string;
    name: string;
    unitName: string;
  };
  amount: number;
  dataPoints?: number;
  derivationCode?: string;
}

export interface NutrientInfo {
  name: string;
  amount: number;
  unit: string;
}

export interface IngredientDetail {
  usda_fdc_id: number;
  name: string;
  data_type?: string;
  brand_owner?: string;
  nutrients: NutrientInfo[];
}

export interface RecipeIngredient {
  id: string;
  ingredient: IngredientDetail;
  quantity_grams: number;
  nutrients: NutrientInfo[];
}

export interface Recipe {
  id: string;
  name: string;
  cuisine?: string;
  description?: string;
  ingredients: RecipeIngredient[];
  nutrients: NutrientInfo[];
  created_at?: string;
  updated_at?: string;
}

export interface RecipeIngredientInput {
  usda_fdc_id: number;
  quantity_grams: number;
}

export interface CreateRecipeRequest {
  name: string;
  cuisine: string;
  description?: string;
  ingredients?: RecipeIngredientInput[];
}

export interface UpdateRecipeRequest {
  name?: string;
  cuisine?: string;
  description?: string;
}

export interface AddIngredientRequest {
  usda_fdc_id: number;
  quantity_grams: number;
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
      invalidatesTags: (_result, _error, { id }) => [{ type: "Recipe", id }, { type: "Recipe", id: "LIST" }],
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
      invalidatesTags: (_result, _error, { id }) => [{ type: "Recipe", id }, { type: "Recipe", id: "LIST" }],
    }),

    removeIngredient: builder.mutation<Recipe, { recipeId: string; ingredientId: string }>({
      query: ({ recipeId, ingredientId }) => ({
        url: `/recipes/${recipeId}/ingredients/${ingredientId}`,
        method: "DELETE",
      }),
      invalidatesTags: (_result, _error, { recipeId }) => [{ type: "Recipe", id: recipeId }, { type: "Recipe", id: "LIST" }],
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
  useRemoveIngredientMutation,
} = recipesApi;
