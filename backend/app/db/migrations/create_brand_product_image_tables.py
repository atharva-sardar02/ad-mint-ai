"""
Database migration script to create brand_style_folders, product_image_folders, and uploaded_images tables.

This migration creates:
- brand_style_folders table with all required fields
- product_image_folders table with all required fields
- uploaded_images table with all required fields
- Foreign key relationships to users table
- Indexes on foreign keys and frequently queried fields

Run this script to update existing databases:
    python -m app.db.migrations.create_brand_product_image_tables

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
    Run migration to create brand_style_folders, product_image_folders, and uploaded_images tables.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("Starting migration: Create brand_style_folders, product_image_folders, and uploaded_images tables")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    try:
        if is_sqlite:
            # SQLite: use connect() and manual commit
            with engine.connect() as conn:
                # Create brand_style_folders table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS brand_style_folders (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL UNIQUE,
                        uploaded_at DATETIME NOT NULL,
                        image_count INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("Created brand_style_folders table")
                
                # Create index on user_id
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_brand_style_folders_user_id ON brand_style_folders(user_id)"
                    ))
                except OperationalError as e:
                    if "already exists" not in str(e).lower():
                        raise
                
                # Create product_image_folders table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_image_folders (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL UNIQUE,
                        uploaded_at DATETIME NOT NULL,
                        image_count INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("Created product_image_folders table")
                
                # Create index on user_id
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_product_image_folders_user_id ON product_image_folders(user_id)"
                    ))
                except OperationalError as e:
                    if "already exists" not in str(e).lower():
                        raise
                
                # Create uploaded_images table
                # Note: folder_id doesn't have FK constraint because it can point to either
                # brand_style_folders.id or product_image_folders.id. Validation is handled at application level.
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS uploaded_images (
                        id VARCHAR(36) PRIMARY KEY,
                        folder_id VARCHAR(36) NOT NULL,
                        folder_type VARCHAR(20) NOT NULL CHECK (folder_type IN ('brand_style', 'product')),
                        filename VARCHAR(255) NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_size INTEGER NOT NULL,
                        uploaded_at DATETIME NOT NULL
                    )
                """))
                print("Created uploaded_images table")
                
                # Create indexes
                try:
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_uploaded_images_folder_id ON uploaded_images(folder_id)"
                    ))
                    conn.execute(text(
                        "CREATE INDEX IF NOT EXISTS ix_uploaded_images_folder_type ON uploaded_images(folder_type)"
                    ))
                except OperationalError as e:
                    if "already exists" not in str(e).lower():
                        raise
                
                conn.commit()
                print("Migration completed successfully (SQLite)")
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling (SQLAlchemy 2.0)
            with engine.begin() as conn:
                # Create enum type for folder_type
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE folder_type_enum AS ENUM ('brand_style', 'product');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Create brand_style_folders table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS brand_style_folders (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL UNIQUE,
                        uploaded_at TIMESTAMP NOT NULL,
                        image_count INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("✅ Created brand_style_folders table")
                
                # Create index on user_id
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_brand_style_folders_user_id ON brand_style_folders(user_id)"
                ))
                
                # Create product_image_folders table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS product_image_folders (
                        id VARCHAR(36) PRIMARY KEY,
                        user_id VARCHAR(36) NOT NULL UNIQUE,
                        uploaded_at TIMESTAMP NOT NULL,
                        image_count INTEGER NOT NULL DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                """))
                print("✅ Created product_image_folders table")
                
                # Create index on user_id
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_product_image_folders_user_id ON product_image_folders(user_id)"
                ))
                
                # Create uploaded_images table
                # Note: folder_id doesn't have FK constraint because it can point to either
                # brand_style_folders.id or product_image_folders.id. Validation is handled at application level.
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS uploaded_images (
                        id VARCHAR(36) PRIMARY KEY,
                        folder_id VARCHAR(36) NOT NULL,
                        folder_type folder_type_enum NOT NULL,
                        filename VARCHAR(255) NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_size INTEGER NOT NULL,
                        uploaded_at TIMESTAMP NOT NULL
                    )
                """))
                print("✅ Created uploaded_images table")
                
                # Create indexes
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_uploaded_images_folder_id ON uploaded_images(folder_id)"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_uploaded_images_folder_type ON uploaded_images(folder_type)"
                ))
                
                print("Migration completed successfully (PostgreSQL)")
        
        else:
            print(f"Unknown database type: {db_url}")
            print("Please run migration manually for your database")
            return False
        
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

