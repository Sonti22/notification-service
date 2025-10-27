#!/bin/bash
# Local development startup script

set -e

echo "=== Notification Service - Local Startup ==="

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo "ERROR: Redis is not running. Start with 'redis-server' or 'docker run -d -p 6379:6379 redis:7-alpine'"
    exit 1
fi

echo "✓ Redis is running"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt

# Initialize database
echo "Initializing database..."
python -m src.database

# Start API server
echo "Starting API server on http://localhost:8000..."
echo "Docs available at http://localhost:8000/docs"
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

