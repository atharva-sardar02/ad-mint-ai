"""
Database initialization script.
Creates all database tables using SQLAlchemy Base.metadata.create_all().
"""
import sys

from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base, engine
from app.db.models import Generation, User  # Import models to register them with Base


def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    Raises:
        SQLAlchemyError: If database connection or table creation fails
    """
    try:
        # Import all models to ensure they're registered with Base
        # This is already done above, but explicit for clarity
        _ = User, Generation
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except SQLAlchemyError as e:
        print(f"❌ Error creating database tables: {e}")
        raise


if __name__ == "__main__":
    try:
        init_db()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)

