.PHONY: help up down restart build rebuild logs ps clean clean-all shell-fastapi shell-go shell-react db-shell redis-shell test lint format type-check security sonarqube

up: ## Start all services
	docker-compose down -v
	docker-compose up -d

restart-build: ## Build all services
	docker-compose down -v
	docker-compose build
	docker-compose up -d

restart-nocache: ## Restart all services
	docker-compose down -v
	docker-compose build --no-cache
	docker-compose up -d

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
	docker-compose exec postgres psql -U postgres -d keto

redis-shell: ## Open Redis CLI
	docker-compose exec redis redis-cli

db-migrate: ## Run database migrations
	docker-compose exec backend-fastapi alembic upgrade head

db-reset: ## Reset database (destroys all data)
	docker-compose down
	docker-compose up -d postgres

test-fastapi: ## Run FastAPI tests
	docker-compose exec backend-fastapi pytest

test-go: ## Run Go tests
	docker-compose exec backend-go go test ./...

test-react: ## Run React tests
	docker-compose exec frontend-react npm test

dev: up logs ## Start services and show logs

lint: ## Run all linting checks
	cd backend-fastapi && python -m pylint app/ || true
	cd backend-fastapi && python -m flake8 app/

format: ## Format code with black and isort
	cd backend-fastapi && python -m black app/ tests/
	cd backend-fastapi && python -m isort app/ tests/

type-check: ## Run type checking with mypy
	cd backend-fastapi && python -m mypy app/ || true

security: ## Run security checks with bandit
	cd backend-fastapi && python -m bandit -r app/

lint-fix: format ## Format and lint (alias)

sonarqube-logs: ## Show SonarQube logs
	docker-compose logs -f sonarqube

sonarqube-status: ## Check SonarQube health
	curl -s http://localhost:9000/api/system/health | jq .

sonarqube-scan: ## Run SonarQube analysis (requires sonar-scanner)
	cd backend-fastapi && \
	python -m pytest --cov=app --cov-report=xml && \
	python -m pylint app/ --exit-zero -f parseable > pylint-report.txt && \
	sonar-scanner -Dsonar.projectBaseDir=.
