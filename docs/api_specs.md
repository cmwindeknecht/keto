# API Specifications

Keto Recipe API endpoints for recipe management and USDA ingredient search.

## Go API Gateway (Public Endpoints)

### POST /api/recipes
Create a new recipe

Request:
```json
{
  "name": "Keto Burger",
  "cuisine": "American",
  "description": "Low carb burger",
  "servings": 2,
  "rating": 85,
  "ingredients": [
    {
      "usda_fdc_id": 123456,
      "quantity_grams": 150
    }
  ]
}
```

Response: Recipe object with calculated nutrition

### GET /api/recipes/:id
Get recipe by ID

### GET /api/recipes
List recipes with pagination

Query params:
- `skip`: Offset (default: 0)
- `limit`: Max results (default: 20)
- `cuisine`: Filter by cuisine

### PUT /api/recipes/:id
Update recipe

### DELETE /api/recipes/:id
Delete recipe

### GET /api/ingredients/search
Search USDA FoodData Central for ingredients

Query params:
- `q`: Search query
- `limit`: Max results (default: 10)

Response:
```json
{
  "foods": [
    {
      "fdcId": 123456,
      "description": "Beef, ground",
      "dataType": "Survey (FNDDS)"
    }
  ]
}
```

## FastAPI (Internal Endpoints)

### POST /internal/usda/search
Search USDA FoodData Central API

### GET /internal/recipes/health
Health check endpoint
