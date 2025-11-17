"""
Database migration script to create editing_sessions table.

This migration creates:
- editing_sessions table with all required fields
- Foreign key relationships to generations and users tables
- Indexes on generation_id and user_id for query performance

Run this script to update existing databases:
    python -m app.db.migrations.create_editing_sessions_table

Note: For SQLite, this uses CREATE TABLE IF NOT EXISTS.
For PostgreSQL, this uses CREATE TABLE IF NOT EXISTS.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.db.base import engine


def run_migration():
    """
    Run migration to create editing_sessions table.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("Starting migration: Create editing_sessions table")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    try:
        if is_sqlite:
            # SQLite: use connect() and manual commit
            with engine.connect() as conn:
                # SQLite CREATE TABLE IF NOT EXISTS
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS editing_sessions (
                        id VARCHAR(36) PRIMARY KEY,
                        generation_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        original_video_path VARCHAR(500) NOT NULL,
                        editing_state TEXT NOT NULL,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        exported_video_path VARCHAR(500),
                        FOREIGN KEY (generation_id) REFERENCES generations(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                
                # Create indexes
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_editing_sessions_generation_id ON editing_sessions(generation_id)"
                    ))
                    print("Created index on generation_id (PostgreSQL)")
                except OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("Index on generation_id already exists, skipping")
                    else:
                        raise
                
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_editing_sessions_user_id ON editing_sessions(user_id)"
                    ))
                    print("Created index on user_id")
                except OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("Index on user_id already exists, skipping")
                    else:
                        raise
                
                conn.commit()
                print("Created editing_sessions table (SQLite)")
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling (SQLAlchemy 2.0)
            with engine.begin() as conn:
                # PostgreSQL CREATE TABLE IF NOT EXISTS
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS editing_sessions (
                        id VARCHAR(36) PRIMARY KEY,
                        generation_id VARCHAR(36) NOT NULL,
                        user_id VARCHAR(36) NOT NULL,
                        original_video_path VARCHAR(500) NOT NULL,
                        editing_state JSONB NOT NULL,
                        status VARCHAR(20) DEFAULT 'active',
                        created_at TIMESTAMP NOT NULL,
                        updated_at TIMESTAMP NOT NULL,
                        exported_video_path VARCHAR(500),
                        FOREIGN KEY (generation_id) REFERENCES generations(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                
                # Create indexes
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_editing_sessions_generation_id ON editing_sessions(generation_id)"
                ))
                print("✅ Created index on generation_id")
                
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_editing_sessions_user_id ON editing_sessions(user_id)"
                ))
                print("Created index on user_id")
                print("Created editing_sessions table (PostgreSQL)")
        
        else:
            print(f"Unknown database type: {db_url}")
            print("Please run migration manually for your database")
            return False
        
        print("Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"Migration failed: {e}")
        raise


if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)

