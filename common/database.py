from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import Column, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from common.config import settings

# Convert postgresql:// to postgresql+asyncpg://
DATABASE_URL = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()


class RawEvent(Base):
    """Raw events table"""

    __tablename__ = "raw_events"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    received_at = Column(DateTime, nullable=False, server_default=text("NOW()"))


class ProcessedEventDB(Base):
    """Processed events table"""

    __tablename__ = "processed_events"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(255), index=True)
    timestamp = Column(DateTime, nullable=False)
    properties = Column(JSONB)
    processed_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    status = Column(String(50), nullable=False, index=True)
    enriched_data = Column(JSONB)
    retry_count = Column(Integer, default=0)


class FailedEvent(Base):
    """Failed events (Dead Letter Queue)"""

    __tablename__ = "failed_events"

    id = Column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    event_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    error_message = Column(Text)
    failed_at = Column(DateTime, nullable=False, server_default=text("NOW()"))
    retry_count = Column(Integer, default=0)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health() -> bool:
    """Check database connectivity"""
    try:
        async with get_db() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
