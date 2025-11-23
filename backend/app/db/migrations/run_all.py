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
from app.db.migrations.add_title_to_generations import run_migration as migrate_title
from app.db.migrations.add_seed_value import run_migration as migrate_seed
from app.db.migrations.add_parent_generation_id import run_migration as migrate_parent_id
from app.db.migrations.add_generation_groups import run_migration as migrate_groups
from app.db.migrations.add_coherence_settings import run_migration as migrate_coherence
from app.db.migrations.create_editing_sessions_table import run_migration as migrate_editing_sessions
from app.db.migrations.add_basic_settings_and_generation_time import run_migration as migrate_basic_settings


def run_all_migrations():
    """
    Run all database migrations in order.
    
    Returns:
        bool: True if all migrations succeeded, False otherwise
    """
    migrations = [
        ("Create editing_sessions table", migrate_editing_sessions),
        ("Add generation_groups", migrate_groups),
        ("Add title to generations", migrate_title),
        ("Add llm_specification and scene_plan", migrate_llm_spec),
        ("Add video_url and thumbnail_url", migrate_video_url),
        ("Add temp_clip_paths and cancellation_requested", migrate_temp_clips),
        ("Add seed_value to generations", migrate_seed),
        ("Add coherence_settings", migrate_coherence),
        ("Add parent_generation_id to generations", migrate_parent_id),
        ("Add basic_settings and generation_time", migrate_basic_settings),
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

