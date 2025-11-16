"""
Database migration script to add parent_generation_id field to generations table.

This migration adds:
- parent_generation_id: String field to link edited videos to their original generation

Run this script to update existing databases:
    python -m app.db.migrations.add_parent_generation_id

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
    Run migration to add parent_generation_id column.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add parent_generation_id to generations table")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    with engine.connect() as conn:
        try:
            if is_sqlite:
                # SQLite doesn't support IF NOT EXISTS, so we'll catch the error
                try:
                    conn.execute(text(
                        "ALTER TABLE generations ADD COLUMN parent_generation_id VARCHAR(36)"
                    ))
                    print("✅ Added parent_generation_id column")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  parent_generation_id column already exists, skipping")
                    else:
                        raise
                
                conn.commit()
            
            elif is_postgres:
                # PostgreSQL supports IF NOT EXISTS
                conn.execute(text(
                    "ALTER TABLE generations ADD COLUMN IF NOT EXISTS parent_generation_id VARCHAR(36)"
                ))
                conn.commit()
                print("✅ Added parent_generation_id column (or already exists)")
            
            else:
                print(f"⚠️  Unknown database type: {db_url}")
                print("Please run migration manually for your database")
                return False
            
            print("✅ Migration completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            conn.rollback()
            raise


if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        sys.exit(1)

