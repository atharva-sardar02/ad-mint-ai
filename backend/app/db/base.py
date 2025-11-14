"""
SQLAlchemy base and engine initialization.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using them
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

# Create declarative base class for all ORM models
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

