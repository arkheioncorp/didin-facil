#!/bin/bash
# Quick Railway Status Check
# Execute: bash scripts/quick_railway_check.sh

echo "=== RAILWAY STATUS ==="
echo ""

echo "1. Verificando CLI..."
railway --version || echo "❌ Railway CLI não encontrado"

echo ""
echo "2. Verificando login..."
railway whoami || echo "❌ Não autenticado - execute: railway login"

echo ""
echo "3. Verificando projeto..."
railway status || echo "❌ Projeto não linkado"

echo ""
echo "4. Listando variáveis críticas..."
railway variables 2>/dev/null | grep -E "DATABASE_URL|REDIS_URL|JWT_SECRET" || echo "⚠️ Execute: railway link -p tiktrend-facil"

echo ""
echo "5. Verificando serviços..."
railway service list 2>/dev/null || echo "⚠️ Não foi possível listar serviços"

echo ""
echo "=== FIM ==="
