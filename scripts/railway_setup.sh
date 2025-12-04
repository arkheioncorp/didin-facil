#!/bin/bash
# =============================================================================
# Railway Setup Script - TikTrend Finder
# =============================================================================
# Script para configurar o ambiente Railway do zero
# Uso: ./scripts/railway_setup.sh
# =============================================================================

set -e

echo "=========================================="
echo "🚀 Railway Setup - TikTrend Finder"
echo "=========================================="
echo ""

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Verificar se está no diretório correto
if [[ ! -f "railway.toml" ]]; then
    echo -e "${RED}❌ Execute este script na raiz do projeto!${NC}"
    exit 1
fi

# 1. Verificar Railway CLI
echo -e "${BLUE}📋 1. Verificando Railway CLI...${NC}"
if ! command -v railway &> /dev/null; then
    echo "Instalando Railway CLI..."
    npm install -g @railway/cli
fi
echo -e "${GREEN}✅ Railway CLI OK${NC}"

# 2. Login
echo ""
echo -e "${BLUE}📋 2. Verificando autenticação...${NC}"
if ! railway whoami &> /dev/null; then
    echo "Fazendo login..."
    railway login
fi
echo -e "${GREEN}✅ Autenticado como: $(railway whoami)${NC}"

# 3. Linkar projeto
echo ""
echo -e "${BLUE}📋 3. Linkando projeto...${NC}"
railway link -p tiktrend-facil -e production 2>/dev/null || railway link
echo -e "${GREEN}✅ Projeto linkado${NC}"

# 4. Verificar/Adicionar PostgreSQL
echo ""
echo -e "${BLUE}📋 4. Verificando PostgreSQL...${NC}"
DB_URL=$(railway variables --json 2>/dev/null | grep -o '"DATABASE_URL"' || echo "")
if [[ -z "$DB_URL" ]]; then
    echo -e "${YELLOW}⚠️  PostgreSQL não encontrado. Adicionando...${NC}"
    echo ""
    echo "Por favor, adicione PostgreSQL manualmente no dashboard do Railway:"
    echo "  1. Acesse: https://railway.app/project/2033403f-9f00-47b6-a01d-488592416b18"
    echo "  2. Clique em '+ New' → 'Database' → 'PostgreSQL'"
    echo "  3. Configure as variáveis compartilhadas entre serviços"
    echo ""
    read -p "Pressione ENTER quando PostgreSQL estiver configurado..."
else
    echo -e "${GREEN}✅ PostgreSQL já configurado${NC}"
fi

# 5. Gerar e configurar JWT_SECRET_KEY
echo ""
echo -e "${BLUE}📋 5. Verificando JWT_SECRET_KEY...${NC}"
JWT=$(railway variables --json 2>/dev/null | grep '"JWT_SECRET_KEY"' || echo "")
if [[ -z "$JWT" ]] || [[ "$JWT" == *"dev-secret"* ]] || [[ "$JWT" == *"CHANGE_ME"* ]]; then
    echo -e "${YELLOW}⚠️  JWT_SECRET_KEY precisa ser configurado${NC}"
    NEW_JWT=$(openssl rand -hex 32)
    echo "Novo JWT gerado: $NEW_JWT"
    read -p "Deseja configurar este JWT no Railway? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        railway variables set JWT_SECRET_KEY="$NEW_JWT"
        echo -e "${GREEN}✅ JWT_SECRET_KEY configurado${NC}"
    fi
else
    echo -e "${GREEN}✅ JWT_SECRET_KEY já configurado${NC}"
fi

# 6. Variáveis opcionais
echo ""
echo -e "${BLUE}📋 6. Variáveis opcionais...${NC}"

# CORS
CORS=$(railway variables --json 2>/dev/null | grep '"CORS_ORIGINS"' || echo "")
if [[ -z "$CORS" ]]; then
    echo "Configurando CORS_ORIGINS padrão..."
    railway variables set CORS_ORIGINS="https://tiktrend-facil.vercel.app,https://tiktrend.com.br,http://localhost:1420"
    echo -e "${GREEN}✅ CORS_ORIGINS configurado${NC}"
fi

# ENVIRONMENT
ENV=$(railway variables --json 2>/dev/null | grep '"ENVIRONMENT"' || echo "")
if [[ -z "$ENV" ]]; then
    railway variables set ENVIRONMENT="production"
    echo -e "${GREEN}✅ ENVIRONMENT=production configurado${NC}"
fi

# 7. Mostrar resumo
echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Setup concluído!${NC}"
echo "=========================================="
echo ""
echo "Próximos passos:"
echo ""
echo "  1. Verificar deploy:"
echo "     railway logs --service ticktrend"
echo ""
echo "  2. Rodar migrations (se necessário):"
echo "     railway run --service ticktrend -- cd backend && alembic upgrade head"
echo ""
echo "  3. Abrir dashboard:"
echo "     railway open"
echo ""
echo "  4. Verificar saúde:"
echo "     ./scripts/railway_check.sh"
echo ""
