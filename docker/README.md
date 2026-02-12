# Docker Configuration

This directory contains all Dockerfiles for the Keto Recipe API.

## Dockerfiles

### [backend-fastapi.Dockerfile](backend-fastapi.Dockerfile)
Python FastAPI service for USDA API integration and recipe management.
- Base: `python:3.11-slim`
- Port: 8000
- Features: Hot reload enabled for development

### [backend-go.Dockerfile](backend-go.Dockerfile)
Go API Gateway for recipe API and rate limiting.
- Base: `golang:1.21-alpine` (builder) → `alpine:latest` (runtime)
- Port: 8080
- Features: Multi-stage build for minimal image size

### [frontend-react.Dockerfile](frontend-react.Dockerfile)
React TypeScript frontend for recipe builder and search.
- Base: `node:20-alpine`
- Port: 3000 (dev) / 80 (prod)
- Features: Multi-stage build with development and production targets

## Usage

### Development Mode (Default)
All services run with hot reload and volume mounts:

```bash
docker-compose up -d
```

### Production Build
To build production images:

```bash
# Build all services
docker-compose build

# Build specific service
docker-compose build backend-fastapi

# Build for production (React)
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### Rebuild After Changes
If you modify dependencies (requirements.txt, go.mod, package.json):

```bash
docker-compose up -d --build
```

## Health Checks

All application services include health checks:
- **FastAPI**: `GET /health` endpoint
- **Go Gateway**: `GET /health` endpoint
- **React**: HTTP check on port 3000

## Troubleshooting

### Service won't start
Check logs:
```bash
docker-compose logs -f [service-name]
```

### Clear everything and rebuild
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Check service health
```bash
docker-compose ps
```
