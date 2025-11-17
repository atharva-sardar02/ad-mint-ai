#!/bin/bash
# Cleanup script to free disk space on EC2 instance
# Removes old backups, caches, and temporary files

set -e

DEPLOYMENT_PATH="${1:-/var/www/ad-mint-ai}"
DEPLOYMENT_DIR=$(dirname "$DEPLOYMENT_PATH")

echo "🧹 Starting disk cleanup..."
echo "📁 Deployment path: $DEPLOYMENT_PATH"
echo "📂 Deployment directory: $DEPLOYMENT_DIR"

# Show disk usage before cleanup
echo ""
echo "💾 Disk usage BEFORE cleanup:"
df -h / | tail -1
echo ""

# Remove old backup directories (keep the most recent .backup and .old-*)
if [ -d "$DEPLOYMENT_DIR" ]; then
  # Keep the current .backup directory (most recent backup)
  if [ -d "${DEPLOYMENT_PATH}.backup" ]; then
    BACKUP_SIZE=$(sudo du -sh "${DEPLOYMENT_PATH}.backup" 2>/dev/null | cut -f1 || echo "unknown")
    echo "✅ Keeping current backup: ${DEPLOYMENT_PATH}.backup (size: $BACKUP_SIZE)"
  else
    echo "⚠️  No .backup directory found"
  fi
  
  # Find all .old-* directories and sort by modification time
  # Keep only the most recent one, remove the rest
  OLD_BACKUPS=$(sudo find "$DEPLOYMENT_DIR" -maxdepth 1 -type d -name "${DEPLOYMENT_PATH##*/}.old-*" -printf '%T@ %p\n' 2>/dev/null | sort -rn || true)
  
  if [ -n "$OLD_BACKUPS" ]; then
    BACKUP_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
    if [ "$BACKUP_COUNT" -gt 1 ]; then
      echo "🗑️  Found $BACKUP_COUNT old .old-* directories, keeping most recent, removing others..."
      KEEP_FIRST=true
      echo "$OLD_BACKUPS" | while read -r timestamp dir; do
        if [ "$KEEP_FIRST" = "true" ]; then
          KEPT_SIZE=$(sudo du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
          echo "  ✅ Keeping most recent: $dir (size: $KEPT_SIZE)"
          KEEP_FIRST=false
        else
          echo "  🗑️  Removing: $dir"
          sudo rm -rf "$dir" 2>/dev/null || true
        fi
      done
    else
      # Only one .old-* directory, keep it
      KEPT_DIR=$(echo "$OLD_BACKUPS" | awk '{print $2}')
      KEPT_SIZE=$(sudo du -sh "$KEPT_DIR" 2>/dev/null | cut -f1 || echo "unknown")
      echo "✅ Keeping only .old-* backup: $KEPT_DIR (size: $KEPT_SIZE)"
    fi
  else
    echo "ℹ️  No old .old-* directories found"
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

# Clean up old logs (keep last 7 days)
echo "🧹 Cleaning old log files..."
sudo find /var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
sudo find /var/log -type f -name "*.gz" -mtime +7 -delete 2>/dev/null || true

# Clean up temporary files
echo "🧹 Cleaning temporary files..."
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# Clean up old journal logs
echo "🧹 Cleaning old journal logs..."
sudo journalctl --vacuum-time=7d 2>/dev/null || true

# Show disk usage after cleanup
echo ""
echo "💾 Disk usage AFTER cleanup:"
df -h / | tail -1
echo ""

echo "✅ Disk cleanup completed!"

