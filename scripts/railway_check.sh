#!/bin/bash
# =============================================================================
# Railway Health Check Script - Didin Fácil
# =============================================================================
# Uso: ./scripts/railway_check.sh
# =============================================================================

set -e

echo "=========================================="
echo "🚀 Railway Health Check - Didin Fácil"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar Railway CLI
echo "📋 1. Verificando Railway CLI..."
if command -v railway &> /dev/null; then
    echo -e "${GREEN}✅ Railway CLI instalado: $(railway --version)${NC}"
else
    echo -e "${RED}❌ Railway CLI não encontrado. Instale com: npm install -g @railway/cli${NC}"
    exit 1
fi

# Verificar login
echo ""
echo "📋 2. Verificando autenticação..."
if railway whoami &> /dev/null; then
    echo -e "${GREEN}✅ Logado como: $(railway whoami)${NC}"
else
    echo -e "${RED}❌ Não autenticado. Execute: railway login${NC}"
    exit 1
fi

# Verificar projeto linkado
echo ""
echo "📋 3. Verificando projeto linkado..."
if railway status &> /dev/null; then
    echo -e "${GREEN}✅ Projeto linkado${NC}"
else
    echo -e "${YELLOW}⚠️  Projeto não linkado corretamente. Relinkando...${NC}"
    railway link -p didin-facil -e production || true
fi

# Listar variáveis
echo ""
echo "📋 4. Variáveis de ambiente configuradas:"
echo "-------------------------------------------"

# Verificar DATABASE_URL
DB_URL=$(railway variables --json 2>/dev/null | grep -o '"DATABASE_URL":[^,}]*' | head -1 || echo "")
if [[ -n "$DB_URL" ]]; then
    echo -e "${GREEN}✅ DATABASE_URL configurado${NC}"
else
    echo -e "${RED}❌ DATABASE_URL NÃO configurado - Adicione PostgreSQL plugin!${NC}"
fi

# Verificar REDIS_URL
REDIS_URL=$(railway variables --json 2>/dev/null | grep -o '"REDIS_URL":[^,}]*' | head -1 || echo "")
if [[ -n "$REDIS_URL" ]]; then
    echo -e "${GREEN}✅ REDIS_URL configurado${NC}"
else
    echo -e "${RED}❌ REDIS_URL NÃO configurado${NC}"
fi

# Verificar JWT_SECRET_KEY
JWT=$(railway variables --json 2>/dev/null | grep -o '"JWT_SECRET_KEY":[^,}]*' | head -1 || echo "")
if [[ -n "$JWT" ]]; then
    echo -e "${GREEN}✅ JWT_SECRET_KEY configurado${NC}"
else
    echo -e "${YELLOW}⚠️  JWT_SECRET_KEY não encontrado - Gere com: openssl rand -hex 32${NC}"
fi

# Verificar OPENAI_API_KEY
OPENAI=$(railway variables --json 2>/dev/null | grep -o '"OPENAI_API_KEY":[^,}]*' | head -1 || echo "")
if [[ -n "$OPENAI" ]]; then
    echo -e "${GREEN}✅ OPENAI_API_KEY configurado${NC}"
else
    echo -e "${YELLOW}⚠️  OPENAI_API_KEY não configurado (opcional)${NC}"
fi

echo ""
echo "=========================================="
echo "📊 5. Testando conexões em produção..."
echo "=========================================="

# Testar Database
echo ""
echo "🗄️  Testando PostgreSQL..."
railway run --service ticktrend -- python3 -c "
import asyncio
import os

async def test_db():
    try:
        import asyncpg
        url = os.environ.get('DATABASE_URL', '').replace('postgres://', 'postgresql://')
        if not url:
            print('❌ DATABASE_URL não definido')
            return
        conn = await asyncpg.connect(url)
        version = await conn.fetchval('SELECT version()')
        tables = await conn.fetch(\"SELECT tablename FROM pg_tables WHERE schemaname = 'public'\")
        print(f'✅ PostgreSQL conectado')
        print(f'   Versão: {version[:50]}...')
        print(f'   Tabelas: {len(tables)} encontradas')
        await conn.close()
    except Exception as e:
        print(f'❌ Erro PostgreSQL: {e}')

asyncio.run(test_db())
" 2>/dev/null || echo -e "${YELLOW}⚠️  Não foi possível testar banco (serviço pode estar parado)${NC}"

# Testar Redis
echo ""
echo "📦 Testando Redis..."
railway run --service ticktrend -- python3 -c "
import asyncio
import os

async def test_redis():
    try:
        from redis.asyncio import Redis
        url = os.environ.get('REDIS_URL', '')
        if not url:
            print('❌ REDIS_URL não definido')
            return
        r = Redis.from_url(url)
        await r.ping()
        info = await r.info('memory')
        print(f'✅ Redis conectado')
        print(f'   Memória usada: {info.get(\"used_memory_human\", \"N/A\")}')
        await r.close()
    except Exception as e:
        print(f'❌ Erro Redis: {e}')

asyncio.run(test_redis())
" 2>/dev/null || echo -e "${YELLOW}⚠️  Não foi possível testar Redis${NC}"

echo ""
echo "=========================================="
echo "🔍 6. Verificando configurações locais..."
echo "=========================================="

# Verificar railway.toml
if [[ -f "railway.toml" ]]; then
    echo -e "${GREEN}✅ railway.toml encontrado${NC}"
    TIMEOUT=$(grep "healthcheckTimeout" railway.toml | grep -o '[0-9]*')
    if [[ "$TIMEOUT" -gt 180 ]]; then
        echo -e "${YELLOW}   ⚠️  healthcheckTimeout=${TIMEOUT}s (recomendado: 60-120s)${NC}"
    else
        echo -e "${GREEN}   ✅ healthcheckTimeout=${TIMEOUT}s${NC}"
    fi
else
    echo -e "${RED}❌ railway.toml não encontrado${NC}"
fi

# Verificar nixpacks.toml
if [[ -f "nixpacks.toml" ]]; then
    echo -e "${GREEN}✅ nixpacks.toml encontrado${NC}"
else
    echo -e "${RED}❌ nixpacks.toml não encontrado${NC}"
fi

# Verificar .gitignore
if grep -q "_railway_info.txt" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ _railway_info.txt no .gitignore (seguro)${NC}"
else
    echo -e "${RED}❌ _railway_info.txt NÃO está no .gitignore (RISCO DE SEGURANÇA!)${NC}"
    echo "   Execute: echo '_railway_info.txt' >> .gitignore"
fi

echo ""
echo "=========================================="
echo "📝 7. Checklist de ações recomendadas:"
echo "=========================================="
echo ""
echo "Se houver problemas, execute:"
echo ""
echo "  1. Adicionar PostgreSQL:"
echo "     railway add --plugin postgresql"
echo ""
echo "  2. Gerar JWT_SECRET_KEY:"
echo "     openssl rand -hex 32"
echo "     railway variables set JWT_SECRET_KEY=<valor_gerado>"
echo ""
echo "  3. Rodar migrations manualmente:"
echo "     railway run --service ticktrend -- alembic upgrade head"
echo ""
echo "  4. Ver logs do backend:"
echo "     railway logs --service ticktrend"
echo ""
echo "=========================================="
echo "✅ Health check concluído!"
echo "=========================================="
