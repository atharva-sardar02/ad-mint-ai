#!/bin/bash
# macOS-compatible deployment testing script

set -e

echo "🧪 Testing Deployment Pipeline on macOS"
echo "========================================"

# 1. Script syntax validation
echo ""
echo "1. Validating deployment script syntax..."
if bash -n deployment/deploy.sh 2>/dev/null; then
    echo "   ✅ Script syntax: VALID"
else
    echo "   ❌ Script syntax: INVALID"
    exit 1
fi

# 2. Environment files
echo ""
echo "2. Checking environment files..."
[ -f backend/.env.example ] && echo "   ✅ backend/.env.example exists" || echo "   ❌ backend/.env.example MISSING"
[ -f frontend/.env.example ] && echo "   ✅ frontend/.env.example exists" || echo "   ❌ frontend/.env.example MISSING"

# 3. Test path substitution (Nginx)
echo ""
echo "3. Testing Nginx configuration path substitution..."
TEST_PATH="/test/deployment/path"
NGINX_OUTPUT=$(sed "s|/path/to/ad-mint-ai|$TEST_PATH|g" deployment/nginx.conf 2>/dev/null)
if echo "$NGINX_OUTPUT" | grep -q "$TEST_PATH"; then
    echo "   ✅ Nginx path substitution works"
else
    echo "   ❌ Nginx path substitution failed"
fi

# 4. Test path substitution (Systemd service)
echo ""
echo "4. Testing systemd service path substitution..."
SERVICE_OUTPUT=$(sed -e "s|/path/to/ad-mint-ai|$TEST_PATH|g" -e "s|/path/to/venv|$TEST_PATH/backend/venv|g" deployment/fastapi.service 2>/dev/null)
if echo "$SERVICE_OUTPUT" | grep -q "$TEST_PATH"; then
    echo "   ✅ Systemd service path substitution works"
else
    echo "   ❌ Systemd service path substitution failed"
fi

# 5. Validate systemd service structure (manual check)
echo ""
echo "5. Validating systemd service file structure..."
REQUIRED_SECTIONS=("\[Unit\]" "\[Service\]" "\[Install\]")
MISSING_SECTIONS=0
for section in "${REQUIRED_SECTIONS[@]}"; do
    if grep -q "$section" deployment/fastapi.service; then
        echo "   ✅ Found section: $section"
    else
        echo "   ❌ Missing section: $section"
        MISSING_SECTIONS=$((MISSING_SECTIONS + 1))
    fi
done

if grep -q "Restart=always" deployment/fastapi.service; then
    echo "   ✅ Restart=always configured"
else
    echo "   ❌ Restart=always MISSING"
fi

if grep -q "WantedBy=multi-user.target" deployment/fastapi.service; then
    echo "   ✅ WantedBy=multi-user.target configured"
else
    echo "   ❌ WantedBy=multi-user.target MISSING"
fi

# 6. Test Nginx configuration syntax (if nginx installed)
echo ""
echo "6. Testing Nginx configuration syntax..."
if command -v nginx &> /dev/null; then
    # Create temp config with updated paths
    TEMP_CONFIG=$(mktemp)
    CURRENT_DIR=$(pwd)
    sed "s|/path/to/ad-mint-ai|$CURRENT_DIR|g" deployment/nginx.conf > "$TEMP_CONFIG"
    
    # Test syntax (may fail due to missing paths, but syntax should be valid)
    if nginx -t -c "$TEMP_CONFIG" 2>&1 | grep -q "syntax is ok\|test is successful"; then
        echo "   ✅ Nginx configuration syntax: VALID"
    elif nginx -t -c "$TEMP_CONFIG" 2>&1 | grep -q "syntax is ok"; then
        echo "   ✅ Nginx configuration syntax: VALID (warnings about missing files expected)"
    else
        echo "   ⚠️  Nginx config test: Check output (may fail due to missing deployment paths)"
        nginx -t -c "$TEMP_CONFIG" 2>&1 | head -3
    fi
    rm -f "$TEMP_CONFIG"
else
    echo "   ⚠️  Nginx not installed (install via: brew install nginx)"
fi

# 7. Test frontend build
echo ""
echo "7. Testing frontend build process..."
if [ -d frontend ]; then
    cd frontend
    if [ -f package.json ]; then
        if npm run build > /dev/null 2>&1; then
            if [ -d dist ] && [ -f dist/index.html ]; then
                echo "   ✅ Frontend builds successfully"
            else
                echo "   ⚠️  Frontend build completed but dist/ missing"
            fi
        else
            echo "   ⚠️  Frontend build failed (may need: npm install)"
        fi
    else
        echo "   ⚠️  package.json not found"
    fi
    cd ..
else
    echo "   ⚠️  frontend/ directory not found"
fi

# 8. Check error handling in deploy script
echo ""
echo "8. Checking deployment script error handling..."
if grep -q "set -e" deployment/deploy.sh; then
    echo "   ✅ Error handling enabled (set -e)"
else
    echo "   ❌ Error handling MISSING"
fi

if grep -q "error_exit" deployment/deploy.sh; then
    echo "   ✅ Custom error function defined"
else
    echo "   ⚠️  Custom error function not found"
fi

# 9. Verify required files exist
echo ""
echo "9. Verifying required deployment files..."
[ -f deployment/deploy.sh ] && echo "   ✅ deployment/deploy.sh" || echo "   ❌ deployment/deploy.sh MISSING"
[ -f deployment/nginx.conf ] && echo "   ✅ deployment/nginx.conf" || echo "   ❌ deployment/nginx.conf MISSING"
[ -f deployment/fastapi.service ] && echo "   ✅ deployment/fastapi.service" || echo "   ❌ deployment/fastapi.service MISSING"
[ -f deployment/README.md ] && echo "   ✅ deployment/README.md" || echo "   ⚠️  deployment/README.md MISSING"

echo ""
echo "✅ macOS validation complete!"
echo ""
echo "Note: Full deployment testing requires Ubuntu 22.04 environment."
echo "      Use Docker or EC2 instance for complete end-to-end testing."
