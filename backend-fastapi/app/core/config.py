from enum import Enum
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

class FetchType(Enum):
    GET = "GET"
    POST = "POST"

class URL(Enum):
    BY_FDCID = "/v1/food/{fdcId}"
    BY_FDCIDS = "/v1/foods"
    ALL_FOODS = "/v1/foods/list"
    SEARCH = "/v1/foods/search"
    

class Settings(BaseSettings):
    """Application configuration loaded from environment variables with multi-environment support."""

    # Environment
    ENVIRONMENT: str = "local"

    # Database (must be set via environment variable or .env file)
    DATABASE_URL: str

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Elasticsearch
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"

    # USDA FoodData Central API
    USDA_API_KEY: str = ""
    USDA_BASE_URLS: dict[URL, FetchType] = {
        URL.BY_FDCID: FetchType.GET,
        URL.BY_FDCIDS: FetchType.POST,
        URL.ALL_FOODS: FetchType.POST,
        URL.SEARCH: FetchType.POST
    }
    USDA_API_BASE_URL: str = "https://api.nal.usda.gov/fdc"

    # Application
    APP_NAME: str = "Keto Recipe API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=[
            str(Path(__file__).resolve().parents[3] / ".env"),
            str(Path(__file__).resolve().parents[3] / ".env.local"),
        ],
    )


settings = Settings()
