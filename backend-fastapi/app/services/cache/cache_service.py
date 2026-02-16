"""Service for managing Redis cache operations."""

import json
import logging
from typing import Optional
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Service for caching ingredient data in Redis.

    Storage format:
    - Key: "ingredient:{fdc_id}" (e.g., "ingredient:534358")
    - Value: JSON-serialized CachedIngredient object
    - TTL: 30 days (auto-expires after 30 days)

    setex() is atomic - if key exists, it overwrites (no duplicate risk).
    """
    TTL_STRATEGY = {
      "Foundation": None,        # Permanent
      "SR Legacy": None,         # Permanent
      "Survey (FNDDS)": 180 * 86400,  # 180 days
      "Branded": 30 * 86400,     # 30 days
    }

    # Cache configuration
    INGREDIENT_TTL = 30 * 24 * 60 * 60  # 30 days in seconds
    INGREDIENT_KEY_PREFIX = "ingredient"

    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self._redis_client: Optional[redis.Redis] = None
        logger.debug(f"CacheService initialized with Redis URL: {self.redis_url}")

    async def connect(self):
        """Initialize Redis connection."""
        if not self._redis_client:
            self._redis_client = await redis.from_url(self.redis_url, decode_responses=True)
            logger.debug("Connected to Redis")

    async def disconnect(self):
        """Close Redis connection."""
        if self._redis_client:
            await self._redis_client.close()
            self._redis_client = None
            logger.debug("Disconnected from Redis")

    def _get_ingredient_key(self, fdc_id: int) -> str:
        """Generate cache key for an ingredient."""
        ingredient_key = f"{self.INGREDIENT_KEY_PREFIX}:{fdc_id}"
        logger.debug(f"Generated cache key for fdc_id {fdc_id}: {ingredient_key}")
        return ingredient_key

    async def get_ingredient(self, fdc_id: int) -> Optional[dict]:
        """
        Retrieve cached ingredient data.

        Args:
        - fdc_id: USDA FoodData Central ID

        @Returns: Optional[dict] if found in cache, None otherwise
        """
        if not self._redis_client:
            await self.connect()

        key = self._get_ingredient_key(fdc_id)
        data = await self._redis_client.get(key)

        if data:
            logger.info(f"Retrieved data for key {key}: {data}")  
            return json.loads(data)
        
        logger.info(f"No data found for key {key}")
        return None

    async def set_ingredient(self, ingredient: dict) -> None:
        """
        Cache ingredient data with 30-day TTL.

        Atomic operation - if key exists, overwrites it. No duplicates.

        Args:
            ingredient: CachedIngredient to store

        Returns:
            True if cached successfully
        """
        if not self._redis_client:
            await self.connect()

        fdc_id = ingredient['fdcId']
        key = self._get_ingredient_key(fdc_id)
        ttl = self.TTL_STRATEGY.get(ingredient.get('dataType'), 30 * 86400)

        logger.info(f"Caching ingredient {fdc_id} --- ({ingredient})")

        try:
            if ttl:
                logger.info(f"Setting ingredient with key {key} and TTL {ttl} seconds")
                await self._redis_client.setex(key, ttl, json.dumps(ingredient))
            else:
                logger.info(f"Setting ingredient with key {key} with no TTL (permanent)")
                await self._redis_client.set(key, json.dumps(ingredient))
        except Exception as e:
            logger.error(f"Error caching ingredient {fdc_id}: {e}")

    async def clear_all_ingredients(self) -> int:
        """
        Clear all cached ingredients (useful for testing/reset).

        Returns:
            Number of keys deleted
        """
        if not self._redis_client:
            await self.connect()

        pattern = f"{self.INGREDIENT_KEY_PREFIX}:*"
        keys = await self._redis_client.keys(pattern)

        if keys:
            logger.info(f"Clearing {len(keys)} cached ingredients")
            return await self._redis_client.delete(*keys)
        return 0

    async def get_cache_info(self) -> dict:
        """Get Redis cache statistics."""
        if not self._redis_client:
            await self.connect()

        info = await self._redis_client.info()
        return {
            "connected": True,
            "used_memory": info.get("used_memory_human"),
            "total_commands": info.get("total_commands_processed"),
        }


cache_service = CacheService()
