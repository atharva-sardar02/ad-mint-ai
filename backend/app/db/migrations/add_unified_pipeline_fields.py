"""
Add JSONB fields for unified pipeline to generations table.

This migration adds the new JSONB fields needed for the unified pipeline:
- brand_assets: Uploaded brand images (product_images, logo, character_images)
- reference_images: 3 reference images with Vision analysis
- scenes: Array of scene objects
- video_clips: Array of video clip objects
- config: Pipeline configuration snapshot
- current_stage: Track which pipeline stage we're in

These fields enable consolidation of 4 separate pipelines into 1 unified system.
"""
import sqlite3
from pathlib import Path

def migrate():
    """Run migration to add unified pipeline fields."""
    # Database is in backend root directory
    db_path = Path(__file__).parent.parent.parent.parent / "ad_mint_ai.db"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Check if columns already exist
        cursor.execute("PRAGMA table_info(generations)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Add brand_assets JSONB field
        if "brand_assets" not in existing_columns:
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN brand_assets TEXT
            """)
            print("✓ Added brand_assets column")

        # Add reference_images JSONB field
        if "reference_images" not in existing_columns:
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN reference_images TEXT
            """)
            print("✓ Added reference_images column")

        # Add scenes JSONB field
        if "scenes" not in existing_columns:
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN scenes TEXT
            """)
            print("✓ Added scenes column")

        # Add video_clips JSONB field
        if "video_clips" not in existing_columns:
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN video_clips TEXT
            """)
            print("✓ Added video_clips column")

        # Add config JSONB field
        if "config" not in existing_columns:
            cursor.execute("""
                ALTER TABLE generations
                ADD COLUMN config TEXT
            """)
            print("✓ Added config column")

        # Update current_stage column if needed (may already exist as current_step)
        # We'll keep current_step for backward compatibility

        conn.commit()
        print("✅ Migration completed successfully")

def rollback():
    """Rollback migration (not recommended after data is populated)."""
    # Database is in backend root directory
    db_path = Path(__file__).parent.parent.parent.parent / "ad_mint_ai.db"

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # SQLite doesn't support DROP COLUMN easily
        # Would require recreating table, so we'll just warn
        print("⚠️  Rollback not implemented for SQLite")
        print("    (SQLite doesn't support DROP COLUMN)")
        print("    Columns: brand_assets, reference_images, scenes, video_clips, config")

if __name__ == "__main__":
    migrate()
