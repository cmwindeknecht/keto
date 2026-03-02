.PHONY: help build run test clean setup dev-install

BINARY_NAME=keto-api
PORT=8080
FASTAPI_URL=http://localhost:8000
REDIS_URL=redis:6379

help:
	@echo "Keto API Gateway - Available commands:"
	@echo ""
	@echo "  make setup         - Install dependencies"
	@echo "  make build         - Build the binary"
	@echo "  make run           - Run the gateway"
	@echo "  make dev           - Run with hot reload (requires air)"
	@echo "  make clean         - Clean build artifacts"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linter"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-run    - Run Docker container"
	@echo ""

setup:
	go mod download
	go mod verify

build: clean
	mkdir -p bin
	GOOS=linux GOARCH=amd64 CGO_ENABLED=0 go build -o bin/${BINARY_NAME} ./cmd/server
	@echo "Build complete: bin/${BINARY_NAME}"

run: build
	PORT=${PORT} FASTAPI_URL=${FASTAPI_URL} REDIS_URL=${REDIS_URL} \
	./bin/${BINARY_NAME}

dev: setup
	@command -v air >/dev/null 2>&1 || { echo "Installing air for hot reload..."; go install github.com/air-verse/air@latest; }
	air

test:
	go test -v ./...

lint:
	@command -v golangci-lint >/dev/null 2>&1 || { echo "Installing golangci-lint..."; go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest; }
	golangci-lint run ./...

clean:
	rm -rf bin/
	go clean

docker-build:
	docker build -f ../docker/backend-go.Dockerfile -t keto-api-gateway:latest .

docker-run: docker-build
	docker run -p 8080:8080 \
		-e PORT=${PORT} \
		-e FASTAPI_URL=${FASTAPI_URL} \
		-e REDIS_URL=${REDIS_URL} \
		-e API_KEYS=test-key,dev-key \
		-e DEBUG=true \
		keto-api-gateway:latest

# Development setup - install dev tools
dev-install:
	go install github.com/air-verse/air@latest
	go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
	go install gotest.tools/gotestsum@latest
	@echo "Development tools installed!"
