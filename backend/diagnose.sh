#!/bin/bash
# Script de diagnóstico das integrações

echo "============================================================"
echo "DIAGNÓSTICO DAS INTEGRAÇÕES - SELLER BOT"
echo "============================================================"

echo ""
echo "[1/7] Status dos containers Docker..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>&1

echo ""
echo "[2/7] Testando n8n..."
curl -s http://localhost:5678/healthz 2>&1 || echo "FALHOU"

echo ""
echo "[3/7] Testando Chatwoot..."
curl -s http://localhost:3000/api | head -c 100 2>&1 || echo "FALHOU"

echo ""
echo "[4/7] Testando Evolution API..."
curl -s http://localhost:8082/ 2>&1 | head -c 200 || echo "FALHOU"

echo ""
echo "[5/7] Testando Backend API..."
curl -s http://localhost:8000/health 2>&1 || echo "SEM RESPOSTA"

echo ""
echo "[6/7] Logs da API (últimas 20 linhas)..."
docker logs tiktrend-api --tail 20 2>&1

echo ""
echo "[7/7] Testando imports Python..."
cd /home/jhonslife/"Didin Facil"/backend
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from modules.chatbot import ProfessionalSellerBot
    print('✅ chatbot OK')
except Exception as e:
    print(f'❌ chatbot: {e}')
try:
    from api.routes.seller_bot import router
    print('✅ seller_bot router OK')
except Exception as e:
    print(f'❌ seller_bot: {e}')
" 2>&1

echo ""
echo "============================================================"
echo "DIAGNÓSTICO COMPLETO"
echo "============================================================"
