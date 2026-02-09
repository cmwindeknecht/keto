# USDA FoodData Central API

This application uses the USDA FoodData Central API to retrieve comprehensive nutrition data for food items.

## API Overview

- **Base URL**: `https://fdc.nal.usda.gov/api/food`
- **Documentation**: https://fdc.nal.usda.gov/api-guide.html
- **Authentication**: Requires a free API key from https://fdc.nal.usda.gov/api-key

## Required Setup

1. Get a free API key from [USDA FoodData Central](https://fdc.nal.usda.gov/api-key)
2. Add your API key to your `.env` file:
   ```
   USDA_API_KEY=your_api_key_here
   ```

## API Endpoints Used

### Search Endpoint
Searches the USDA FoodData Central database for foods matching a query.

**Request:**
```
GET https://fdc.nal.usda.gov/api/food/search
?query=chicken
&pageSize=20
&api_key=YOUR_API_KEY
```

**Parameters:**
- `query` (required): Search term (food name or keyword)
- `pageSize` (optional): Maximum results per page (default: 10, max: 100)
- `api_key` (required): Your USDA API key

**Response:**
Returns a JSON object with a `foods` array containing matching foods with nutrition data.

### Food Details Endpoint
Gets detailed nutrition information for a specific food item.

**Request:**
```
GET https://fdc.nal.usda.gov/api/food/{fdcId}
?api_key=YOUR_API_KEY
```

**Parameters:**
- `{fdcId}` (required): The FDC ID of the food (e.g., "167556")
- `api_key` (required): Your USDA API key

**Response:**
Returns a detailed food object with complete nutrition data.

## Nutrient IDs

The USDA API returns nutrients with specific IDs. We use these key nutrients:

| ID   | Nutrient              | Unit |
|------|----------------------|------|
| 1008 | Energy (kcal)        | kcal |
| 1003 | Protein              | g    |
| 1004 | Total Lipid (Fat)    | g    |
| 1005 | Carbohydrates        | g    |
| 1079 | Fiber, total dietary | g    |

## Rate Limiting

- **Free tier**: 3600 requests per hour per API key
- **Rate limit header**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`

Check the response headers to monitor your usage.

## Food Data Types

USDA FoodData Central contains foods from multiple data types:

1. **Foundation Foods** (fdc_id prefixed with 'SR')
   - Carefully chosen foods representative of American diet
   - Complete nutrient profiles

2. **SR Legacy Foods** (fdc_id prefixed with 'SR')
   - Foods from the original USDA nutrient database
   - Well-researched, complete data

3. **Branded Foods** (various prefixes)
   - Actual commercial products with nutrition labels
   - Most relevant for packaged/processed foods

## Example Request/Response

### Search for Chicken

**Request:**
```bash
curl "https://fdc.nal.usda.gov/api/food/search?query=chicken&pageSize=5&api_key=YOUR_API_KEY"
```

**Response (truncated):**
```json
{
  "foods": [
    {
      "fdcId": "167556",
      "description": "Chicken, broilers or fryers, meat only, raw",
      "foodNutrients": [
        {
          "nutrientId": 1008,
          "value": 165,
          "unitName": "kcal"
        },
        {
          "nutrientId": 1003,
          "value": 18.6,
          "unitName": "g"
        },
        {
          "nutrientId": 1004,
          "value": 9.3,
          "unitName": "g"
        }
      ]
    }
  ],
  "totalHits": 847
}
```

## Keto Recipe App Integration

Our application:

1. **Searches ingredients** using the `/internal/recipes/search-ingredients` endpoint
   - Calls USDA search endpoint
   - Returns results with 100g nutrition data

2. **Caches ingredients** in the local database
   - Stores USDA FDC ID for future reference
   - Stores extracted nutrition data (calories, protein, fat, carbs, fiber)
   - Reduces API calls for frequently used ingredients

3. **Calculates recipe nutrition**
   - Combines ingredient nutrition data based on recipe quantities
   - Provides total macro information for recipes

## Best Practices

- **Cache aggressively**: Store looked-up ingredients in the database to minimize API calls
- **Handle errors gracefully**: USDA API may timeout or be rate-limited
- **Validate quantities**: Ensure reasonable ingredient quantities (1g to 10kg)
- **Use Foundation Foods when possible**: More reliable than branded products

## Troubleshooting

### "API key not configured"
- Ensure `USDA_API_KEY` is set in your `.env` file
- Verify the API key is valid at https://fdc.nal.usda.gov/api-key

### "No results found"
- The ingredient may not exist in USDA database
- Try broader search terms
- Check spelling of ingredient

### "Rate limit exceeded"
- Your API key has hit the 3600 requests/hour limit
- Wait until the next hour to continue
- Consider caching more aggressively

## References

- [USDA FoodData Central](https://fdc.nal.usda.gov/)
- [API Documentation](https://fdc.nal.usda.gov/api-guide.html)
- [Data Types and Scope](https://fdc.nal.usda.gov/what-is-fdc.html)
