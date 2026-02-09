## Services
- **FastAPI (Python)**: Port 8000, USDA FoodData Central API integration, recipe management
- **Go API Gateway**: Port 8080, public API, rate limiting
- **React Frontend**: Port 3000, recipe building & nutrition tracking UI

## Data Stores
- Postgres (Supabase): Recipe data, ingredients, user recipes with nutrition info
- Redis (localhost:6379): Caching ingredient searches, recipe data, nutrition calculations
- Kafka (localhost:9092): Event streaming for recipe creation, updates, user interactions
- Elasticsearch (localhost:9200): Full-text search on recipes, ingredients, cuisine types

## API Flow
Frontend → Go Gateway → FastAPI → Postgres/Redis/Elasticsearch
FastAPI ↔ USDA FoodData Central API (ingredient lookups, nutrition data)
FastAPI → Kafka (event streaming of recipe events)

## Key Directories
- `backend-fastapi/`: Python FastAPI service (private API)
- `backend-go/`: Go API gateway (public API) - empty, ready for implementation
- `frontend-react/`: React TypeScript UI - empty, ready for implementation
- `.claude/`: Claude Code project documentation and guidelines