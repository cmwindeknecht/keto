# Steam Analytics FastAPI Backend

FastAPI service for the Steam Analytics platform. Handles Steam API integration, data processing, and internal API endpoints.

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
docker build -t steamanalytics-api .
docker run -p 8000:8000 --env-file .env steamanalytics-api
```

## API Endpoints

### Health Check

```
GET /health
```

### Internal Endpoints

These are called internally by the Go gateway.

#### Fetch Game from Steam

```
POST /internal/games/fetch

Request:
{
  "steam_app_id": 570
}

Response:
{
  "success": true,
  "game_id": 1,
  "error": null
}
```

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
