# Keto API Gateway (Go)

A public-facing API gateway that acts as a Backend For Frontend (BFF) for the Keto Recipe API. It provides:

- **Authentication**: JWT and API key validation
- **Caching**: Redis-backed response caching for GET requests
- **Reverse Proxy**: Forward requests to the internal FastAPI backend
- **Rate Limiting**: Ready for edge caching with Fastly

## Architecture

```
Client Request (Port 3000)
         ↓
   Go API Gateway (Port 8080)
         ↓
  FastAPI Backend (Port 8000)
```

## Configuration

Set environment variables or create a `.env` file based on `.env.example`:

- `PORT`: Server port (default: 8080)
- `FASTAPI_URL`: FastAPI backend URL (default: http://localhost:8000)
- `REDIS_URL`: Redis connection string (default: redis:6379)
- `JWT_SECRET`: Secret for JWT validation (change in production!)
- `API_KEYS`: Comma-separated list of valid API keys
- `CACHE_TTL`: Cache TTL in seconds (default: 300)
- `CACHE_ENABLED`: Enable response caching (default: true)
- `DEBUG`: Enable debug logging (default: false)
- `REQUEST_TIMEOUT`: Request timeout in seconds (default: 30)

## Local Development

### Prerequisites
- Go 1.21 or later
- Redis running on localhost:6379
- FastAPI backend running on localhost:8000

### Setup

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env

# Run the gateway
go run cmd/server/main.go
```

### Building

```bash
# Build binary
go build -o ./bin/keto-api ./cmd/server

# Run binary
./bin/keto-api
```

## Docker

```bash
# Build
docker build -f ../docker/backend-go.Dockerfile -t keto-api-gateway .

# Run
docker run -p 8080:8080 \
  -e FASTAPI_URL=http://fastapi:8000 \
  -e REDIS_URL=redis:6379 \
  -e API_KEYS=test-key \
  keto-api-gateway
```

Or use docker-compose:

```bash
docker-compose up backend-go
```

## API Endpoints

### Public (No Auth Required)
- `GET /health` - Health check
- `GET /` - Service info

### Protected (Requires Auth)
All other endpoints require authentication via:

**API Key:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8080/recipes
```

**JWT Bearer Token:**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8080/recipes
```

## BFF Endpoints

The gateway exposes a clean public API that internally proxies to the FastAPI backend:

**Recipe Management:**
- `GET /recipes` - List recipes
- `POST /recipes` - Create recipe
- `GET /recipes/{id}` - Get recipe
- `PUT /recipes/{id}` - Update recipe
- `DELETE /recipes/{id}` - Delete recipe
- `POST /recipes/{id}/ingredients` - Add ingredient
- `DELETE /recipes/{id}/ingredients/{ingredient_id}` - Remove ingredient
- `POST /search-ingredients` - Search ingredients

**USDA Integration:**
- `GET /usda/food/{fdc_id}` - Get food details
- `POST /usda/foods` - Get multiple foods
- `POST /usda/foods/list` - List foods
- `POST /usda/search` - Search foods
- `POST /usda/search/advanced` - Advanced search
- `GET /usda/search-ingredients` - Search ingredients
- `GET /usda/ingredient/{fdc_id}` - Get ingredient details

**Frontend Integration Note:**
The gateway maps these public endpoints to the internal FastAPI endpoints:
- Frontend hits: `GET /recipes`
- Gateway internally calls: `GET /internal/recipes`
- Gateway returns response to frontend (no client knows about /internal)

## Response Headers

The gateway adds these headers to all responses:

- `X-Proxy-By: keto-api-gateway` - Identifies response came from gateway
- `X-Cache: HIT|MISS` - Cache status (if caching enabled)
- `Access-Control-Allow-*` - CORS headers

## Caching

GET requests are cached in Redis with a configurable TTL. The cache key is based on:
- HTTP method
- Request path
- Query string

Only 200 responses are cached. To bypass cache, add `Cache-Control: no-cache` header.

## Security Considerations

- Always change `JWT_SECRET` in production
- Use strong API keys in production
- Deploy behind HTTPS in production
- Consider adding rate limiting with Fastly for edge protection
- Do not expose FastAPI backend directly to clients

## Future Enhancements

1. **Fastly CDN Integration**: Add edge caching, DDoS protection
2. **Rate Limiting**: Per-IP or per-key rate limiting
3. **Request Logging**: Structured logging to files or external services
4. **Metrics**: Prometheus-style metrics collection
5. **GraphQL**: GraphQL gateway layer on top of REST
6. **Request/Response Validation**: Schema validation with OpenAPI

## Testing

### Using Swagger UI (Recommended)
Open your browser and navigate to:
```
http://localhost:8080/docs
```

This provides an interactive interface to test all endpoints with proper authentication headers.

### Using cURL

```bash
# Test health endpoint (no auth)
curl http://localhost:8080/health

# Test protected endpoint (no auth - should get 401)
curl http://localhost:8080/recipes

# Test with API key
curl -H "X-API-Key: test-key" http://localhost:8080/recipes

# Test with JWT (generate token first)
curl -H "Authorization: Bearer <your-jwt-token>" http://localhost:8080/recipes

# Test caching - second request should have X-Cache: HIT
curl -H "X-API-Key: test-key" http://localhost:8080/recipes -v
```

## Troubleshooting

**Connection refused**
- Verify FastAPI backend is running on configured FASTAPI_URL
- Check Redis is running on configured REDIS_URL

**401 Unauthorized**
- Verify API key or JWT token is correct
- Check X-API-Key or Authorization headers are properly formatted

**Cache not working**
- Verify CACHE_ENABLED is true
- Check Redis connection is working
- Review cache key generation logic

**Slow responses**
- Check FastAPI backend response time
- Verify Redis cache hit rate (check X-Cache headers)
- Consider increasing CACHE_TTL

## License

See LICENSE file in project root
