# Docker Setup Guide

Complete Docker configuration for the Steam Analytics platform.

## Quick Start

1. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your STEAM_API_KEY
   ```

2. **Start all services**
   ```bash
   docker-compose up -d
   # Or use Make: make up
   ```

3. **Check service status**
   ```bash
   docker-compose ps
   # Or use Make: make ps
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   # Or use Make: make logs
   ```

## Architecture

### Application Services
- **FastAPI Backend** → [localhost:8000](http://localhost:8000)
  - Steam API integration
  - ML analysis
  - Postgres, Redis, Kafka, Elasticsearch integration

- **Go API Gateway** → [localhost:8080](http://localhost:8080)
  - Public API
  - Rate limiting
  - Proxies to FastAPI

- **React Frontend** → [localhost:3000](http://localhost:3000)
  - Game search & analytics UI
  - Connects to Go Gateway

### Infrastructure Services
- **Postgres** → localhost:5432
  - Game data, reviews, prices
  - Auto-initialized with schema

- **Redis** → localhost:6379
  - Caching layer

- **Kafka** → localhost:9092
  - Event streaming
  - With Zookeeper on port 2181

- **Elasticsearch** → localhost:9200
  - Search engine

- **Flink** → localhost:8081 (UI)
  - Stream processing (JobManager + TaskManager)

## Common Commands

### Using Make (Recommended)
```bash
make help           # Show all available commands
make up             # Start all services
make down           # Stop all services
make logs           # View logs
make logs-api       # View FastAPI logs
make ps             # Show container status
make build          # Build all services
make rebuild        # Rebuild from scratch
make clean          # Remove volumes and stop
make db-shell       # Open database shell
make redis-shell    # Open Redis CLI
make test-fastapi   # Run Python tests
```

### Using Docker Compose Directly
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild specific service
docker-compose up -d --build backend-fastapi

# Execute command in container
docker-compose exec backend-fastapi bash
```

## Development Workflow

### Hot Reload
All application services support hot reload:
- **FastAPI**: Code changes auto-reload via uvicorn
- **Go**: Requires rebuild (`docker-compose up -d --build backend-go`)
- **React**: Hot module replacement enabled

### Local Overrides
Create `docker-compose.override.yml` for local customizations:
```bash
cp docker-compose.override.yml.example docker-compose.override.yml
# Edit as needed
```

### Debugging

**FastAPI**
```bash
# View logs
make logs-api

# Shell access
make shell-fastapi

# Run tests
docker-compose exec backend-fastapi pytest -v
```

**Go Gateway**
```bash
# View logs
make logs-go

# Shell access
make shell-go

# Run tests
docker-compose exec backend-go go test -v ./...
```

**React**
```bash
# View logs
make logs-react

# Shell access
make shell-react

# Run tests
docker-compose exec frontend-react npm test
```

## Database

### Access Database
```bash
make db-shell
# Or manually:
docker-compose exec postgres psql -U postgres -d steamanalytics
```

### Run Migrations
```bash
# Assuming you're using Alembic for FastAPI
docker-compose exec backend-fastapi alembic upgrade head
```

### Reset Database
```bash
make db-reset  # WARNING: Destroys all data
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs [service-name]

# Verify environment variables
cat .env

# Ensure ports aren't in use
netstat -an | findstr "8000 8080 3000 5432 6379 9092 9200"
```

### Port conflicts
Edit `docker-compose.override.yml`:
```yaml
services:
  postgres:
    ports:
      - "5433:5432"  # Use alternate port
```

### Rebuild from scratch
```bash
make clean-all
make build
make up
```

### Clear Docker cache
```bash
docker system prune -a --volumes
# WARNING: Removes all unused Docker data
```

## Production Considerations

For production deployment:

1. **Use production Dockerfiles** (multi-stage builds)
2. **Set production environment variables**
3. **Use secrets management** (not .env files)
4. **Configure proper networking** (not bridge mode)
5. **Add resource limits**
6. **Enable logging drivers**
7. **Use orchestration** (Kubernetes, as per infrastructure/k8s/)

## File Structure

```
.
├── docker/
│   ├── backend-fastapi.Dockerfile   # FastAPI Dockerfile
│   ├── backend-go.Dockerfile        # Go Dockerfile
│   ├── frontend-react.Dockerfile    # React Dockerfile
│   └── README.md                     # Docker docs
├── docker-compose.yml                # Main compose config
├── docker-compose.override.yml       # Local overrides (gitignored)
├── .dockerignore                     # Docker ignore rules
├── .env.example                      # Environment template
├── .env                              # Your environment (gitignored)
└── Makefile                          # Convenience commands
```

## Health Checks

All services include health checks. Check status:
```bash
docker-compose ps
```

Healthy services show `healthy` status.

## Next Steps

1. ✅ Set up environment variables
2. ✅ Start services with `make up`
3. 🔲 Create application code in service directories
4. 🔲 Add requirements.txt / go.mod / package.json
5. 🔲 Implement API endpoints
6. 🔲 Add tests
7. 🔲 Configure CI/CD pipeline
