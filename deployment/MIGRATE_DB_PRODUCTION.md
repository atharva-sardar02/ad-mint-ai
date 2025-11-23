# Database Migration Guide for Production

## Quick Migration Command

SSH into your production EC2 instance and run:

```bash
# SSH into EC2 (replace with your actual IP and key)
ssh -i ad-mint-ai-key.pem ubuntu@YOUR_EC2_IP

# Navigate to backend directory
cd /var/www/ad-mint-ai/backend

# Activate virtual environment
source venv/bin/activate

# Option 1: Run migrations with initialization (RECOMMENDED)
python run_migrations.py

# Option 2: Use the module approach (only runs migrations, assumes DB initialized)
python -m app.db.migrations.run_all

# Restart FastAPI service to ensure changes take effect
sudo systemctl restart fastapi

# Check service status
sudo systemctl status fastapi
```

## What This Does

1. **Initializes database** (creates base tables if they don't exist)
2. **Runs all migrations** in the correct order:
   - Add video_url and thumbnail_url
   - Add llm_specification and scene_plan
   - Add temp_clip_paths and cancellation_requested
   - Add title to generations
   - Add seed_value to generations
   - Add parent_generation_id to generations
   - Add generation_groups
   - Add coherence_settings
   - Create editing_sessions table
   - Add basic_settings and generation_time

## Verify Migration Success

```bash
# Check migration output for success messages
# Should see: "✅ All migrations completed successfully"

# Check FastAPI logs for any errors
sudo journalctl -u fastapi -n 50 --no-pager

# Test health endpoint
curl http://127.0.0.1:8000/api/health
```

## Troubleshooting

### If migrations fail:

1. **Check database connection:**
   ```bash
   # Verify .env file has correct DATABASE_URL
   cat /var/www/ad-mint-ai/backend/.env | grep DATABASE_URL
   ```

2. **Check database permissions:**
   ```bash
   # For SQLite, check file permissions
   ls -la /var/www/ad-mint-ai/backend/ad_mint_ai.db
   
   # For PostgreSQL, test connection
   psql -h YOUR_RDS_ENDPOINT -U ad_mint_user -d ad_mint_ai
   ```

3. **View detailed error:**
   ```bash
   # Run migrations with verbose output
   python run_migrations.py
   ```

### If service won't start after migration:

```bash
# Check service logs
sudo journalctl -u fastapi -n 100 --no-pager

# Restart service
sudo systemctl restart fastapi

# Check status
sudo systemctl status fastapi
```

## Automated Migration (Future)

To add migrations to your deployment script, update `deployment/deploy.sh` to include:

```bash
# After database initialization (around line 219)
python -m app.db.migrations.run_all || error_exit "Failed to run database migrations"
```

