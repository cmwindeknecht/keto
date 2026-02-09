# USDA FoodData Central API Documentation

> **Last modified:** 2020-04-30

## Overview

The FoodData Central API provides REST access to FoodData Central (FDC). It is intended primarily to assist application developers wishing to incorporate nutrient data into their applications or websites.

To take full advantage of the API, developers should familiarize themselves with the database by reading the database documentation available via links on [Data Type Documentation](https://fdc.nal.usda.gov/data-documentation.html). This documentation provides the detailed definitions and descriptions needed to understand the data elements referenced in the API documentation.

Additional details about the API including rate limits, access, and licensing are available on the [FDC website](https://fdc.nal.usda.gov/api-guide.html).

**Version:** 1.0.1
**Base URL:** `https://api.nal.usda.gov/fdc`
**Authentication:** API Key (via query parameter `api_key`)

---

## Endpoints

### 1. Get Food by FDC ID

**Endpoint:** `GET /v1/food/{fdcId}`

Retrieves a single food item by an FDC ID. Optional format and nutrients can be specified.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `fdcId` | Path | String | Yes | FDC id of the food to retrieve |
| `format` | Query | String | No | 'abridged' for abridged set, 'full' for all elements (default) |
| `nutrients` | Query | Array[Integer] | No | List of up to 25 nutrient numbers (comma-separated or repeating parameters) |

#### Response

**200 OK** - One food result
- Returns one of: `AbridgedFoodItem`, `BrandedFoodItem`, `FoundationFoodItem`, `SRLegacyFoodItem`, `SurveyFoodItem`

**400** - Bad input parameter

**404** - No results found

---

### 2. Get Multiple Foods by FDC IDs (GET)

**Endpoint:** `GET /v1/foods`

Retrieves a list of food items by a list of up to 20 FDC IDs. Optional format and nutrients can be specified. Invalid FDC IDs or ones that are not found are omitted.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `fdcIds` | Query | Array[String] | Yes | List of FDC IDs (comma-separated or repeating parameters) |
| `format` | Query | String | No | 'abridged' or 'full' (default) |
| `nutrients` | Query | Array[Integer] | No | List of up to 25 nutrient numbers |

#### Response

**200 OK** - List of food details matching specified FDC IDs

**400** - Bad input parameter

---

### 3. Get Multiple Foods by FDC IDs (POST)

**Endpoint:** `POST /v1/foods`

Retrieves a list of food items by a list of up to 20 FDC IDs. Optional format and nutrients can be specified.

#### Request Body

```json
{
  "fdcIds": [534358, 373052, 616350],
  "format": "full",
  "nutrients": [203, 204, 205]
}
```

**Schema:** `FoodsCriteria`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `fdcIds` | Array[Integer] | Yes | List of FDC IDs (1-20 items) |
| `format` | String | No | 'abridged' or 'full' (default) |
| `nutrients` | Array[Integer] | No | List of up to 25 nutrient numbers |

#### Response

**200 OK** - List of food details

**400** - Bad input parameter

---

### 4. List All Foods (GET)

**Endpoint:** `GET /v1/foods/list`

Returns a paged list of foods in the 'abridged' format. Use the pageNumber parameter to page through the entire result set.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `dataType` | Query | Array[String] | No | Filter by data type: Branded, Foundation, Survey (FNDDS), SR Legacy |
| `pageSize` | Query | Integer | No | Max results per page (1-200, default 50) |
| `pageNumber` | Query | Integer | No | Page number to retrieve |
| `sortBy` | Query | String | No | Sort field: dataType.keyword, lowercaseDescription.keyword, fdcId, publishedDate |
| `sortOrder` | Query | String | No | 'asc' or 'desc' |

#### Response

**200 OK** - List of foods for the requested page

**400** - Bad input parameter

---

### 5. List All Foods (POST)

**Endpoint:** `POST /v1/foods/list`

Returns a paged list of foods in the 'abridged' format.

#### Request Body

**Schema:** `FoodListCriteria`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dataType` | Array[String] | No | Filter by data type |
| `pageSize` | Integer | No | Max results per page (1-200, default 50) |
| `pageNumber` | Integer | No | Page number |
| `sortBy` | String | No | Sort field |
| `sortOrder` | String | No | 'asc' or 'desc' |

#### Response

**200 OK** - List of foods for the requested page

**400** - Bad input parameter

---

### 6. Search Foods (GET)

**Endpoint:** `GET /v1/foods/search`

Search for foods using keywords. Results can be filtered by dataType and there are options for result page sizes or sorting.

#### Parameters

| Name | Location | Type | Required | Description |
|------|----------|------|----------|-------------|
| `query` | Query | String | Yes | One or more search terms (supports [search operators](https://fdc.nal.usda.gov/help.html#bkmk-2)) |
| `dataType` | Query | Array[String] | No | Filter by data type |
| `pageSize` | Query | Integer | No | Max results per page (1-200, default 50) |
| `pageNumber` | Query | Integer | No | Page number |
| `sortBy` | Query | String | No | Sort field |
| `sortOrder` | Query | String | No | 'asc' or 'desc' |
| `brandOwner` | Query | String | No | Filter by brand owner (Branded Foods only) |

#### Response

**200 OK** - List of foods matching search criteria

```json
{
  "foodSearchCriteria": { ... },
  "totalHits": 1034,
  "currentPage": 1,
  "totalPages": 35,
  "foods": [ ... ]
}
```

**400** - Bad input parameter

---

### 7. Search Foods (POST)

**Endpoint:** `POST /v1/foods/search`

Search for foods using keywords with POST request body.

#### Request Body

**Schema:** `FoodSearchCriteria`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | String | Yes | Search terms |
| `dataType` | Array[String] | No | Filter by data type |
| `pageSize` | Integer | No | Max results per page |
| `pageNumber` | Integer | No | Page number |
| `sortBy` | String | No | Sort field |
| `sortOrder` | String | No | 'asc' or 'desc' |
| `brandOwner` | String | No | Filter by brand owner |
| `tradeChannel` | Array[String] | No | Filter by trade channel |
| `startDate` | String | No | Filter foods published after this date (YYYY-MM-DD) |
| `endDate` | String | No | Filter foods published before this date (YYYY-MM-DD) |

#### Response

**200 OK** - List of foods matching search criteria

**400** - Bad input parameter

---

## Request/Response Models

### FoodsCriteria

```typescript
{
  fdcIds: number[];           // 1-20 items, required
  format?: 'abridged' | 'full';  // optional, default 'full'
  nutrients?: number[];       // 1-25 items, nutrient numbers
}
```

### FoodListCriteria

```typescript
{
  dataType?: ('Branded' | 'Foundation' | 'Survey (FNDDS)' | 'SR Legacy')[];
  pageSize?: number;          // 1-200, default 50
  pageNumber?: number;
  sortBy?: 'dataType.keyword' | 'lowercaseDescription.keyword' | 'fdcId' | 'publishedDate';
  sortOrder?: 'asc' | 'desc';
}
```

### FoodSearchCriteria

```typescript
{
  query: string;              // required
  dataType?: ('Branded' | 'Foundation' | 'Survey (FNDDS)' | 'SR Legacy')[];
  pageSize?: number;          // 1-200, default 50
  pageNumber?: number;
  sortBy?: 'dataType.keyword' | 'lowercaseDescription.keyword' | 'fdcId' | 'publishedDate';
  sortOrder?: 'asc' | 'desc';
  brandOwner?: string;
  tradeChannel?: ('CHILD_NUTRITION_FOOD_PROGRAMS' | 'DRUG' | 'FOOD_SERVICE' | 'GROCERY' | 'MASS_MERCHANDISING' | 'MILITARY' | 'ONLINE' | 'VENDING')[];
  startDate?: string;         // YYYY-MM-DD format
  endDate?: string;           // YYYY-MM-DD format
}
```

### Food Items

All food endpoints return one or more of these food item types:
- `AbridgedFoodItem` - Basic food information
- `BrandedFoodItem` - Branded food with detailed nutrition
- `FoundationFoodItem` - Foundation food with detailed nutrition
- `SRLegacyFoodItem` - Legacy food item
- `SurveyFoodItem` - Survey (FNDDS) food item

---

## Notes

- All requests require an API key passed as the `api_key` query parameter
- POST endpoints provide an alternative to GET for complex queries with request bodies
- Most numeric IDs (fdcId, nutrient numbers) are integers
- Food data varies by type; some fields only apply to specific food types
