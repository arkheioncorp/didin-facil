#!/bin/bash
# ============================================================================
# Setup Script - Didin Fácil Integrations
# ============================================================================
# Este script configura todas as integrações do sistema
# Uso: ./scripts/setup-integrations.sh
# ============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "=============================================="
echo "   Didin Fácil - Setup de Integrações"
echo "=============================================="
echo -e "${NC}"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker não encontrado. Instale o Docker primeiro.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose não encontrado.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker e Docker Compose encontrados${NC}"

# Create data directories
echo -e "\n${YELLOW}📁 Criando diretórios de dados...${NC}"
mkdir -p backend/data/youtube_tokens
mkdir -p backend/data/tiktok_sessions
mkdir -p backend/data/instagram_sessions
mkdir -p backend/data/temp_uploads

# Create .env file if not exists
if [ ! -f "backend/.env" ]; then
    echo -e "\n${YELLOW}📝 Criando arquivo .env...${NC}"
    cat > backend/.env << 'EOF'
# ============================================================================
# Didin Fácil - Environment Variables
# ============================================================================

# Environment
ENVIRONMENT=development
DEBUG=true

# Database
DATABASE_URL=postgresql://tiktrend:tiktrend_dev@localhost:5434/tiktrend

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=change-this-to-a-secure-random-string

# OpenAI (para geração de copies)
OPENAI_API_KEY=

# Mercado Pago (para pagamentos)
MERCADO_PAGO_ACCESS_TOKEN=
MERCADO_PAGO_WEBHOOK_SECRET=

# Evolution API (WhatsApp)
EVOLUTION_API_URL=http://localhost:8082
EVOLUTION_API_KEY=429683C4C977415CAAFCCE10F7D57E11

# Chatwoot (Customer Support)
CHATWOOT_API_URL=http://localhost:3000
CHATWOOT_ACCESS_TOKEN=
CHATWOOT_ACCOUNT_ID=1

# YouTube OAuth (configure no Google Cloud Console)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Instagram (credenciais da conta para automação)
INSTAGRAM_USERNAME=
INSTAGRAM_PASSWORD=

# Data Directory
DATA_DIR=data

# CORS
CORS_ORIGINS=http://localhost:1420,http://localhost:5173,tauri://localhost
EOF
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
else
    echo -e "${GREEN}✅ Arquivo .env já existe${NC}"
fi

# Start services
echo -e "\n${YELLOW}🐳 Iniciando serviços Docker...${NC}"
cd docker

# Start core services first
echo -e "${BLUE}Iniciando PostgreSQL e Redis...${NC}"
docker compose up -d postgres redis

# Wait for database
echo -e "${BLUE}Aguardando banco de dados...${NC}"
sleep 10

# Start Evolution API
echo -e "${BLUE}Iniciando Evolution API (WhatsApp)...${NC}"
docker compose up -d evolution-api

# Start API
echo -e "${BLUE}Iniciando API FastAPI...${NC}"
docker compose up -d api

echo -e "\n${GREEN}=============================================="
echo "   ✅ Serviços Iniciados!"
echo "==============================================${NC}"

echo -e "\n${BLUE}URLs disponíveis:${NC}"
echo "  📡 API:              http://localhost:8000"
echo "  📡 API Docs:         http://localhost:8000/docs"
echo "  📱 Evolution API:    http://localhost:8082"
echo "  🗄️ PostgreSQL:       localhost:5434"
echo "  📦 Redis:            localhost:6379"

echo -e "\n${YELLOW}Próximos passos:${NC}"
echo "  1. Configure as variáveis em backend/.env"
echo "  2. Acesse http://localhost:8000/docs para testar a API"
echo "  3. Configure o WhatsApp em Settings > Integrações"
echo "  4. Configure o YouTube OAuth (veja docs/YOUTUBE-SETUP.md)"

echo -e "\n${BLUE}Para parar os serviços:${NC}"
echo "  cd docker && docker compose down"

echo -e "\n${GREEN}Done! 🚀${NC}"
