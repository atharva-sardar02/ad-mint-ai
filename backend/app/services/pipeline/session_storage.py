"""
Session Storage Adapters for Interactive Pipeline

Provides flexible session persistence with multiple backend options:
- Redis (preferred - fast in-memory storage with TTL support)
- PostgreSQL (fallback - database-backed persistence)
- In-Memory (development only - not production-safe)

Usage:
    storage = get_session_storage()
    await storage.save(session)
    session = await storage.load(session_id)
    await storage.delete(session_id)
"""

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings
from app.schemas.interactive import PipelineSessionState

logger = logging.getLogger(__name__)


# ============================================================================
# Abstract Base Class
# ============================================================================

class SessionStorage(ABC):
    """Abstract base class for session storage backends."""

    @abstractmethod
    async def save(self, session: PipelineSessionState) -> None:
        """Save session to storage."""
        pass

    @abstractmethod
    async def load(self, session_id: str) -> Optional[PipelineSessionState]:
        """Load session from storage. Returns None if not found."""
        pass

    @abstractmethod
    async def delete(self, session_id: str) -> None:
        """Delete session from storage."""
        pass

    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Check if session exists in storage."""
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired sessions. Returns number of sessions deleted."""
        pass


# ============================================================================
# Redis Storage Adapter
# ============================================================================

class RedisSessionStorage(SessionStorage):
    """Redis-based session storage (preferred)."""

    def __init__(self, redis_url: str = None, key_prefix: str = "pipeline:session:"):
        """
        Initialize Redis storage.

        Args:
            redis_url: Redis connection URL (default: from settings)
            key_prefix: Key prefix for all sessions
        """
        try:
            import redis.asyncio as redis
            self.redis_available = True
        except ImportError:
            self.redis_available = False
            logger.warning("redis package not installed - Redis storage unavailable")
            return

        self.redis_url = redis_url or getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
        self.key_prefix = key_prefix
        self.redis = None

    async def _get_client(self):
        """Get or create Redis client."""
        if not self.redis_available:
            raise RuntimeError("Redis not available")

        if self.redis is None:
            import redis.asyncio as redis
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self.redis

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session."""
        return f"{self.key_prefix}{session_id}"

    async def save(self, session: PipelineSessionState) -> None:
        """Save session to Redis with TTL."""
        client = await self._get_client()

        # Serialize session to JSON
        session_data = session.model_dump_json()
        key = self._make_key(session.session_id)

        # Calculate TTL from expires_at
        if session.expires_at:
            ttl_seconds = int((session.expires_at - datetime.utcnow()).total_seconds())
            ttl_seconds = max(ttl_seconds, 60)  # Min 60 seconds TTL
        else:
            ttl_seconds = 3600  # Default 1 hour

        # Store with TTL
        await client.setex(key, ttl_seconds, session_data)
        logger.debug(f"Session saved to Redis: {session.session_id} (TTL: {ttl_seconds}s)")

    async def load(self, session_id: str) -> Optional[PipelineSessionState]:
        """Load session from Redis."""
        client = await self._get_client()
        key = self._make_key(session_id)

        data = await client.get(key)
        if data is None:
            logger.debug(f"Session not found in Redis: {session_id}")
            return None

        # Deserialize from JSON
        session = PipelineSessionState.model_validate_json(data)
        logger.debug(f"Session loaded from Redis: {session_id}")
        return session

    async def delete(self, session_id: str) -> None:
        """Delete session from Redis."""
        client = await self._get_client()
        key = self._make_key(session_id)

        deleted = await client.delete(key)
        if deleted:
            logger.debug(f"Session deleted from Redis: {session_id}")

    async def exists(self, session_id: str) -> bool:
        """Check if session exists in Redis."""
        client = await self._get_client()
        key = self._make_key(session_id)
        return await client.exists(key) > 0

    async def cleanup_expired(self) -> int:
        """Redis handles expiration automatically via TTL. Returns 0."""
        logger.debug("Redis auto-expires sessions - no manual cleanup needed")
        return 0


# ============================================================================
# PostgreSQL Storage Adapter
# ============================================================================

class PostgreSQLSessionStorage(SessionStorage):
    """PostgreSQL-based session storage (fallback)."""

    def __init__(self, table_name: str = "pipeline_sessions"):
        """
        Initialize PostgreSQL storage.

        Args:
            table_name: Table name for sessions
        """
        from sqlalchemy import create_engine, Table, Column, String, Text, DateTime, MetaData
        from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
        from sqlalchemy.orm import sessionmaker

        self.table_name = table_name

        # Convert sync DATABASE_URL to async if needed
        db_url = settings.DATABASE_URL
        if db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

        self.engine = create_async_engine(db_url, echo=settings.DEBUG)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Define table schema
        self.metadata = MetaData()
        self.sessions_table = Table(
            table_name,
            self.metadata,
            Column("session_id", String(50), primary_key=True),
            Column("data", Text, nullable=False),
            Column("expires_at", DateTime, nullable=False),
            Column("created_at", DateTime, default=datetime.utcnow),
            Column("updated_at", DateTime, default=datetime.utcnow, onupdate=datetime.utcnow),
        )

    async def _ensure_table(self):
        """Create table if it doesn't exist."""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.metadata.create_all)

    async def save(self, session: PipelineSessionState) -> None:
        """Save session to PostgreSQL."""
        from sqlalchemy import insert, update
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        await self._ensure_table()

        session_data = session.model_dump_json()
        expires_at = session.expires_at or datetime.utcnow() + timedelta(hours=1)

        async with self.async_session() as db:
            # Use upsert (INSERT ... ON CONFLICT UPDATE)
            stmt = pg_insert(self.sessions_table).values(
                session_id=session.session_id,
                data=session_data,
                expires_at=expires_at,
                updated_at=datetime.utcnow()
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["session_id"],
                set_={"data": session_data, "expires_at": expires_at, "updated_at": datetime.utcnow()}
            )

            await db.execute(stmt)
            await db.commit()

        logger.debug(f"Session saved to PostgreSQL: {session.session_id}")

    async def load(self, session_id: str) -> Optional[PipelineSessionState]:
        """Load session from PostgreSQL."""
        from sqlalchemy import select

        await self._ensure_table()

        async with self.async_session() as db:
            stmt = select(self.sessions_table).where(
                self.sessions_table.c.session_id == session_id
            )
            result = await db.execute(stmt)
            row = result.first()

            if row is None:
                logger.debug(f"Session not found in PostgreSQL: {session_id}")
                return None

            # Check if expired
            if row.expires_at < datetime.utcnow():
                logger.debug(f"Session expired: {session_id}")
                await self.delete(session_id)
                return None

            # Deserialize from JSON
            session = PipelineSessionState.model_validate_json(row.data)
            logger.debug(f"Session loaded from PostgreSQL: {session_id}")
            return session

    async def delete(self, session_id: str) -> None:
        """Delete session from PostgreSQL."""
        from sqlalchemy import delete

        await self._ensure_table()

        async with self.async_session() as db:
            stmt = delete(self.sessions_table).where(
                self.sessions_table.c.session_id == session_id
            )
            await db.execute(stmt)
            await db.commit()

        logger.debug(f"Session deleted from PostgreSQL: {session_id}")

    async def exists(self, session_id: str) -> bool:
        """Check if session exists in PostgreSQL."""
        from sqlalchemy import select, func

        await self._ensure_table()

        async with self.async_session() as db:
            stmt = select(func.count()).select_from(self.sessions_table).where(
                self.sessions_table.c.session_id == session_id,
                self.sessions_table.c.expires_at > datetime.utcnow()
            )
            result = await db.execute(stmt)
            count = result.scalar()
            return count > 0

    async def cleanup_expired(self) -> int:
        """Delete all expired sessions from PostgreSQL."""
        from sqlalchemy import delete

        await self._ensure_table()

        async with self.async_session() as db:
            stmt = delete(self.sessions_table).where(
                self.sessions_table.c.expires_at < datetime.utcnow()
            )
            result = await db.execute(stmt)
            await db.commit()
            deleted_count = result.rowcount

        logger.info(f"Cleaned up {deleted_count} expired sessions from PostgreSQL")
        return deleted_count


