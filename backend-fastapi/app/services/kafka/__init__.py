"""Kafka event streaming service for ingredient indexing."""

from .producer import kafka_producer

__all__ = ["kafka_producer"]
