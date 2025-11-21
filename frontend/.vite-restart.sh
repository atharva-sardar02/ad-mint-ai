#!/bin/bash
# Stop any running Vite processes
pkill -f "vite" || true

# Clear all caches
rm -rf node_modules/.vite
rm -rf dist
rm -rf .turbo

# Restart Vite
npm run dev
