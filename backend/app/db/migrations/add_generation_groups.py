"""
Database migration script to add generation_groups table and generation_group_id field to generations table.

This migration adds:
- generation_groups table with fields: id (UUID), user_id (FK), created_at, comparison_type (enum: 'settings', 'prompt')
- generation_group_id field to generations table (FK, nullable, indexed)

Run this script to update existing databases:
    python -m app.db.migrations.add_generation_groups

Note: For SQLite, this uses CREATE TABLE and ALTER TABLE ADD COLUMN.
For PostgreSQL, this uses CREATE TABLE IF NOT EXISTS and ALTER TABLE ADD COLUMN IF NOT EXISTS.

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
    Run migration to add generation_groups table and generation_group_id column.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add generation_groups table and generation_group_id to generations table")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    try:
        if is_sqlite:
            # SQLite: use connect() and manual commit
            with engine.connect() as conn:
                # SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we'll catch errors
                # Create generation_groups table
                try:
                    conn.execute(text("""
                        CREATE TABLE generation_groups (
                            id VARCHAR(36) PRIMARY KEY,
                            user_id VARCHAR(36) NOT NULL,
                            created_at DATETIME NOT NULL,
                            comparison_type VARCHAR(20) NOT NULL CHECK(comparison_type IN ('settings', 'prompt')),
                            FOREIGN KEY (user_id) REFERENCES users(id)
                        )
                    """))
                    print("✅ Created generation_groups table")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  generation_groups table already exists, skipping")
                    else:
                        raise
                
                # Create index on user_id
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_generation_groups_user_id ON generation_groups(user_id)"))
                    print("✅ Created index on generation_groups.user_id")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  Index on generation_groups.user_id already exists, skipping")
                    else:
                        raise
                
                # Create index on created_at
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_generation_groups_created_at ON generation_groups(created_at)"))
                    print("✅ Created index on generation_groups.created_at")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  Index on generation_groups.created_at already exists, skipping")
                    else:
                        raise
                
                # Add generation_group_id column to generations table
                try:
                    conn.execute(text(
                        "ALTER TABLE generations ADD COLUMN generation_group_id VARCHAR(36)"
                    ))
                    print("✅ Added generation_group_id column to generations table")
                except OperationalError as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print("ℹ️  generation_group_id column already exists, skipping")
                    else:
                        raise
                
                # Create index on generation_group_id
                try:
                    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_generations_generation_group_id ON generations(generation_group_id)"))
                    print("✅ Created index on generations.generation_group_id")
                except OperationalError as e:
                    if "already exists" in str(e).lower() or "duplicate" in str(e).lower():
                        print("ℹ️  Index on generations.generation_group_id already exists, skipping")
                    else:
                        raise
                
                # Add foreign key constraint (SQLite supports this)
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS temp_fk_check ON generations(generation_group_id)
                    """))
                    # Note: SQLite doesn't support adding foreign key constraints to existing tables easily
                    # The foreign key relationship is enforced by SQLAlchemy ORM
                    print("ℹ️  Foreign key relationship will be enforced by ORM")
                except OperationalError:
                    pass  # Index creation might fail if already exists, that's okay
                
                conn.commit()
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling (SQLAlchemy 2.0)
            with engine.begin() as conn:
                # Create generation_groups table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS generation_groups (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        comparison_type VARCHAR(20) NOT NULL CHECK(comparison_type IN ('settings', 'prompt')),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("✅ Created generation_groups table (or already exists)")
                
                # Create indexes
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_generation_groups_user_id ON generation_groups(user_id)
                """))
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_generation_groups_created_at ON generation_groups(created_at)
                """))
                print("✅ Created indexes on generation_groups")
                
                # Add generation_group_id column to generations table
                conn.execute(text(
                    "ALTER TABLE generations ADD COLUMN IF NOT EXISTS generation_group_id VARCHAR(36)"
                ))
                print("✅ Added generation_group_id column to generations table (or already exists)")
                
                # Create index on generation_group_id
                conn.execute(text("""
                    CREATE INDEX IF NOT EXISTS ix_generations_generation_group_id ON generations(generation_group_id)
                """))
                print("✅ Created index on generations.generation_group_id")
                
                # Add foreign key constraint
                try:
                    conn.execute(text("""
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM pg_constraint 
                                WHERE conname = 'generations_generation_group_id_fkey'
                            ) THEN
                                ALTER TABLE generations 
                                ADD CONSTRAINT generations_generation_group_id_fkey 
                                FOREIGN KEY (generation_group_id) REFERENCES generation_groups(id);
                            END IF;
                        END $$;
                    """))
                    print("✅ Added foreign key constraint on generations.generation_group_id")
                except OperationalError as e:
                    if "already exists" in str(e).lower():
                        print("ℹ️  Foreign key constraint already exists, skipping")
                    else:
                        raise
        
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



