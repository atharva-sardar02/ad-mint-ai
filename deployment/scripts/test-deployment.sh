#!/bin/bash
# Test deployment script - mirrors CI/CD pipeline for manual testing
# Run this via SSH to test deployment before pushing to trigger CI/CD

set -e

DEPLOYMENT_PATH="${1:-/var/www/ad-mint-ai}"
BACKUP_PATH="${DEPLOYMENT_PATH}.backup"
DEPLOYMENT_DIR=$(dirname "$DEPLOYMENT_PATH")

echo "🧪 Starting TEST deployment (manual via SSH)..."
echo "📁 Deployment path: $DEPLOYMENT_PATH"
echo ""

# Step 1: Cleanup old backups and free disk space
echo "🧹 Step 1: Cleaning up old backups and freeing disk space..."
if [ -d "$DEPLOYMENT_DIR" ]; then
  # Find all .old-* directories and sort by modification time
  OLD_BACKUPS=$(sudo find "$DEPLOYMENT_DIR" -maxdepth 1 -type d -name "${DEPLOYMENT_PATH##*/}.old-*" -printf '%T@ %p\n' 2>/dev/null | sort -rn || true)
  
  if [ -n "$OLD_BACKUPS" ]; then
    BACKUP_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
    if [ "$BACKUP_COUNT" -gt 1 ]; then
      echo "🗑️  Found $BACKUP_COUNT old .old-* directories, keeping most recent, removing others..."
      KEEP_FIRST=true
      echo "$OLD_BACKUPS" | while read -r timestamp dir; do
        if [ "$KEEP_FIRST" = "true" ]; then
          echo "  ✅ Keeping most recent: $dir"
          KEEP_FIRST=false
        else
          echo "  🗑️  Removing: $dir"
          sudo rm -rf "$dir" 2>/dev/null || true
        fi
      done
    else
      KEPT_DIR=$(echo "$OLD_BACKUPS" | awk '{print $2}')
      echo "✅ Keeping only .old-* backup: $KEPT_DIR"
    fi
  fi
  
  # Remove old .backup directory only if we're about to create a new one
  if [ -d "$BACKUP_PATH" ]; then
    echo "🗑️  Removing old .backup directory (will create fresh one)..."
    sudo rm -rf "$BACKUP_PATH"
  fi
fi

# Clean up pip cache
echo "🧹 Cleaning pip cache..."
pip cache purge 2>/dev/null || true
sudo -H pip cache purge 2>/dev/null || true

# Clean up apt cache
echo "🧹 Cleaning apt cache..."
sudo apt-get clean 2>/dev/null || true
sudo apt-get autoclean 2>/dev/null || true

# Clean up temporary files
echo "🧹 Cleaning temporary files..."
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# Clean up old journal logs
echo "🧹 Cleaning old journal logs..."
sudo journalctl --vacuum-time=7d 2>/dev/null || true

# Show disk usage
echo "💾 Current disk usage:"
df -h / | tail -1
echo ""

# Step 2: Backup current deployment
echo "💾 Step 2: Creating backup of current deployment..."
if [ -d "$DEPLOYMENT_PATH" ]; then
  echo "📦 Copying deployment to backup (excluding large directories)..."
  sudo mkdir -p "$BACKUP_PATH"
  sudo rsync -a --exclude='node_modules' --exclude='venv' --exclude='__pycache__' --exclude='.git' --exclude='*.pyc' --exclude='.pytest_cache' --exclude='dist' --exclude='build' "$DEPLOYMENT_PATH/" "$BACKUP_PATH/"
  sudo chown -R ubuntu:ubuntu "$BACKUP_PATH"
  echo "✅ Backup created at: $BACKUP_PATH"
else
  echo "⚠️  Deployment directory not found, skipping backup"
fi
echo ""

# Step 3: Deploy backend
echo "🚀 Step 3: Deploying backend..."
# Navigate to deployment directory or create it
if [ ! -d "$DEPLOYMENT_PATH" ]; then
  echo "📁 Creating deployment directory..."
  sudo mkdir -p "$DEPLOYMENT_PATH"
  sudo chown ubuntu:ubuntu "$DEPLOYMENT_PATH"
fi

cd "$DEPLOYMENT_PATH"

