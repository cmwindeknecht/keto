# Testing Guide

This document describes how to run the comprehensive test suite for the Keto backend FastAPI application.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (isolated components)
│   ├── test_cache_service.py
│   ├── test_usda_utils.py
│   └── test_recipe_service.py
├── integration/             # Integration tests (component interactions)
│   ├── test_usda_routes.py
│   └── test_recipe_routes.py
└── test_main.py             # Basic API tests
```

## Running Tests

### Run all tests
```bash
cd backend-fastapi
pytest
```

### Run specific test file
```bash
pytest tests/unit/test_cache_service.py
pytest tests/integration/test_recipe_routes.py
```

### Run specific test
```bash
pytest tests/unit/test_cache_service.py::test_cache_service_connect
```

### Run unit tests only
```bash
pytest tests/unit/
```

### Run integration tests only
```bash
pytest tests/integration/
```

### Run with coverage report
```bash
pytest --cov=app --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`

### Run with verbose output
```bash
pytest -v
```

### Run with detailed failure info
```bash
pytest -vv
```

## Test Coverage

### Unit Tests
- **Cache Service** (`test_cache_service.py`)
  - Redis connection/disconnection
  - Cache key generation
  - Get/set operations
  - Cache clearing
  - Statistics retrieval
  - Error handling

- **USDA Utils** (`test_usda_utils.py`)
  - Nutrient extraction (nested and flat structures)
  - Proportional nutrient calculation
  - Nutrient summation across ingredients
  - Edge cases (empty data, single ingredient, etc.)

- **Recipe Service** (`test_recipe_service.py`)
  - Recipe CRUD operations
  - Ingredient management
  - Error handling (not found, missing ingredients)
  - Database interactions (mocked)

### Integration Tests
- **USDA Routes** (`test_usda_routes.py`)
  - GET /internal/usda/foods (multiple foods by FDC IDs)
  - POST /internal/usda/search (search by criteria)
  - Input validation
  - Response structure verification
  - Empty results handling

- **Recipe Routes** (`test_recipe_routes.py`)
  - POST /internal/recipes (create)
  - GET /internal/recipes (list, with filtering)
  - GET /internal/recipes/{id} (retrieve)
  - PUT /internal/recipes/{id} (update)
  - DELETE /internal/recipes/{id} (delete)
  - POST /internal/recipes/{id}/ingredients (add)
  - DELETE /internal/recipes/{id}/ingredients/{ingredient_id} (remove)

## Test Fixtures

Shared fixtures in `conftest.py`:

- `event_loop` - Async event loop for tests
- `test_engine` - In-memory SQLite database
- `test_db_session` - Database session for async tests
- `test_client` - FastAPI TestClient with mocked database
- `mock_usda_api` - Sample USDA API responses
- `mock_cache_service` - Mocked cache service
- `mock_elasticsearch_service` - Mocked Elasticsearch service
- `mock_kafka_producer` - Mocked Kafka producer

## Mocking Strategy

Tests use `unittest.mock` to isolate components:

1. **External API calls** - USDA API responses are mocked
2. **Database** - In-memory SQLite is used
3. **Cache** - AsyncMock used for Redis operations
4. **Message Queue** - Kafka producer is mocked
5. **Search** - Elasticsearch is mocked

This ensures tests:
- Run fast (no network calls)
- Don't require external services
- Are deterministic and repeatable
- Can run in CI/CD environments

## Common Issues

### AsyncIO Errors
If you see "RuntimeError: no running event loop", ensure:
- `pytest.ini` has `asyncio_mode = auto`
- `pytest-asyncio` is installed
- Async test functions are properly decorated

### Database Errors
If tests fail with database errors:
- Check that SQLite is available with aiosqlite
- Verify `test_db_session` fixture is being used

### Mock Issues
If mocks aren't working:
- Ensure mock is created before route is called
- Use `AsyncMock` for async functions
- Patch the module where the function is imported

## Writing New Tests

### Unit Test Template
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_new_feature(mock_dependency):
    """Test description."""
    # Arrange
    mock_dependency.method.return_value = expected_value

    # Act
    result = await function_under_test()

    # Assert
    assert result == expected_value
    mock_dependency.method.assert_called_once()
```

### Integration Test Template
```python
def test_new_route(test_client):
    """Test endpoint."""
    payload = {"key": "value"}

    response = test_client.post("/api/endpoint", json=payload)

    assert response.status_code == 200
    assert response.json()["field"] == "value"
```

## CI/CD Integration

Run tests in CI with:
```bash
pytest --cov=app --cov-report=xml --cov-report=term-missing
```

This generates:
- XML coverage report for CI tools
- Terminal output with coverage details
