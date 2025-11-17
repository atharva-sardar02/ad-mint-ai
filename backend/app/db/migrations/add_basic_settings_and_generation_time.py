"""
Database migration script to add basic_settings and track generation_time_seconds properly.

This migration adds:
- model: String field to store the model used for generation
- num_clips: Integer field to store number of clips requested
- use_llm: Boolean field to store whether LLM was used
- generation_time_seconds: Already exists, but we'll ensure it's properly set

Run with:
    python -m app.db.migrations.add_basic_settings_and_generation_time
"""
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.db.session import SessionLocal
from app.db.base import engine
from sqlalchemy import text, inspect


def run_migration():
    """
    Run migration to add basic_settings fields to generations table.
    
    This migration is idempotent - it can be run multiple times safely.
    """
    print("🔄 Starting migration: Add basic_settings fields to generations table")
    
    db = SessionLocal()
    try:
        # Check database type
        db_type = engine.dialect.name
        
        if db_type == "sqlite":
            # SQLite: Check if columns exist, add if not
            inspector = inspect(engine)
            existing_columns = [col["name"] for col in inspector.get_columns("generations")]
            
            if "model" not in existing_columns:
                print("  Adding 'model' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN model VARCHAR(100)"))
                db.commit()
                print("  ✅ Added 'model' column")
            else:
                print("  ⏭️  'model' column already exists")
            
            if "num_clips" not in existing_columns:
                print("  Adding 'num_clips' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN num_clips INTEGER"))
                db.commit()
                print("  ✅ Added 'num_clips' column")
            else:
                print("  ⏭️  'num_clips' column already exists")
            
            if "use_llm" not in existing_columns:
                print("  Adding 'use_llm' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN use_llm BOOLEAN DEFAULT 1"))
                db.commit()
                print("  ✅ Added 'use_llm' column")
            else:
                print("  ⏭️  'use_llm' column already exists")
        
        elif db_type == "postgresql":
            # PostgreSQL: Use IF NOT EXISTS equivalent
            inspector = inspect(engine)
            existing_columns = [col["name"] for col in inspector.get_columns("generations")]
            
            if "model" not in existing_columns:
                print("  Adding 'model' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN model VARCHAR(100)"))
                db.commit()
                print("  ✅ Added 'model' column")
            else:
                print("  ⏭️  'model' column already exists")
            
            if "num_clips" not in existing_columns:
                print("  Adding 'num_clips' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN num_clips INTEGER"))
                db.commit()
                print("  ✅ Added 'num_clips' column")
            else:
                print("  ⏭️  'num_clips' column already exists")
            
            if "use_llm" not in existing_columns:
                print("  Adding 'use_llm' column...")
                db.execute(text("ALTER TABLE generations ADD COLUMN use_llm BOOLEAN DEFAULT TRUE"))
                db.commit()
                print("  ✅ Added 'use_llm' column")
            else:
                print("  ⏭️  'use_llm' column already exists")
        
        else:
            print(f"⚠️  Unknown database type: {db_type}")
            print("Please run migration manually for your database")
            return False
        
        print("✅ Migration completed successfully")
        return True
    
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    try:
        success = run_migration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Migration error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