# Check if it's a git repository, if not clone it
if [ ! -d ".git" ]; then
  echo "📥 Cloning repository (first time deployment or not a git repo)..."
  # Backup .env file if it exists
  ENV_BACKUP="/tmp/ad-mint-ai-env-backup"
  if [ -f "$DEPLOYMENT_PATH/backend/.env" ]; then
    echo "💾 Backing up .env file..."
    sudo cp "$DEPLOYMENT_PATH/backend/.env" "$ENV_BACKUP" 2>/dev/null || true
  fi
  
  # Remove old deployment directory (but keep venv if it exists to save space)
  if [ -d "$DEPLOYMENT_PATH" ]; then
    echo "🗑️  Removing old deployment directory..."
    # Remove everything except venv to save space
    sudo find "$DEPLOYMENT_PATH" -mindepth 1 -maxdepth 1 ! -name "venv" -exec sudo rm -rf {} + 2>/dev/null || true
  fi
  
  # Clone fresh
  git clone https://github.com/atharva-sardar02/ad-mint-ai.git "$DEPLOYMENT_PATH"
  cd "$DEPLOYMENT_PATH"
  sudo chown -R ubuntu:ubuntu "$DEPLOYMENT_PATH"
  
  # Restore .env file if we backed it up
  if [ -f "$ENV_BACKUP" ]; then
    echo "📝 Restoring .env file..."
    sudo cp "$ENV_BACKUP" "$DEPLOYMENT_PATH/backend/.env"
    sudo rm "$ENV_BACKUP"
    sudo chmod 640 "$DEPLOYMENT_PATH/backend/.env"
    sudo chown ubuntu:www-data "$DEPLOYMENT_PATH/backend/.env"
  fi
else
  # Pull latest code
  echo "📥 Pulling latest code from GitHub..."
  git fetch origin
  git reset --hard origin/main
fi

# Update dependencies
echo "📦 Updating Python dependencies..."
cd backend

# Check disk space before creating venv
AVAILABLE_SPACE=$(df / | tail -1 | awk '{print $4}')
echo "💾 Available disk space: ${AVAILABLE_SPACE}KB"

# Remove old venv if disk space is low (less than 500MB)
if [ "$AVAILABLE_SPACE" -lt 512000 ] && [ -d "venv" ]; then
  echo "⚠️  Low disk space, removing old venv..."
  rm -rf venv
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
  echo "🐍 Creating Python virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip --no-cache-dir
pip install -r requirements.txt --no-cache-dir

# Initialize database (create tables if they don't exist)
echo "🗄️  Initializing database (creating tables if needed)..."
python -m app.db.init_db
if [ $? -ne 0 ]; then
  echo "❌ Database initialization failed"
  exit 1
fi
echo "✅ Database initialized"

# Run database migrations
echo "🔄 Running database migrations..."
python -m app.db.migrations.run_all
if [ $? -ne 0 ]; then
  echo "❌ Database migrations failed"
  exit 1
fi
echo "✅ Database migrations completed"

# Ensure .env file has correct permissions
if [ -f ".env" ]; then
  echo "🔐 Setting .env file permissions..."
  sudo chmod 640 .env
  sudo chown ubuntu:www-data .env
fi

# Create output directories with proper permissions
echo "📁 Creating output directories..."
sudo mkdir -p output/cache output/videos output/thumbnails
sudo chown -R www-data:www-data output
sudo chmod -R 755 output

# Restart FastAPI service
echo "🔄 Restarting FastAPI service..."
sudo systemctl restart fastapi

# Wait for service to start and check status
echo "⏳ Waiting for service to start..."
sleep 5

# Check service status
if sudo systemctl is-active --quiet fastapi; then
  echo "✅ FastAPI service is running"
else
  echo "⚠️  FastAPI service may not be running, checking logs..."
  sudo journalctl -u fastapi -n 20 --no-pager || true
fi

echo "✅ Backend deployment completed"

# Show final disk usage
echo "💾 Final disk usage:"
df -h / | tail -1
echo ""

# Step 4: Health check
echo "🔍 Step 4: Running health check..."
MAX_ATTEMPTS=20
WAIT_SECONDS=5
API_URL="http://localhost/api/health"

# First check if service is running
echo "🔍 Checking FastAPI service status..."
if sudo systemctl is-active --quiet fastapi; then
  echo "✅ FastAPI service is active"
  sudo systemctl status fastapi --no-pager -l | head -10
else
  echo "❌ FastAPI service is not active"
  echo "📋 Recent service logs:"
  sudo journalctl -u fastapi -n 30 --no-pager || true
  exit 1
fi

for i in $(seq 1 $MAX_ATTEMPTS); do
  echo "📡 Health check attempt $i/$MAX_ATTEMPTS..."
  
  if response=$(curl -s -f "$API_URL" 2>/dev/null); then
    if echo "$response" | grep -q '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
      echo "✅ Health check passed!"
      echo "Response: $response"
      echo ""
      echo "🎉 TEST DEPLOYMENT SUCCESSFUL!"
      exit 0
    else
      echo "⚠️  Service responding but not healthy yet"
      echo "Response: $response"
    fi
  else
    echo "⏳ Service not responding yet (attempt $i/$MAX_ATTEMPTS)"
  fi
  
  if [ $i -lt $MAX_ATTEMPTS ]; then
    sleep $WAIT_SECONDS
  fi
done

echo "❌ Health check failed after $MAX_ATTEMPTS attempts"
echo "📋 Recent service logs:"
sudo journalctl -u fastapi -n 30 --no-pager || true
exit 1

