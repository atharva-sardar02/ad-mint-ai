#!/bin/bash
# Deployment script for Ad Mint AI
# This script handles deployment of the application to an EC2 instance
#
# Usage:
#   ./deploy.sh [deployment_path]
#
# Arguments:
#   deployment_path: Base directory where the application is deployed (default: /var/www/ad-mint-ai)
#
# Prerequisites:
#   - Running on Ubuntu 22.04 LTS
#   - Script must be run with sudo privileges
#   - Repository cloned to deployment_path
#   - Environment variables configured in .env files

set -e  # Exit on any error

# Configuration
DEPLOYMENT_PATH=${1:-/var/www/ad-mint-ai}
PROJECT_NAME="ad-mint-ai"
NGINX_SITE_NAME="ad-mint-ai"
SERVICE_NAME="fastapi"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error handling function
error_exit() {
    echo -e "${RED}❌ Error: $1${NC}" >&2
    exit 1
}

# Success message function
success_msg() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Info message function
info_msg() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    error_exit "This script must be run with sudo privileges"
fi

echo "🚀 Starting deployment for Ad Mint AI"
echo "📁 Deployment path: $DEPLOYMENT_PATH"

# Verify deployment path exists
if [ ! -d "$DEPLOYMENT_PATH" ]; then
    error_exit "Deployment path does not exist: $DEPLOYMENT_PATH"
fi

cd "$DEPLOYMENT_PATH" || error_exit "Failed to change to deployment directory"

# Step 1: Install system dependencies
info_msg "Installing system dependencies..."
export DEBIAN_FRONTEND=noninteractive

# Update package list
apt-get update -qq || error_exit "Failed to update package list"

# Install Python 3.11
if ! command -v python3.11 &> /dev/null; then
    info_msg "Installing Python 3.11..."
    apt-get install -y -qq python3.11 python3.11-venv python3.11-dev python3-pip || error_exit "Failed to install Python 3.11"
else
    success_msg "Python 3.11 already installed"
fi

# Install Node.js 18+
if ! command -v node &> /dev/null || [ "$(node -v | cut -d'v' -f2 | cut -d'.' -f1)" -lt 18 ]; then
    info_msg "Installing Node.js 18+..."
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash - || error_exit "Failed to add Node.js repository"
    apt-get install -y -qq nodejs || error_exit "Failed to install Node.js"
else
    success_msg "Node.js $(node -v) already installed"
fi

# Install FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    info_msg "Installing FFmpeg..."
    apt-get install -y -qq ffmpeg || error_exit "Failed to install FFmpeg"
else
    success_msg "FFmpeg already installed"
fi

# Install Nginx
if ! command -v nginx &> /dev/null; then
    info_msg "Installing Nginx..."
    apt-get install -y -qq nginx || error_exit "Failed to install Nginx"
else
    success_msg "Nginx already installed"
fi

success_msg "System dependencies installed"

# Step 2: Set up Python virtual environment
info_msg "Setting up Python virtual environment..."
BACKEND_DIR="$DEPLOYMENT_PATH/backend"
VENV_PATH="$BACKEND_DIR/venv"

if [ ! -d "$VENV_PATH" ]; then
    info_msg "Creating virtual environment..."
    python3.11 -m venv "$VENV_PATH" || error_exit "Failed to create virtual environment"
    success_msg "Virtual environment created"
else
    success_msg "Virtual environment already exists"
fi

# Step 3: Install Python dependencies
info_msg "Installing Python dependencies..."
source "$VENV_PATH/bin/activate"
pip install --upgrade pip -q || error_exit "Failed to upgrade pip"
pip install -r "$BACKEND_DIR/requirements.txt" -q || error_exit "Failed to install Python dependencies"
deactivate
success_msg "Python dependencies installed"

# Step 4: Build React frontend
info_msg "Building React frontend..."
FRONTEND_DIR="$DEPLOYMENT_PATH/frontend"
cd "$FRONTEND_DIR" || error_exit "Failed to change to frontend directory"

# Install npm dependencies
npm install --silent || error_exit "Failed to install npm dependencies"

# Build frontend
npm run build || error_exit "Failed to build frontend"

if [ ! -d "$FRONTEND_DIR/dist" ]; then
    error_exit "Frontend build failed: dist directory not found"
fi

success_msg "Frontend built successfully"
cd "$DEPLOYMENT_PATH" || error_exit "Failed to return to deployment directory"

# Step 5: Copy Nginx configuration
info_msg "Configuring Nginx..."
NGINX_CONFIG_SOURCE="$DEPLOYMENT_PATH/deployment/nginx.conf"
NGINX_CONFIG_DEST="/etc/nginx/sites-available/$NGINX_SITE_NAME"

if [ ! -f "$NGINX_CONFIG_SOURCE" ]; then
    error_exit "Nginx configuration file not found: $NGINX_CONFIG_SOURCE"
fi

