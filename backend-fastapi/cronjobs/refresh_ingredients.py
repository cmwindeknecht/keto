"""Cronjob to refresh branded ingredients approaching TTL expiration."""

import asyncio
from datetime import datetime

from sqlalchemy import text

from app.db.database import db_manager
from app.services.cache.cache_service import cache_service
from app.services.elasticsearch.es_service import elasticsearch_service
from app.services.usda.usda_service import usda_service


async def refresh_branded_ingredients():
    """
    Refresh branded ingredients with TTL < 5 days.

    Runs daily (typically at 2am) to:
    1. Find all branded ingredients used in recipes
    2. Check their Redis TTL
    3. Refresh any nearing expiration (< 5 days)
    4. Re-fetch from USDA
    5. Update Redis cache and Elasticsearch index

    This ensures popular ingredients stay fresh and don't cause cache misses
    on recipe lookups.
    """
    print(f"Starting ingredient refresh cronjob at {datetime.utcnow()}")

    try:
        await cache_service.connect()
        await elasticsearch_service.connect()

        # Get all FDC IDs used in recipes
        async for db in db_manager.get_session():
            query = text("SELECT DISTINCT usda_fdc_id FROM recipe_ingredients WHERE usda_fdc_id IS NOT NULL")
            result = await db.execute(query)
            fdc_ids = [row[0] for row in result]

        print(f"Checking {len(fdc_ids)} ingredients for refresh...")

        refreshed_count = 0
        assert cache_service._redis_client is not None
        for fdc_id in fdc_ids:
            try:
                # Check TTL
                ttl = await cache_service._redis_client.ttl(f"ingredient:{fdc_id}")

                # TTL is in seconds. Refresh if:
                # - ttl exists (> 0) and is less than 5 days (432000 seconds)
                if ttl and 0 < ttl < 5 * 86400:
                    print(f"Refreshing ingredient {fdc_id} (TTL: {ttl}s remaining)")

                    # Re-fetch from USDA
                    usda_data = await usda_service._fetch_from_usda(fdc_id)

                    # Update Redis
                    await cache_service.set_ingredient(usda_data)

                    # Update Elasticsearch
                    await elasticsearch_service.index_ingredient(usda_data)

                    refreshed_count += 1

            except Exception as e:
                print(f"✗ Error refreshing ingredient {fdc_id}: {e}")
                continue

        print(f"✓ Refreshed {refreshed_count} ingredients")

    except Exception as e:
        print(f"✗ Cronjob failed: {e}")
    finally:
        await cache_service.disconnect()
        await elasticsearch_service.disconnect()
        print(f"Cronjob completed at {datetime.utcnow()}")


if __name__ == "__main__":
    asyncio.run(refresh_branded_ingredients())
