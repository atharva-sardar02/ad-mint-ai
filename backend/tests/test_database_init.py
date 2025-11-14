"""
Tests for database initialization.
"""
import pytest
from sqlalchemy import inspect, create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.models import Generation, User


def test_database_table_creation():
    """Test that database initialization creates users and generations tables."""
    # Create in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    
    # Import models to register them
    _ = User, Generation
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    # Inspect database
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    assert "users" in tables
    assert "generations" in tables


def test_users_table_schema():
    """Test that users table has correct schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    _ = User, Generation
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("users")}
    
    # Check required columns exist
    assert "id" in columns
    assert "username" in columns
    assert "password_hash" in columns
    assert "email" in columns
    assert "total_generations" in columns
    assert "total_cost" in columns
    assert "created_at" in columns
    assert "last_login" in columns
    
    # Check data types
    assert columns["id"]["type"].python_type == str
    assert columns["username"]["type"].python_type == str
    assert columns["total_generations"]["type"].python_type == int
    assert columns["total_cost"]["type"].python_type == float


def test_generations_table_schema():
    """Test that generations table has correct schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    _ = User, Generation
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    columns = {col["name"]: col for col in inspector.get_columns("generations")}
    
    # Check required columns exist
    assert "id" in columns
    assert "user_id" in columns
    assert "prompt" in columns
    assert "status" in columns
    assert "created_at" in columns


def test_database_indexes():
    """Test that indexes are created on specified columns."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    _ = User, Generation
    Base.metadata.create_all(bind=engine)
    
    inspector = inspect(engine)
    
    # Check users.username unique index
    users_indexes = inspector.get_indexes("users")
    username_index = next((idx for idx in users_indexes if "username" in idx["column_names"]), None)
    assert username_index is not None
    # SQLite returns 1 for True, so check for truthiness
    assert username_index["unique"] is True or username_index["unique"] == 1
    
    # Check generations indexes
    generations_indexes = inspector.get_indexes("generations")
    index_columns = [col for idx in generations_indexes for col in idx["column_names"]]
    
    assert "user_id" in index_columns
    assert "status" in index_columns
    assert "created_at" in index_columns

