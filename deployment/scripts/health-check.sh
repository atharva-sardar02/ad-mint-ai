#!/bin/bash
# Health check script for FastAPI backend
# Polls the health endpoint until it returns healthy or timeout is reached

set -e

API_URL="${1:-http://localhost:8000/api/health}"
MAX_ATTEMPTS="${2:-12}"
WAIT_SECONDS="${3:-5}"

echo "🔍 Starting health check for: $API_URL"
echo "⏱️  Max attempts: $MAX_ATTEMPTS (${WAIT_SECONDS}s between attempts)"

for i in $(seq 1 $MAX_ATTEMPTS); do
    echo "📡 Attempt $i/$MAX_ATTEMPTS..."
    
    # Try to get health status
    if response=$(curl -s -f "$API_URL" 2>/dev/null); then
        # Check if response contains "healthy" status
        if echo "$response" | grep -q '"status"[[:space:]]*:[[:space:]]*"healthy"'; then
            echo "✅ Health check passed!"
            echo "Response: $response"
            exit 0
        else
            echo "⚠️  Service responding but not healthy yet"
            echo "Response: $response"
        fi
    else
        echo "⏳ Service not responding yet (attempt $i/$MAX_ATTEMPTS)"
    fi
    
    # Wait before next attempt (except on last attempt)
    if [ $i -lt $MAX_ATTEMPTS ]; then
        sleep $WAIT_SECONDS
    fi
done

echo "❌ Health check failed after $MAX_ATTEMPTS attempts"
echo "Service at $API_URL is not healthy"
exit 1

