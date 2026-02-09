# Keto Recipe API - FastAPI Backend

FastAPI service for the Keto Recipe platform. Handles USDA FoodData Central API integration, recipe management, nutrition calculation, and internal API endpoints.

## Architecture

```
app/
├── core/           # Configuration, exceptions, logging
├── db/            # Database connections and ORM models
├── models/        # Pydantic request/response schemas
├── routes/        # API endpoint handlers
│   └── internal/  # Internal service endpoints
├── services/      # Business logic services
└── main.py        # FastAPI app initialization
```

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Docker (optional)

### Installation

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env .env.local  # Create local .env file
# Edit .env.local with your configuration
```

## Running the Service

### Development

```bash
python app/main.py
```

The API will be available at `http://localhost:8000`

- API Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### With Docker

```bash
docker build -t keto-recipe-api .
docker run -p 8000:8000 --env-file .env keto-recipe-api
```

## API Endpoints

### Health Check

```
GET /health
```

### Internal Endpoints

These are called internally by the Go gateway.

#### Recipe Management

- `POST /internal/recipes/` - Create a new recipe with ingredients
- `GET /internal/recipes/{recipe_id}` - Get recipe with calculated nutrition
- `GET /internal/recipes/` - List recipes (with optional cuisine filter)
- `PUT /internal/recipes/{recipe_id}` - Update recipe details
- `DELETE /internal/recipes/{recipe_id}` - Delete a recipe
- `POST /internal/recipes/{recipe_id}/ingredients` - Add ingredient to recipe
- `DELETE /internal/recipes/{recipe_id}/ingredients/{ingredient_id}` - Remove ingredient

#### Ingredient Search

- `POST /internal/recipes/search-ingredients` - Search USDA FoodData Central for ingredients

See [USDA_API.md](./USDA_API.md) for details on USDA integration.

## Testing

Run tests with coverage:

```bash
pytest --cov=app --cov-report=html
```

## Conventions

- All endpoints use `async/await`
- Pydantic models for all request/response schemas
- Type hints required for all functions
- Max line length: 150 characters
- Error handling with HTTPException
- Database access through dependency injection

## Notes for Claude

**Please call out incorrect assumptions.** If asked to check something but it's patently incorrect, tell me directly rather than pretending to verify. Example: "That file doesn't exist" or "Requirements.txt is already there"—no need to run checks that will obviously fail or waste time being overly polite.

**When defining properties, always include setters.** If a class uses `@property` decorators, make sure to add corresponding `@property_name.setter` methods. Read-only properties will cause `AttributeError` at runtime when assignment is attempted.

## Development

### Adding New Endpoints

1. Create a route file in `app/routes/`
2. Define Pydantic models in `app/models/`
3. Implement business logic in `app/services/`
4. Add tests in `tests/`
5. Include router in `app/main.py`

### Adding New Services

1. Create service class in `app/services/`
2. Use dependency injection where needed
3. Add proper error handling with custom exceptions
4. Write tests for business logic

## Dependencies

See `requirements.txt` for full list. Key dependencies:

- **FastAPI**: Modern web framework
- **SQLAlchemy**: ORM for database
- **asyncpg**: PostgreSQL async driver
- **redis**: Redis client
- **httpx**: Async HTTP client
- **pydantic**: Data validation
