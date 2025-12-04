#!/bin/bash
set -e

echo "🚀 Starting deployment script..."

# Run database migrations
echo "📦 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations applied successfully"
else
    echo "❌ Failed to apply migrations"
    exit 1
fi

# Start application
echo "🔌 Starting application on port $PORT..."
python3 -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
