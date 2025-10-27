#!/bin/bash
# Wait for external services (Redis, DB) to be ready

set -e

wait_for_redis() {
    echo "Waiting for Redis at $REDIS_URL..."
    for i in {1..30}; do
        if redis-cli -u "$REDIS_URL" ping > /dev/null 2>&1; then
            echo "✓ Redis is ready"
            return 0
        fi
        echo "Waiting for Redis... ($i/30)"
        sleep 1
    done
    echo "ERROR: Redis did not become ready in time"
    exit 1
}

# Wait for services
if [ -n "$REDIS_URL" ]; then
    wait_for_redis
fi

echo "All services ready"

