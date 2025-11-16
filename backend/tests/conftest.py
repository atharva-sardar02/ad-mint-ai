"""
Pytest configuration and fixtures.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import all models to ensure they're registered with Base.metadata
from app.db.base import Base
from app.db.models.editing_session import EditingSession
from app.db.models.generation import Generation
from app.db.models.user import User

# Ensure models are registered (explicit import)
_ = Generation
_ = User
_ = EditingSession


@pytest.fixture(scope="function")
def db_session():
    """
    Create a test database session with in-memory SQLite database.
    
    Yields:
        Session: SQLAlchemy session for testing
    """
    # Create in-memory SQLite database with foreign keys enabled
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Enable foreign key constraints in SQLite (disabled by default)
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    
    Base.metadata.create_all(bind=engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        bind=engine,
    )
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

