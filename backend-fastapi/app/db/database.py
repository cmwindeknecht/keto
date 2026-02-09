from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self):
        self.engine = None
        self.async_session = None

    async def initialize(self):
        """Initialize the database engine and session factory."""
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,
            future=True,
            pool_pre_ping=True,
        )
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False, future=True
        )

    async def get_session(self) -> AsyncSession:
        """Get a new database session."""
        if self.async_session is None:
            await self.initialize()
        async with self.async_session() as session:
            yield session

    async def close(self):
        """Close the database connection pool."""
        if self.engine:
            await self.engine.dispose()


db_manager = DatabaseManager()


async def get_db() -> AsyncSession:
    """Dependency for getting a database session."""
    async for session in db_manager.get_session():
        yield session
