## Services
- **FastAPI (Python)**: Port 8000, Steam API integration, ML analysis
- **Go API Gateway**: Port 8080, public API, rate limiting
- **React Frontend**: Port 3000, game search & analytics UI

## Data Stores
- Postgres (Supabase): Game data, reviews, prices
- Redis (localhost:6379): Caching
- Kafka (localhost:9092): Event streaming
- Elasticsearch (localhost:9200): Search

## API Flow
Frontend → Go Gateway → FastAPI → Postgres/Redis
FastAPI → Kafka → Flink → Postgres

## Key Directories
- `backend-fastapi/`: Python FastAPI service
- `backend-go/`: Go API gateway
- `frontend-react/`: React TypeScript UI
- `infrastructure/`: Terraform, K8s, Docker configs