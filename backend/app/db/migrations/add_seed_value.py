"""
Database migration script to add seed_value field to generations table.

This migration adds:
- seed_value: Integer field (nullable) to store seed value for visual consistency

Run this script to update existing databases:
    python -m app.db.migrations.add_seed_value

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
    Run migration to add seed_value column.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add seed_value to generations table")
    
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
                        "ALTER TABLE generations ADD COLUMN seed_value INTEGER"
                    ))
                    print("✅ Added seed_value column")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower():
                        print("ℹ️  seed_value column already exists, skipping")
                    else:
                        raise
                
                conn.commit()
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling (SQLAlchemy 2.0)
            with engine.begin() as conn:
                conn.execute(text(
                    "ALTER TABLE generations ADD COLUMN IF NOT EXISTS seed_value INTEGER"
                ))
                print("✅ Added seed_value column (or already exists)")
        
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


