"""Unit tests for cache service."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.cache.cache_service import CacheService


@pytest.fixture
def cache_service():
    """Create cache service instance."""
    return CacheService()


@pytest.mark.asyncio
async def test_cache_service_connect(cache_service):
    """Test connecting to Redis."""
    with patch("app.services.cache.cache_service.redis.from_url", new_callable=AsyncMock) as mock_redis:
        mock_redis.return_value = MagicMock()
        await cache_service.connect()
        assert cache_service._redis_client is not None
        mock_redis.assert_called_once()


@pytest.mark.asyncio
async def test_cache_service_disconnect(cache_service):
    """Test disconnecting from Redis."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis

    await cache_service.disconnect()

    mock_redis.close.assert_called_once()
    assert cache_service._redis_client is None


@pytest.mark.asyncio
async def test_get_ingredient_key(cache_service):
    """Test generating cache key."""
    key = cache_service._get_ingredient_key(12345)
    assert key == "ingredient:12345"


@pytest.mark.asyncio
async def test_set_ingredient_success(cache_service):
    """Test caching ingredient successfully."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis

    from app.services.cache.models import CachedIngredient

    ingredient = CachedIngredient(fdc_id=12345, description="Test Ingredient", data_type="Foundation", nutrients={})

    result = await cache_service.set_ingredient(ingredient)

    assert result is True
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_set_ingredient_failure(cache_service):
    """Test cache service handles exceptions."""
    mock_redis = AsyncMock()
    mock_redis.setex.side_effect = Exception("Redis error")
    cache_service._redis_client = mock_redis

    from app.services.cache.models import CachedIngredient

    ingredient = CachedIngredient(fdc_id=12345, description="Test", data_type="Foundation", nutrients={})

    result = await cache_service.set_ingredient(ingredient)
    assert result is False


@pytest.mark.asyncio
async def test_get_ingredient_found(cache_service):
    """Test retrieving cached ingredient."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis

    from app.services.cache.models import CachedIngredient

    ingredient = CachedIngredient(fdc_id=12345, description="Test", data_type="Foundation", nutrients={})

    mock_redis.get.return_value = ingredient.model_dump_json()

    result = await cache_service.get_ingredient(12345)

    assert result is not None
    assert result.fdc_id == 12345


@pytest.mark.asyncio
async def test_get_ingredient_not_found(cache_service):
    """Test cache miss."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis
    mock_redis.get.return_value = None

    result = await cache_service.get_ingredient(12345)

    assert result is None


@pytest.mark.asyncio
async def test_clear_all_ingredients(cache_service):
    """Test clearing all cached ingredients."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis
    mock_redis.keys.return_value = ["ingredient:1", "ingredient:2"]
    mock_redis.delete.return_value = 2

    result = await cache_service.clear_all_ingredients()

    assert result == 2
    mock_redis.delete.assert_called_once()


@pytest.mark.asyncio
async def test_clear_all_ingredients_empty(cache_service):
    """Test clearing when cache is empty."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis
    mock_redis.keys.return_value = []

    result = await cache_service.clear_all_ingredients()

    assert result == 0


@pytest.mark.asyncio
async def test_get_cache_info(cache_service):
    """Test getting cache statistics."""
    mock_redis = AsyncMock()
    cache_service._redis_client = mock_redis
    mock_redis.info.return_value = {
        "used_memory_human": "1M",
        "total_commands_processed": 100,
    }

    result = await cache_service.get_cache_info()

    assert result["connected"] is True
    assert result["used_memory"] == "1M"
    assert result["total_commands"] == 100