# ============================================================================
# In-Memory Storage Adapter (Development Only)
# ============================================================================

class InMemorySessionStorage(SessionStorage):
    """In-memory session storage (development only - not production-safe)."""

    def __init__(self):
        """Initialize in-memory storage."""
        self._store = {}
        logger.warning("Using in-memory session storage - NOT PRODUCTION SAFE")

    async def save(self, session: PipelineSessionState) -> None:
        """Save session to memory."""
        self._store[session.session_id] = session
        logger.debug(f"Session saved to memory: {session.session_id}")

    async def load(self, session_id: str) -> Optional[PipelineSessionState]:
        """Load session from memory."""
        session = self._store.get(session_id)

        if session is None:
            logger.debug(f"Session not found in memory: {session_id}")
            return None

        # Check if expired
        if session.expires_at and session.expires_at < datetime.utcnow():
            logger.debug(f"Session expired: {session_id}")
            await self.delete(session_id)
            return None

        logger.debug(f"Session loaded from memory: {session_id}")
        return session

    async def delete(self, session_id: str) -> None:
        """Delete session from memory."""
        if session_id in self._store:
            del self._store[session_id]
            logger.debug(f"Session deleted from memory: {session_id}")

    async def exists(self, session_id: str) -> bool:
        """Check if session exists in memory."""
        session = self._store.get(session_id)
        if session is None:
            return False

        # Check if expired
        if session.expires_at and session.expires_at < datetime.utcnow():
            return False

        return True

    async def cleanup_expired(self) -> int:
        """Delete all expired sessions from memory."""
        now = datetime.utcnow()
        expired_ids = [
            sid for sid, session in self._store.items()
            if session.expires_at and session.expires_at < now
        ]

        for sid in expired_ids:
            del self._store[sid]

        logger.info(f"Cleaned up {len(expired_ids)} expired sessions from memory")
        return len(expired_ids)


# ============================================================================
# Storage Factory
# ============================================================================

_storage_instance = None


def get_session_storage() -> SessionStorage:
    """
    Get session storage instance (singleton).

    Priority:
    1. Redis (if available and configured)
    2. PostgreSQL (fallback if DB is configured)
    3. In-Memory (development only)
    """
    global _storage_instance

    if _storage_instance is not None:
        return _storage_instance

    # Try Redis first
    redis_url = getattr(settings, "REDIS_URL", None)
    if redis_url:
        try:
            storage = RedisSessionStorage(redis_url)
            if storage.redis_available:
                logger.info("Using Redis session storage")
                _storage_instance = storage
                return storage
        except Exception as e:
            logger.warning(f"Failed to initialize Redis storage: {e}")

    # Fall back to PostgreSQL
    if settings.DATABASE_URL and not settings.DATABASE_URL.startswith("sqlite"):
        try:
            storage = PostgreSQLSessionStorage()
            logger.info("Using PostgreSQL session storage")
            _storage_instance = storage
            return storage
        except Exception as e:
            logger.warning(f"Failed to initialize PostgreSQL storage: {e}")

    # Last resort: in-memory (not production-safe)
    logger.warning("Using in-memory session storage - NOT PRODUCTION SAFE")
    _storage_instance = InMemorySessionStorage()
    return _storage_instance
