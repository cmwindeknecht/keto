"""Shared test fixtures and configuration."""

import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.database import get_db
from app.db.models import Base
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_engine):
    """Create a test database session."""
    AsyncSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
def test_client(event_loop):
    """Create a test client with mocked database."""
    # Create test session for this client
    AsyncSessionLocal = async_sessionmaker(
        create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        ),
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def create_tables():
        engine = AsyncSessionLocal.kw["bind"]
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    event_loop.run_until_complete(create_tables())

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

    # Cleanup engine
    async def cleanup():
        engine = AsyncSessionLocal.kw["bind"]
        await engine.dispose()

    event_loop.run_until_complete(cleanup())


@pytest.fixture
def mock_usda_api():
    """Mock USDA API responses."""
    return {
        "search_result": {
            "fdcId": 2346407,
            "dataType": "Foundation",
            "description": "Cabbage, green, raw",
            "foodNutrients": [
                {
                    "nutrientId": 1003,
                    "nutrientNumber": "203",
                    "nutrientName": "Protein",
                    "value": 0.961,
                    "unitName": "G",
                    "derivationCode": "NC",
                    "derivationDescription": "Calculated",
                },
                {
                    "nutrientId": 1004,
                    "nutrientNumber": "204",
                    "nutrientName": "Total lipid (fat)",
                    "value": 0.228,
                    "unitName": "G",
                    "derivationCode": "A",
                    "derivationDescription": "Analytical",
                },
                {
                    "nutrientId": 1005,
                    "nutrientNumber": "205",
                    "nutrientName": "Carbohydrate, by difference",
                    "value": 6.38,
                    "unitName": "G",
                    "derivationCode": "NC",
                    "derivationDescription": "Calculated",
                },
            ],
            "publicationDate": None,
            "brandOwner": None,
            "gtinUpc": None,
            "ingredients": None,
            "ndbNumber": 11109,
            "score": 675.59,
        },
        "multiple_results": [
            {
                "fdcId": 2346407,
                "dataType": "Foundation",
                "description": "Cabbage, green, raw",
                "foodNutrients": [
                    {"nutrientId": 1003, "nutrientName": "Protein", "value": 0.961, "unitName": "G"},
                ],
            },
            {
                "fdcId": 2346408,
                "dataType": "Foundation",
                "description": "Cabbage, red, raw",
                "foodNutrients": [
                    {"nutrientId": 1003, "nutrientName": "Protein", "value": 1.0, "unitName": "G"},
                ],
            },
        ],
    }


@pytest.fixture
def mock_cache_service():
    """Mock cache service."""
    cache_mock = AsyncMock()
    cache_mock.get_ingredient = AsyncMock(return_value=None)
    cache_mock.set_ingredient = AsyncMock(return_value=True)
    cache_mock.clear_all_ingredients = AsyncMock(return_value=0)
    return cache_mock


@pytest.fixture
def mock_elasticsearch_service():
    """Mock Elasticsearch service."""
    es_mock = AsyncMock()
    es_mock.search_foods = AsyncMock(return_value=[])
    es_mock.index_food = AsyncMock(return_value=True)
    return es_mock


@pytest.fixture
def mock_kafka_producer():
    """Mock Kafka producer."""
    kafka_mock = AsyncMock()
    kafka_mock.publish = AsyncMock(return_value=True)
    return kafka_mock
