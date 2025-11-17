#!/bin/bash
# Rollback script for FastAPI backend deployment
# Restores the backup directory and restarts the service

set -e

DEPLOYMENT_PATH="${1:-/var/www/ad-mint-ai}"
BACKUP_PATH="${DEPLOYMENT_PATH}.backup"

echo "🔄 Starting rollback process..."
echo "📁 Deployment path: $DEPLOYMENT_PATH"
echo "💾 Backup path: $BACKUP_PATH"

# Check if backup exists
if [ ! -d "$BACKUP_PATH" ]; then
    echo "❌ Backup directory not found: $BACKUP_PATH"
    echo "⚠️  Cannot perform rollback"
    exit 1
fi

echo "✅ Backup found, proceeding with rollback..."

# Stop FastAPI service
echo "🛑 Stopping FastAPI service..."
sudo systemctl stop fastapi || echo "⚠️  Service may already be stopped"

# Remove current deployment (keep .env file if it exists)
if [ -d "$DEPLOYMENT_PATH" ]; then
    echo "🗑️  Removing current deployment..."
    # Backup .env if it exists
    if [ -f "$DEPLOYMENT_PATH/backend/.env" ]; then
        echo "💾 Backing up current .env file..."
        cp "$DEPLOYMENT_PATH/backend/.env" "$DEPLOYMENT_PATH/backend/.env.current"
    fi
    
    # Remove deployment directory
    rm -rf "$DEPLOYMENT_PATH"
fi

# Restore from backup
echo "📦 Restoring from backup..."
cp -r "$BACKUP_PATH" "$DEPLOYMENT_PATH"

# Restore .env file if we backed it up
if [ -f "$DEPLOYMENT_PATH/backend/.env.current" ]; then
    echo "📝 Restoring .env file..."
    mv "$DEPLOYMENT_PATH/backend/.env.current" "$DEPLOYMENT_PATH/backend/.env"
fi

# Ensure proper permissions
echo "🔐 Setting permissions..."
sudo chown -R ubuntu:ubuntu "$DEPLOYMENT_PATH"

# Restart FastAPI service
echo "🚀 Restarting FastAPI service..."
sudo systemctl start fastapi

# Wait a moment for service to start
sleep 5

# Check service status
if sudo systemctl is-active --quiet fastapi; then
    echo "✅ FastAPI service is running"
else
    echo "⚠️  FastAPI service may not be running properly"
    echo "Check status with: sudo systemctl status fastapi"
fi

echo "✅ Rollback completed successfully"
echo "📋 Deployment restored to previous version"

# Clean up old backup directories after successful rollback
echo "🧹 Cleaning up old backup directories..."
DEPLOYMENT_DIR=$(dirname "$DEPLOYMENT_PATH")
if [ -d "$DEPLOYMENT_DIR" ]; then
  # Remove old .old-* directories
  OLD_BACKUPS=$(sudo find "$DEPLOYMENT_DIR" -maxdepth 1 -type d -name "${DEPLOYMENT_PATH##*/}.old-*" 2>/dev/null || true)
  if [ -n "$OLD_BACKUPS" ]; then
    echo "$OLD_BACKUPS" | while read -r dir; do
      if [ -d "$dir" ]; then
        echo "  Removing old backup: $dir"
        sudo rm -rf "$dir"
      fi
    done
  fi
fi

# Show disk usage after cleanup
echo "💾 Disk usage after cleanup:"
df -h / | tail -1

