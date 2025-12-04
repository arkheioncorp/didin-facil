#!/bin/bash
# ============================================================================
# Script de Teste de Uploads - TikTrend Finder
# ============================================================================
# Testa todas as integrações de upload (WhatsApp, YouTube, Instagram, TikTok)
# Uso: ./scripts/test-uploads.sh
# ============================================================================

set -e

API_URL="${API_URL:-http://localhost:8000}"
API_TOKEN="${API_TOKEN:-}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "=============================================="
echo "   TikTrend Finder - Teste de Uploads"
echo "=============================================="
echo -e "${NC}"

# Check if API is running
echo -e "${YELLOW}🔍 Verificando API...${NC}"
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${RED}❌ API não está rodando em $API_URL${NC}"
    echo "   Execute: cd backend && uvicorn api.main:app --reload"
    exit 1
fi
echo -e "${GREEN}✅ API está online${NC}"

# Function to make API calls
api_call() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    if [ -n "$API_TOKEN" ]; then
        if [ -n "$data" ]; then
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Authorization: Bearer $API_TOKEN" \
                -H "Content-Type: application/json" \
                -d "$data"
        else
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Authorization: Bearer $API_TOKEN"
        fi
    else
        if [ -n "$data" ]; then
            curl -s -X "$method" "$API_URL$endpoint" \
                -H "Content-Type: application/json" \
                -d "$data"
        else
            curl -s -X "$method" "$API_URL$endpoint"
        fi
    fi
}

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}1. TESTE WHATSAPP (Evolution API)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Check Evolution API
EVOLUTION_URL="${EVOLUTION_API_URL:-http://localhost:8082}"
echo -e "${YELLOW}📱 Verificando Evolution API...${NC}"

if curl -s "$EVOLUTION_URL" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Evolution API online${NC}"
    
    # List instances
    echo -e "${YELLOW}   Listando instâncias...${NC}"
    response=$(api_call GET "/whatsapp/instances")
    echo "   $response" | head -c 200
else
    echo -e "${YELLOW}⚠️  Evolution API offline (opcional)${NC}"
fi

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}2. TESTE YOUTUBE${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}📺 Verificando contas YouTube...${NC}"
response=$(api_call GET "/youtube/accounts")
echo "   Contas: $response" | head -c 200

echo -e "\n${YELLOW}   Verificando quota disponível...${NC}"
response=$(api_call GET "/youtube/quota")
echo "   Quota: $response" | head -c 200

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}3. TESTE INSTAGRAM${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}📸 Verificando sessões Instagram...${NC}"
response=$(api_call GET "/instagram/sessions")
echo "   Sessões: $response" | head -c 200

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}4. TESTE TIKTOK${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo -e "${YELLOW}🎵 Verificando sessões TikTok...${NC}"
response=$(api_call GET "/tiktok/sessions")
echo "   Sessões: $response" | head -c 200

echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}5. TESTE DE UPLOAD (Simulação)${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Create test video
TEST_VIDEO="/tmp/test_upload_tiktrend.mp4"
if [ ! -f "$TEST_VIDEO" ]; then
    echo -e "${YELLOW}📹 Criando vídeo de teste...${NC}"
    # Create a 3-second test video with ffmpeg if available
    if command -v ffmpeg &> /dev/null; then
        ffmpeg -f lavfi -i "color=c=blue:s=1080x1920:d=3" \
               -f lavfi -i "anullsrc=r=44100:cl=stereo" \
               -shortest -y "$TEST_VIDEO" 2>/dev/null
        echo -e "${GREEN}✅ Vídeo de teste criado: $TEST_VIDEO${NC}"
    else
        echo -e "${YELLOW}⚠️  ffmpeg não encontrado, pulando criação de vídeo${NC}"
    fi
fi

if [ -f "$TEST_VIDEO" ]; then
    echo -e "${YELLOW}📤 Simulando upload...${NC}"
    echo -e "   Arquivo: $TEST_VIDEO"
    echo -e "   Tamanho: $(du -h "$TEST_VIDEO" | cut -f1)"
    echo -e "${GREEN}✅ Arquivo pronto para upload${NC}"
    echo ""
    echo -e "${BLUE}Para fazer upload real, use:${NC}"
    echo ""
    echo -e "  YouTube:"
    echo -e "  curl -X POST $API_URL/youtube/upload \\"
    echo -e "       -H 'Authorization: Bearer \$TOKEN' \\"
    echo -e "       -F 'file=@$TEST_VIDEO' \\"
    echo -e "       -F 'title=Meu Vídeo' \\"
    echo -e "       -F 'description=Descrição'"
    echo ""
    echo -e "  TikTok:"
    echo -e "  curl -X POST $API_URL/tiktok/upload \\"
    echo -e "       -H 'Authorization: Bearer \$TOKEN' \\"
    echo -e "       -F 'file=@$TEST_VIDEO' \\"
    echo -e "       -F 'caption=#trending #viral'"
fi

echo -e "\n${GREEN}=============================================="
echo "   ✅ Testes Concluídos!"
echo "==============================================${NC}"

echo -e "\n${BLUE}Resumo:${NC}"
echo "  ✅ API está online e respondendo"
echo "  📝 Verifique as credenciais em backend/.env"
echo "  📖 Documentação completa em docs/"
echo ""
