"""
Database migration script to add temp_clip_paths and cancellation_requested fields to generations table.

This migration adds:
- temp_clip_paths: JSON field to store array of temp video clip file paths
- cancellation_requested: Boolean field to track cancellation requests

Run this script to update existing databases:
    python -m app.db.migrations.add_temp_clip_paths_and_cancellation

Note: For SQLite, this uses ALTER TABLE ADD COLUMN.
For PostgreSQL, this uses ALTER TABLE ADD COLUMN IF NOT EXISTS.
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
    Run migration to add temp_clip_paths and cancellation_requested columns.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add temp_clip_paths and cancellation_requested to generations table")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    try:
        if is_sqlite:
            # SQLite: use connect() and manual commit
            with engine.connect() as conn:
                try:
                    conn.execute(text(
                        "ALTER TABLE generations ADD COLUMN temp_clip_paths TEXT"
                    ))
                    print("✅ Added temp_clip_paths column")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  temp_clip_paths column already exists, skipping")
                    else:
                        raise
                
                try:
                    conn.execute(text(
                        "ALTER TABLE generations ADD COLUMN cancellation_requested INTEGER DEFAULT 0"
                    ))
                    print("✅ Added cancellation_requested column")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  cancellation_requested column already exists, skipping")
                    else:
                        raise
                
                conn.commit()
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling (SQLAlchemy 2.0)
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE generations ADD COLUMN IF NOT EXISTS temp_clip_paths JSONB"
                ))
                print("✅ Added temp_clip_paths column (or already exists)")
                
                conn.execute(text(
                    "ALTER TABLE generations ADD COLUMN IF NOT EXISTS cancellation_requested BOOLEAN DEFAULT FALSE"
                ))
                print("✅ Added cancellation_requested column (or already exists)")
        
        else:
            print(f"⚠️  Unknown database type: {db_url}")
            print("Please run migration manually for your database")
            return False
        
        print("✅ Migration completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)



