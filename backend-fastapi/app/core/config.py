from pathlib import Path

from pydantic_settings import BaseSettings, DotEnvSettingsSource


class Settings(BaseSettings):
    """Application configuration loaded from environment variables with multi-environment support."""

    # Environment
    ENVIRONMENT: str = "local"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/steamanalytics"

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
        case_sensitive = True

        @classmethod
        def settings_customise_sources(
            cls,
            settings_cls,
            init_settings,
            env_settings,
            dotenv_settings,
            file_settings,
        ):
            """
            Load settings from multiple .env files based on ENVIRONMENT variable.

            Priority order (highest to lowest):
            1. init_settings (direct instantiation)
            2. environment variables
            3. .env.{environment} file
            4. .env.local file
            5. .env file
            """
            import os

            env = os.getenv("ENVIRONMENT", "local")
            base_path = Path(__file__).parent.parent.parent

            env_files = [
                base_path / ".env",
                base_path / ".env.local",
                base_path / f".env.{env}",
            ]

            dotenv_sources = [
                DotEnvSettingsSource(settings_cls, env_file=str(f)) for f in env_files if f.exists()
            ]

            return (
                init_settings,
                env_settings,
                *dotenv_sources,
                file_settings,
            )


settings = Settings()
