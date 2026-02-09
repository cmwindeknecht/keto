.PHONY: help up down restart build rebuild logs ps clean clean-all shell-fastapi shell-go shell-react db-shell redis-shell test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

up: ## Start all services
	docker-compose up -d

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

build: ## Build all services
	docker-compose build

rebuild: ## Rebuild all services from scratch (no cache)
	docker-compose build --no-cache

logs: ## Show logs from all services (follow mode)
	docker-compose logs -f

logs-api: ## Show FastAPI logs
	docker-compose logs -f backend-fastapi

logs-go: ## Show Go Gateway logs
	docker-compose logs -f backend-go

logs-react: ## Show React logs
	docker-compose logs -f frontend-react

ps: ## Show running containers
	docker-compose ps

clean: ## Stop containers and remove volumes
	docker-compose down -v

clean-all: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

shell-fastapi: ## Open shell in FastAPI container
	docker-compose exec backend-fastapi /bin/bash

shell-go: ## Open shell in Go container
	docker-compose exec backend-go /bin/sh

shell-react: ## Open shell in React container
	docker-compose exec frontend-react /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d steamanalytics

redis-shell: ## Open Redis CLI
	docker-compose exec redis redis-cli

db-migrate: ## Run database migrations (example)
	docker-compose exec backend-fastapi alembic upgrade head

db-reset: ## Reset database (WARNING: destroys all data)
	docker-compose down postgres -v
	docker-compose up -d postgres

test-fastapi: ## Run FastAPI tests
	docker-compose exec backend-fastapi pytest

test-go: ## Run Go tests
	docker-compose exec backend-go go test ./...

test-react: ## Run React tests
	docker-compose exec frontend-react npm test

dev: up logs ## Start services and show logs
