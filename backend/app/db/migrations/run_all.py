"""
Run all database migrations in order.

This script runs all migrations sequentially. Migrations are idempotent
and can be run multiple times safely.

Usage:
    python -m app.db.migrations.run_all
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from app.db.migrations.add_video_url_and_thumbnail_url import run_migration as migrate_video_url
from app.db.migrations.add_llm_specification_and_scene_plan import run_migration as migrate_llm_spec
from app.db.migrations.add_temp_clip_paths_and_cancellation import run_migration as migrate_temp_clips


def run_all_migrations():
    """
    Run all database migrations in order.
    
    Returns:
        bool: True if all migrations succeeded, False otherwise
    """
    migrations = [
        ("Add video_url and thumbnail_url", migrate_video_url),
        ("Add llm_specification and scene_plan", migrate_llm_spec),
        ("Add temp_clip_paths and cancellation_requested", migrate_temp_clips),
    ]
    
    print("🔄 Starting database migrations...")
    print(f"📋 Total migrations to run: {len(migrations)}\n")
    
    for i, (name, migration_func) in enumerate(migrations, 1):
        print(f"[{i}/{len(migrations)}] {name}")
        print("-" * 60)
        
        try:
            success = migration_func()
            if not success:
                print(f"❌ Migration failed: {name}")
                return False
            print()  # Empty line for readability
        except Exception as e:
            print(f"❌ Migration error in {name}: {e}")
            return False
    
    print("✅ All migrations completed successfully")
    return True


if __name__ == "__main__":
    try:
        success = run_all_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Fatal error running migrations: {e}")
        sys.exit(1)

