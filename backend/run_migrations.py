"""
Run all database migrations in the correct order.

This script:
1. Initializes the database (creates base tables)
2. Runs all migrations in the correct order
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.db.init_db import init_db

# Migration order - must be run in this sequence
MIGRATIONS = [
    "app.db.migrations.create_editing_sessions_table",
    "app.db.migrations.add_generation_groups",
    "app.db.migrations.add_title_to_generations",
    "app.db.migrations.add_llm_specification_and_scene_plan",
    "app.db.migrations.add_video_url_and_thumbnail_url",
    "app.db.migrations.add_temp_clip_paths_and_cancellation",
    "app.db.migrations.add_seed_value",
    "app.db.migrations.add_coherence_settings",
    "app.db.migrations.add_parent_generation_id",
    "app.db.migrations.add_basic_settings_and_generation_time",
    "app.db.migrations.create_brand_product_image_tables",
    "app.db.migrations.add_extraction_fields",
]


def run_all_migrations():
    """Run all database migrations in order."""
    print("=" * 60)
    print("Database Migration Runner")
    print("=" * 60)
    
    # Step 1: Initialize database (creates base tables)
    print("\nStep 1: Initializing database...")
    try:
        init_db()
        print("[OK] Database initialized successfully")
    except Exception as e:
        print(f"[ERROR] Database initialization failed: {e}")
        print("[WARN] Continuing with migrations anyway...")
    
    # Step 2: Run all migrations
    print("\nStep 2: Running migrations...")
    failed_migrations = []
    
    for migration_module in MIGRATIONS:
        try:
            print(f"\nRunning: {migration_module}")
            module = __import__(migration_module, fromlist=["run_migration"])
            if hasattr(module, "run_migration"):
                success = module.run_migration()
                if success:
                    print(f"[OK] {migration_module} completed")
                else:
                    print(f"[WARN] {migration_module} returned False")
                    failed_migrations.append(migration_module)
            else:
                print(f"[WARN] {migration_module} has no run_migration function")
        except Exception as e:
            print(f"[ERROR] {migration_module} failed: {e}")
            failed_migrations.append(migration_module)
    
    # Summary
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    
    if failed_migrations:
        print(f"[ERROR] {len(failed_migrations)} migration(s) failed:")
        for migration in failed_migrations:
            print(f"   - {migration}")
        return False
    else:
        print("[OK] All migrations completed successfully!")
        return True


if __name__ == "__main__":
    try:
        success = run_all_migrations()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

