"""Kafka producer for publishing ingredient events."""

import json
from typing import Optional
from aiokafka import AIOKafkaProducer
from pydantic import BaseModel
from app.services.kafka.models import IngredientCached

from app.core.config import settings


class KafkaProducerService:
    """Service for publishing events to Kafka."""

    INGREDIENT_INDEXED_TOPIC = "ingredient-indexed"

    def __init__(self):
        self.bootstrap_servers = settings.KAFKA_BOOTSTRAP_SERVERS
        self.producer: Optional[AIOKafkaProducer] = None

    async def start(self):
        """Start Kafka producer."""
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode()
            )
            await self.producer.start()
            print("Kafka producer started")

    async def stop(self):
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            print("Kafka producer stopped")

    async def publish(self, topic: str, event: BaseModel):
        """
        Publish an event to Kafka.

        Args:
            topic: Kafka topic name
            event: Pydantic model to publish
        """
        if not self.producer:
            await self.start()

        try:
            await self.producer.send(topic, value=event.model_dump())
            print(f"Published event to topic '{topic}' with data: {event.model_dump()}")
        except Exception as e:
            print(f"Error publishing to to topic '{topic}' with data: {event.model_dump()} due to exceptiopn {e}")
            raise

    async def publish_ingredient_cached(self, event: "IngredientCached"):  # noqa: F821
        """
        Publish an ingredient caching event.

        Args:
            event: IngredientCached event
        """
        await self.publish(self.INGREDIENT_INDEXED_TOPIC, event)


kafka_producer = KafkaProducerService()
