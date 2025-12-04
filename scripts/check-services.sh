#!/bin/bash
# ============================================================================
# Script de Verificação Rápida - TikTrend Finder
# ============================================================================

echo "🔍 Verificando Serviços TikTrend Finder..."
echo "========================================"

# Verificar Docker
echo ""
echo "📦 DOCKER CONTAINERS:"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null

# Verificar APIs
echo ""
echo "🌐 TESTANDO ENDPOINTS:"

echo -n "  API (8000): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
if [ "$response" = "200" ]; then
    echo "✅ OK"
else
    echo "❌ HTTP $response"
fi

echo -n "  Evolution API (8082): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8082/ 2>/dev/null)
if [ "$response" = "200" ] || [ "$response" = "401" ]; then
    echo "✅ OK"
else
    echo "❌ HTTP $response"
fi

echo -n "  Chatwoot (3000): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/ 2>/dev/null)
if [ "$response" = "200" ] || [ "$response" = "302" ]; then
    echo "✅ OK"
else
    echo "❌ HTTP $response"
fi

echo -n "  N8N (5678): "
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5678/ 2>/dev/null)
if [ "$response" = "200" ] || [ "$response" = "302" ]; then
    echo "✅ OK"
else
    echo "❌ HTTP $response"
fi

# Verificar Redis
echo ""
echo -n "  Redis: "
redis_ok=$(redis-cli ping 2>/dev/null)
if [ "$redis_ok" = "PONG" ]; then
    echo "✅ OK"
else
    echo "❌ Não conectado"
fi

# Verificar PostgreSQL
echo ""
echo -n "  PostgreSQL: "
pg_ok=$(docker exec tiktrend-postgres pg_isready -U tiktrend 2>/dev/null | grep -c "accepting")
if [ "$pg_ok" -gt 0 ]; then
    echo "✅ OK"
else
    echo "❌ Não conectado"
fi

echo ""
echo "========================================"
echo "🚀 Para iniciar o frontend: npm run dev"
echo "📖 API Docs: http://localhost:8000/docs"
echo "========================================"
