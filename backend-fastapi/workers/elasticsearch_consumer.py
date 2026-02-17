"""Kafka consumer worker that indexes ingredients in Elasticsearch."""

import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from app.core.config import settings
from app.services.elasticsearch.es_service import elasticsearch_service
from app.services.kafka.models import IngredientCached

logger = logging.getLogger(__name__)


async def consume_ingredient_events():
    """
    Consume ingredient caching events from Kafka and index them in Elasticsearch.

    Runs continuously, listening for IngredientCached events published when
    ingredients are cached in Redis. Indexes each ingredient in Elasticsearch
    for fuzzy search.
    """
    consumer = AIOKafkaConsumer(
        "ingredient-indexed",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode()),
        group_id="elasticsearch-indexer",
        auto_offset_reset="earliest",
    )

    await consumer.start()
    logger.info("Elasticsearch consumer started")

    try:
        async for message in consumer:
            try:
                # Parse the event
                event_data = message.value
                event = IngredientCached(**event_data)

                logger.debug(f"Indexing ingredient {event.fdc_id} in Elasticsearch")

                # Index the ingredient
                await elasticsearch_service.index_ingredient(event.data)
                logger.debug(f"Successfully indexed ingredient {event.fdc_id}")

            except Exception as e:
                logger.warning(f"Failed to process event: {e}")
                # Continue processing next message instead of crashing

    except asyncio.CancelledError:
        logger.error("Elasticsearch consumer cancelled, shutting down...")
        raise
    finally:
        await consumer.stop()
        logger.info("Elasticsearch consumer stopped")


if __name__ == "__main__":
    asyncio.run(consume_ingredient_events())
