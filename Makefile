.PHONY: env up restart-frontend prettier dev rebuild rebuild-nocache logs logs-api logs-go logs-react logs-sonarqube shell-fastapi shell-go shell-react db-shell redis-shell db-migrate db-reset test lint sonarqube-status sonarqube-scan pre-commit-install pre-commit-run requirements

up: ## Start all services (rebuilds Go gateway)
	docker-compose down
	docker-compose build backend-go
	docker-compose up -d

restart-frontend:
	docker-compose stop frontend-react
	docker-compose rm -f frontend-react
	docker-compose up -d frontend-react

prettier:
	cd frontend-react && npx prettier --write src/

dev: up logs ## Start services and show logs

rebuild: ## Build all services
	docker-compose down -v
	docker-compose build backend-go
	docker-compose build
	docker-compose up -d

rebuild-nocache: ## Restart all services
	docker-compose down -v
	docker-compose build backend-go
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

logs-sonarqube: ## Show SonarQube logs
	docker-compose logs -f sonarqube

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

db-reset: ## Reset database
	docker-compose down
	docker-compose up -d postgres

test:
	docker-compose exec backend-fastapi pytest
	# cd backend-go && go test ./... # TODO: add go test framework
	# docker-compose exec frontend-react npm test  # TODO: add frontend test framework

lint: ## Run all linting checks
	cd backend-fastapi && python -m black app/ tests/
	cd backend-fastapi && python -m isort app/ tests/
	cd backend-fastapi && python -m pylint app/ || true
	cd backend-fastapi && python -m flake8 app/
	cd backend-fastapi && python -m mypy app/ || true
	cd backend-fastapi && python -m bandit -r app/

sonarqube-status: ## Check SonarQube health
	curl -s http://localhost:9000/api/system/health | jq .

sonarqube-scan: ## Run SonarQube analysis (requires sonar-scanner)
	cd backend-fastapi && \
	python -m pytest --cov=app --cov-report=xml && \
	python -m pylint app/ --exit-zero -f parseable > pylint-report.txt && \
	sonar-scanner -Dsonar.projectBaseDir=.

pre-commit-install: ## Install pre-commit hooks
	python -c "import pre_commit.main; pre_commit.main.main(['install'])"

pre-commit-run: ## Run pre-commit checks on all files
	python -c "import pre_commit.main; pre_commit.main.main(['run', '--all-files'])"

requirements:
	python -m pip install -r backend-fastapi/requirements.txt
	python -m pip install -r backend-fastapi/requirements-dev.txt

env:
	source .venv/Scripts/activate
