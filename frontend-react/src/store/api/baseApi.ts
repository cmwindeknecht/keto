import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8080";
const apiKey = process.env.NEXT_PUBLIC_API_KEY;

if (typeof window !== "undefined") {
  console.log("[RTK Query] baseUrl:", baseUrl);
  console.log("[RTK Query] apiKey:", apiKey);
}

const baseQuery = fetchBaseQuery({
  baseUrl,
  prepareHeaders: (headers) => {
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
