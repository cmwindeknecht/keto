import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseQuery = fetchBaseQuery({
  baseUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080",
  prepareHeaders: (headers) => {
    const apiKey = process.env.NEXT_PUBLIC_API_KEY;
    if (apiKey) {
      headers.set("X-API-Key", apiKey);
    }
    return headers;
  },
});

export const baseApi = createApi({
  baseQuery,
  tagTypes: ["Recipe"],
  endpoints: () => ({}),
});
