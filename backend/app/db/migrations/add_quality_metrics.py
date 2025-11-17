"""
Database migration script to add quality_metrics table.

This migration adds:
- quality_metrics table with fields:
  - id (UUID, primary key)
  - generation_id (FK to generations)
  - scene_number (int)
  - clip_path (string)
  - vbench_scores (JSON)
  - overall_quality (float)
  - passed_threshold (bool)
  - regeneration_attempts (int, default 0)
  - created_at (timestamp)

Run this script to update existing databases:
    python -m app.db.migrations.add_quality_metrics

Note: For SQLite, this uses CREATE TABLE.
For PostgreSQL, this uses CREATE TABLE IF NOT EXISTS.

Migration Approach:
This project uses standalone migration scripts rather than Alembic. This approach
is consistent with other migrations in this project. The migration script is idempotent
and can be run multiple times safely. For production deployments, migrations should
be run as part of the deployment process.
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
    Run migration to add quality_metrics table.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add quality_metrics table")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    with engine.connect() as conn:
        try:
            if is_sqlite:
                # SQLite doesn't support IF NOT EXISTS for CREATE TABLE, so we'll catch errors
                try:
                    conn.execute(text("""
                        CREATE TABLE quality_metrics (
                            id VARCHAR(36) PRIMARY KEY,
                            generation_id VARCHAR(36) NOT NULL,
                            scene_number INTEGER NOT NULL,
                            clip_path VARCHAR(500) NOT NULL,
                            vbench_scores TEXT NOT NULL,
                            overall_quality REAL NOT NULL,
                            passed_threshold BOOLEAN NOT NULL DEFAULT 0,
                            regeneration_attempts INTEGER NOT NULL DEFAULT 0,
                            created_at DATETIME NOT NULL,
                            FOREIGN KEY (generation_id) REFERENCES generations(id)
                        )
                    """))
                    print("✅ Created quality_metrics table")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  quality_metrics table already exists, skipping")
                    else:
                        raise
                
                # Create indexes
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_quality_metrics_generation_id ON quality_metrics(generation_id)"))
                    print("✅ Created index on quality_metrics.generation_id")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  Index on quality_metrics.generation_id already exists, skipping")
                    else:
                        raise
                
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_quality_metrics_created_at ON quality_metrics(created_at)"))
                    print("✅ Created index on quality_metrics.created_at")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  Index on quality_metrics.created_at already exists, skipping")
                    else:
                        raise
                
                conn.commit()
            
            elif is_postgres:
                # PostgreSQL supports IF NOT EXISTS
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS quality_metrics (
                        id VARCHAR(36) PRIMARY KEY,
                        generation_id VARCHAR(36) NOT NULL,
                        scene_number INTEGER NOT NULL,
                        clip_path VARCHAR(500) NOT NULL,
                        vbench_scores JSONB NOT NULL,
                        overall_quality REAL NOT NULL,
                        passed_threshold BOOLEAN NOT NULL DEFAULT FALSE,
                        regeneration_attempts INTEGER NOT NULL DEFAULT 0,
                        created_at TIMESTAMP NOT NULL,
                        FOREIGN KEY (generation_id) REFERENCES generations(id)
                    )
                """))
                print("✅ Created quality_metrics table (or already exists)")
                
                # Create indexes
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_quality_metrics_generation_id ON quality_metrics(generation_id)"))
                print("✅ Created index on quality_metrics.generation_id")
                
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_quality_metrics_created_at ON quality_metrics(created_at)"))
                print("✅ Created index on quality_metrics.created_at")
                
                conn.commit()
            
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

