from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

Base = declarative_base()


class DatabaseManager:
    """Manages database connections and sessions."""

    @property
    def engine(self) -> AsyncEngine | None:
        return self._engine
    
    @property
    def async_session(self) -> sessionmaker | None:
        return self._async_session
    
    def __init__(self):
        self._engine: AsyncEngine | None = None
        self._async_session: sessionmaker | None = None

    async def initialize(self):
        """
        Initialize the database engine and session factory.
        echo=settings.DEBUG --- When True, logs all SQL statements to stdout. Super useful for debugging locally.
        future=True	--- Enables SQLAlchemy 2.0 style API (more async/await friendly than 1.4 style).
        pool_pre_ping=True --- Sends a test query before using a connection from the pool. Prevents "connection closed" errors if a connection went stale.
        expire_on_commit=False --- disable SQLAlchemy from clearing object state after commits
        """
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
