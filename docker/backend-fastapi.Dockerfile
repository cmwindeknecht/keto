FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend-fastapi/requirements.txt .
COPY backend-fastapi/requirements-dev.txt* .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install dev dependencies if BUILD_ENV=dev (for local development with pre-commit hooks and type checking)
ARG BUILD_ENV=prod
RUN if [ "$BUILD_ENV" = "dev" ] && [ -f requirements-dev.txt ]; then \
    pip install --no-cache-dir -r requirements-dev.txt; \
    fi

# Copy application code
COPY backend-fastapi/ .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
