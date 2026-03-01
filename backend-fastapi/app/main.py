import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.database import db_manager
from app.middleware.inbound_rate_limiter import InboundRateLimiterMiddleware
from app.middleware.logging import LoggingMiddleware
from app.routes.internal import recipes as internal_recipes_routes
from app.routes.internal import usda as internal_usda_routes
from app.services.cache.cache_service import cache_service
from app.services.elasticsearch.es_service import elasticsearch_service
from app.services.kafka.producer import kafka_producer

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Suppress verbose library logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("aiokafka").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Manage application lifecycle (startup/shutdown)."""
    # Startup
    db_manager.initialize()
    await cache_service.connect()
    await elasticsearch_service.initialize()
    await kafka_producer.start()
    yield
    # Shutdown
    await kafka_producer.stop()
    await elasticsearch_service.disconnect()
    await cache_service.disconnect()
    await db_manager.close()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Keto Recipe API with nutrition tracking and recipe building",
    lifespan=lifespan,
)

app.add_middleware(LoggingMiddleware)
app.add_middleware(InboundRateLimiterMiddleware)

# Include routers
app.include_router(internal_recipes_routes.router)
app.include_router(internal_usda_routes.router)


@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "keto-recipe-api"}


@app.get("/", tags=["info"])
async def root() -> dict[str, str]:
    """Root endpoint with service information."""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # nosec B104 - internal service behind Go gateway
        port=8000,
        reload=settings.DEBUG,
    )
