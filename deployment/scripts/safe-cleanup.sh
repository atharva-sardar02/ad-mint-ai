#!/bin/bash
# Safe cleanup script that keeps at least one backup for rollback
# Removes old backups but keeps the most recent ones

set -e

DEPLOYMENT_PATH="${1:-/var/www/ad-mint-ai}"
DEPLOYMENT_DIR=$(dirname "$DEPLOYMENT_PATH")

echo "🧹 Starting SAFE disk cleanup (keeping backups for rollback)..."
echo "📁 Deployment path: $DEPLOYMENT_PATH"
echo "📂 Deployment directory: $DEPLOYMENT_DIR"

# Show disk usage before cleanup
echo ""
echo "💾 Disk usage BEFORE cleanup:"
df -h / | tail -1
echo ""

# Keep the current .backup directory (most recent backup)
if [ -d "${DEPLOYMENT_PATH}.backup" ]; then
  BACKUP_SIZE=$(sudo du -sh "${DEPLOYMENT_PATH}.backup" 2>/dev/null | cut -f1 || echo "unknown")
  echo "✅ Keeping current backup: ${DEPLOYMENT_PATH}.backup (size: $BACKUP_SIZE)"
else
  echo "⚠️  No .backup directory found"
fi

# Find all .old-* directories and sort by modification time
# Keep only the most recent one, remove the rest
if [ -d "$DEPLOYMENT_DIR" ]; then
  OLD_BACKUPS=$(sudo find "$DEPLOYMENT_DIR" -maxdepth 1 -type d -name "${DEPLOYMENT_PATH##*/}.old-*" -printf '%T@ %p\n' 2>/dev/null | sort -rn || true)
  
  if [ -n "$OLD_BACKUPS" ]; then
    BACKUP_COUNT=$(echo "$OLD_BACKUPS" | wc -l)
    echo "📊 Found $BACKUP_COUNT old .old-* backup directories"
    
    if [ "$BACKUP_COUNT" -gt 1 ]; then
      echo "🗑️  Keeping most recent, removing $((BACKUP_COUNT - 1)) older ones..."
      KEEP_FIRST=true
      REMOVED_COUNT=0
      TOTAL_FREED=0
      
      echo "$OLD_BACKUPS" | while read -r timestamp dir; do
        if [ "$KEEP_FIRST" = "true" ]; then
          KEPT_SIZE=$(sudo du -sh "$dir" 2>/dev/null | cut -f1 || echo "unknown")
          echo "  ✅ Keeping most recent: $dir (size: $KEPT_SIZE)"
          KEEP_FIRST=false
        else
          DIR_SIZE=$(sudo du -sm "$dir" 2>/dev/null | cut -f1 || echo "0")
          echo "  🗑️  Removing: $dir (size: ${DIR_SIZE}MB)"
          sudo rm -rf "$dir" 2>/dev/null || true
          REMOVED_COUNT=$((REMOVED_COUNT + 1))
          TOTAL_FREED=$((TOTAL_FREED + DIR_SIZE))
        fi
      done
      
      echo "  📊 Removed $REMOVED_COUNT old backups, freed approximately ${TOTAL_FREED}MB"
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

# Clean up pip cache (safe to remove)
echo ""
echo "🧹 Cleaning pip cache..."
pip cache purge 2>/dev/null || true
sudo -H pip cache purge 2>/dev/null || true

# Clean up apt cache (safe to remove)
echo "🧹 Cleaning apt cache..."
sudo apt-get clean 2>/dev/null || true
sudo apt-get autoclean 2>/dev/null || true

# Clean up old logs (keep last 7 days)
echo "🧹 Cleaning old log files (keeping last 7 days)..."
sudo find /var/log -type f -name "*.log" -mtime +7 -delete 2>/dev/null || true
sudo find /var/log -type f -name "*.gz" -mtime +7 -delete 2>/dev/null || true

# Clean up temporary files (safe to remove)
echo "🧹 Cleaning temporary files..."
sudo rm -rf /tmp/* 2>/dev/null || true
sudo rm -rf /var/tmp/* 2>/dev/null || true

# Clean up old journal logs (keep last 7 days)
echo "🧹 Cleaning old journal logs (keeping last 7 days)..."
sudo journalctl --vacuum-time=7d 2>/dev/null || true

# Show disk usage after cleanup
echo ""
echo "💾 Disk usage AFTER cleanup:"
df -h / | tail -1
echo ""

# List remaining backups
echo "📦 Remaining backups (for rollback):"
if [ -d "${DEPLOYMENT_PATH}.backup" ]; then
  echo "  ✅ ${DEPLOYMENT_PATH}.backup"
fi
if [ -n "$OLD_BACKUPS" ]; then
  KEPT_DIR=$(echo "$OLD_BACKUPS" | head -1 | awk '{print $2}')
  if [ -d "$KEPT_DIR" ]; then
    echo "  ✅ $KEPT_DIR"
  fi
fi

echo ""
echo "✅ Safe cleanup completed! At least one backup is preserved for rollback."

