from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/steamanalytics"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Steam API
    STEAM_API_KEY: str = ""
    STEAM_API_BASE_URL: str = "https://api.steampowered.com"

    # Application
    APP_NAME: str = "Steam Analytics FastAPI"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
