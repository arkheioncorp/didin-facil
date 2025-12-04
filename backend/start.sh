#!/bin/bash
set -e

echo "🚀 Starting deployment script..."
echo "📍 Current directory: $(pwd)"
echo "🔌 PORT: $PORT"

# Check DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL is not set!"
    exit 1
else
    echo "✅ DATABASE_URL is configured"
fi

# Check REDIS_URL
if [ -z "$REDIS_URL" ]; then
    echo "⚠️ REDIS_URL not set, using default"
else
    echo "✅ REDIS_URL is configured"
fi

# Test database connection
echo "🔍 Testing database connection..."
python3 -c "
import asyncio
import asyncpg
import os

async def test_db():
    url = os.environ.get('DATABASE_URL', '').replace('postgresql://', 'postgres://')
    try:
        conn = await asyncpg.connect(url)
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print(f'✅ Database connection successful: {result}')
        return True
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        return False

success = asyncio.run(test_db())
exit(0 if success else 1)
" || echo "⚠️ Database test failed, continuing anyway..."

# Run database migrations
echo "📦 Running database migrations..."
echo "📍 Alembic config check:"
python3 -c "
from shared.config import settings
print(f'DATABASE_URL set: {bool(settings.DATABASE_URL)}')
print(f'URL preview: {settings.DATABASE_URL[:50]}...' if settings.DATABASE_URL else 'NOT SET')
"

# Run migrations with full output
echo "🔄 Executing: alembic upgrade head"
alembic upgrade head 2>&1 || {
    echo "❌ Migration failed! Checking tables..."
    python3 -c "
import asyncio
import asyncpg
import os

async def check_tables():
    url = os.environ.get('DATABASE_URL', '')
    try:
        conn = await asyncpg.connect(url)
        tables = await conn.fetch(\"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\")
        print(f'Existing tables: {[t[\"tablename\"] for t in tables]}')
        await conn.close()
    except Exception as e:
        print(f'Error checking tables: {e}')

asyncio.run(check_tables())
"
    echo "⚠️ Continuing despite migration error..."
}

# List applied migrations
echo "📋 Current migration status:"
alembic current 2>&1 || echo "Could not check migration status"

# Start application
echo "🔌 Starting application on port $PORT..."
exec python3 -m uvicorn api.main:app --host 0.0.0.0 --port $PORT
