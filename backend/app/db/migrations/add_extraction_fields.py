"""
Database migration script to add extraction fields to brand_style_folders and uploaded_images tables.

This migration adds:
- extracted_style_json, extraction_status, extracted_at to brand_style_folders
- extracted_product_style_json to uploaded_images

Run this script to update existing databases:
    python -m app.db.migrations.add_extraction_fields

Note: For SQLite, this uses ALTER TABLE ADD COLUMN IF NOT EXISTS.
For PostgreSQL, this uses ALTER TABLE ADD COLUMN IF NOT EXISTS.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings
from app.db.base import engine


def run_migration():
    """
    Run migration to add extraction fields to brand_style_folders and uploaded_images tables.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("Starting migration: Add extraction fields to brand_style_folders and uploaded_images")
    
    # Check database type
    db_url = settings.DATABASE_URL
    is_sqlite = db_url.startswith("sqlite")
    is_postgres = "postgresql" in db_url or "postgres" in db_url
    
    try:
        if is_sqlite:
            # SQLite: use connect() and manual commit
            with engine.connect() as conn:
                # Add extraction fields to brand_style_folders
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN extracted_style_json TEXT
                    """))
                    print("Added extracted_style_json column to brand_style_folders")
                except OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        raise
                    print("Column extracted_style_json already exists in brand_style_folders")
                
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN extraction_status VARCHAR(20) DEFAULT 'pending'
                    """))
                    print("Added extraction_status column to brand_style_folders")
                except OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        raise
                    print("Column extraction_status already exists in brand_style_folders")
                
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN extracted_at DATETIME
                    """))
                    print("Added extracted_at column to brand_style_folders")
                except OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        raise
                    print("Column extracted_at already exists in brand_style_folders")
                
                # Add product style field to uploaded_images
                try:
                    conn.execute(text("""
                        ALTER TABLE uploaded_images 
                        ADD COLUMN extracted_product_style_json TEXT
                    """))
                    print("Added extracted_product_style_json column to uploaded_images")
                except OperationalError as e:
                    if "duplicate column" not in str(e).lower():
                        raise
                    print("Column extracted_product_style_json already exists in uploaded_images")
                
                conn.commit()
                print("Migration completed successfully (SQLite)")
        
        elif is_postgres:
            # PostgreSQL: use begin() for proper transaction handling
            with engine.begin() as conn:
                # Create enum type for extraction_status if it doesn't exist
                conn.execute(text("""
                    DO $$ BEGIN
                        CREATE TYPE extraction_status_enum AS ENUM ('pending', 'completed', 'failed');
                    EXCEPTION
                        WHEN duplicate_object THEN null;
                    END $$;
                """))
                
                # Add extraction fields to brand_style_folders
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN IF NOT EXISTS extracted_style_json JSONB
                    """))
                    print("✅ Added extracted_style_json column to brand_style_folders")
                except ProgrammingError as e:
                    if "already exists" not in str(e).lower():
                        raise
                    print("Column extracted_style_json already exists in brand_style_folders")
                
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN IF NOT EXISTS extraction_status extraction_status_enum DEFAULT 'pending'
                    """))
                    print("✅ Added extraction_status column to brand_style_folders")
                except ProgrammingError as e:
                    if "already exists" not in str(e).lower():
                        raise
                    print("Column extraction_status already exists in brand_style_folders")
                
                try:
                    conn.execute(text("""
                        ALTER TABLE brand_style_folders 
                        ADD COLUMN IF NOT EXISTS extracted_at TIMESTAMP
                    """))
                    print("✅ Added extracted_at column to brand_style_folders")
                except ProgrammingError as e:
                    if "already exists" not in str(e).lower():
                        raise
                    print("Column extracted_at already exists in brand_style_folders")
                
                # Add product style field to uploaded_images
                try:
                    conn.execute(text("""
                        ALTER TABLE uploaded_images 
                        ADD COLUMN IF NOT EXISTS extracted_product_style_json JSONB
                    """))
                    print("✅ Added extracted_product_style_json column to uploaded_images")
                except ProgrammingError as e:
                    if "already exists" not in str(e).lower():
                        raise
                    print("Column extracted_product_style_json already exists in uploaded_images")
                
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