# Update nginx.conf with actual deployment path before copying
sed -i "s|/path/to/ad-mint-ai|$DEPLOYMENT_PATH|g" "$NGINX_CONFIG_SOURCE" || error_exit "Failed to update Nginx configuration paths"

cp "$NGINX_CONFIG_SOURCE" "$NGINX_CONFIG_DEST" || error_exit "Failed to copy Nginx configuration"
success_msg "Nginx configuration copied to $NGINX_CONFIG_DEST"

# Step 6: Create symlink for Nginx site
info_msg "Enabling Nginx site..."
NGINX_ENABLED="/etc/nginx/sites-enabled/$NGINX_SITE_NAME"

# Remove existing symlink if it exists
if [ -L "$NGINX_ENABLED" ]; then
    rm "$NGINX_ENABLED"
fi

# Create new symlink
ln -s "$NGINX_CONFIG_DEST" "$NGINX_ENABLED" || error_exit "Failed to create Nginx symlink"
success_msg "Nginx site enabled"

# Test Nginx configuration
info_msg "Testing Nginx configuration..."
nginx -t || error_exit "Nginx configuration test failed"

# Step 7: Create temp directory for MoviePy and other temporary files
info_msg "Creating temp directory for application..."
TEMP_DIR="$BACKEND_DIR/tmp"
mkdir -p "$TEMP_DIR" || error_exit "Failed to create temp directory"
chown www-data:www-data "$TEMP_DIR" || error_exit "Failed to set temp directory ownership"
chmod 755 "$TEMP_DIR" || error_exit "Failed to set temp directory permissions"
success_msg "Temp directory created: $TEMP_DIR"

# Step 8: Copy systemd service file
info_msg "Configuring systemd service..."
SERVICE_SOURCE="$DEPLOYMENT_PATH/deployment/fastapi.service"
SERVICE_DEST="/etc/systemd/system/${SERVICE_NAME}.service"

if [ ! -f "$SERVICE_SOURCE" ]; then
    error_exit "Systemd service file not found: $SERVICE_SOURCE"
fi

# Update service file with actual paths before copying
sed -i "s|/path/to/ad-mint-ai|$DEPLOYMENT_PATH|g" "$SERVICE_SOURCE"
sed -i "s|/path/to/venv|$VENV_PATH|g" "$SERVICE_SOURCE"

cp "$SERVICE_SOURCE" "$SERVICE_DEST" || error_exit "Failed to copy systemd service file"
success_msg "Systemd service file copied to $SERVICE_DEST"

# Step 9: Reload systemd and enable/start services
info_msg "Reloading systemd daemon..."
systemctl daemon-reload || error_exit "Failed to reload systemd daemon"
success_msg "Systemd daemon reloaded"

# Enable and start FastAPI service
info_msg "Enabling and starting FastAPI service..."
systemctl enable "${SERVICE_NAME}.service" || error_exit "Failed to enable FastAPI service"
systemctl restart "${SERVICE_NAME}.service" || error_exit "Failed to start FastAPI service"
success_msg "FastAPI service enabled and started"

# Reload Nginx
info_msg "Reloading Nginx..."
systemctl reload nginx || error_exit "Failed to reload Nginx"
success_msg "Nginx reloaded"

# Step 10: Run database initialization
info_msg "Initializing database..."
cd "$BACKEND_DIR" || error_exit "Failed to change to backend directory"
source "$VENV_PATH/bin/activate"
python -m app.db.init_db || error_exit "Failed to initialize database"
deactivate
success_msg "Database initialized"
cd "$DEPLOYMENT_PATH" || error_exit "Failed to return to deployment directory"

# Step 11: Verification steps
info_msg "Running verification steps..."

# Check FastAPI service status
if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
    success_msg "FastAPI service is running"
else
    error_exit "FastAPI service is not running"
fi

# Check Nginx status
if systemctl is-active --quiet nginx; then
    success_msg "Nginx service is running"
else
    error_exit "Nginx service is not running"
fi

# Test health endpoint
info_msg "Testing health endpoint..."
sleep 2  # Give service a moment to fully start
HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/health || echo "000")

if [ "$HEALTH_RESPONSE" = "200" ]; then
    success_msg "Health endpoint returned 200 OK"
else
    error_exit "Health endpoint test failed (HTTP $HEALTH_RESPONSE)"
fi

# Verify frontend files exist
if [ -d "$FRONTEND_DIR/dist" ] && [ -f "$FRONTEND_DIR/dist/index.html" ]; then
    success_msg "Frontend build files verified"
else
    error_exit "Frontend build files not found"
fi

echo ""
success_msg "Deployment completed successfully!"
echo ""
info_msg "Service Status:"
echo "  - FastAPI: $(systemctl is-active ${SERVICE_NAME}.service)"
echo "  - Nginx: $(systemctl is-active nginx)"
echo ""
info_msg "Next steps:"
echo "  - Verify application is accessible at your domain/IP"
echo "  - Check logs: sudo journalctl -u ${SERVICE_NAME} -f"
echo "  - View Nginx logs: sudo tail -f /var/log/nginx/error.log"

