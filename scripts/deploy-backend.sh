#!/bin/bash

# ============================================================================
# TikTrend Finder - Backend Deployment Script
# ============================================================================
# Deploy dos serviços backend (API + Scraper Workers)
# Suporta: Railway, DigitalOcean, Docker Compose
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Valores padrão
DEPLOY_TARGET="docker"
ENVIRONMENT="production"
SERVICE="all"
DRY_RUN=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            DEPLOY_TARGET="$2"
            shift 2
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --service)
            SERVICE="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [opções]"
            echo ""
            echo "Opções:"
            echo "  --target <target>     Plataforma de deploy (docker, railway, digitalocean)"
            echo "  --env <environment>   Ambiente (production, staging)"
            echo "  --service <service>   Serviço específico (api, scraper, all)"
            echo "  --dry-run             Simular deploy sem executar"
            echo "  --help, -h            Mostrar esta ajuda"
            echo ""
            echo "Exemplos:"
            echo "  $0 --target docker --env staging"
            echo "  $0 --target railway --service api"
            echo "  $0 --target digitalocean --env production"
            exit 0
            ;;
        *)
            log_error "Opção desconhecida: $1"
            exit 1
            ;;
    esac
done

# Header
echo ""
echo "=============================================="
echo "    TikTrend Finder - Backend Deploy         "
echo "=============================================="
echo ""

# Detectar diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

log_info "Target: $DEPLOY_TARGET"
log_info "Ambiente: $ENVIRONMENT"
log_info "Serviço: $SERVICE"

if [ "$DRY_RUN" = true ]; then
    log_warning "Modo DRY RUN - Nenhuma alteração será aplicada"
fi

# ============================================================================
# Funções de Deploy
# ============================================================================

deploy_docker() {
    log_step "Deploy via Docker Compose..."
    
    DOCKER_DIR="$PROJECT_ROOT/docker"
    
    if [ ! -d "$DOCKER_DIR" ]; then
        log_error "Diretório docker/ não encontrado!"
        exit 1
    fi
    
    cd "$DOCKER_DIR"
    
    # Verificar se docker-compose existe
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose não encontrado!"
        exit 1
    fi
    
    # Usar docker compose (v2) ou docker-compose (v1)
    COMPOSE_CMD="docker compose"
    if ! docker compose version &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    fi
    
    # Selecionar arquivo compose baseado no ambiente
    COMPOSE_FILE="docker-compose.yml"
    if [ "$ENVIRONMENT" = "production" ] && [ -f "docker-compose.prod.yml" ]; then
        COMPOSE_FILE="docker-compose.prod.yml"
    fi
    
    log_info "Usando: $COMPOSE_FILE"
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: $COMPOSE_CMD -f $COMPOSE_FILE up --build -d"
        return
    fi
    
    # Build e deploy
    case $SERVICE in
        api)
            $COMPOSE_CMD -f $COMPOSE_FILE up --build -d api
            ;;
        scraper)
            $COMPOSE_CMD -f $COMPOSE_FILE up --build -d scraper
            ;;
        all)
            $COMPOSE_CMD -f $COMPOSE_FILE up --build -d
            ;;
    esac
    
    log_success "Deploy Docker concluído!"
    
    # Mostrar status
    $COMPOSE_CMD -f $COMPOSE_FILE ps
}

deploy_railway() {
    log_step "Deploy via Railway..."
    
    # Verificar Railway CLI
    if ! command -v railway &> /dev/null; then
        log_info "Instalando Railway CLI..."
        if [ "$DRY_RUN" = true ]; then
            log_info "DRY RUN: npm install -g @railway/cli"
        else
            npm install -g @railway/cli
        fi
    fi
    
    # Verificar login
    if ! railway whoami &> /dev/null 2>&1; then
        log_error "Não autenticado no Railway. Execute: railway login"
        exit 1
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: railway up --service $SERVICE"
        return
    fi
    
    case $SERVICE in
        api)
            railway up --service api
            ;;
        scraper)
            railway up --service scraper
            ;;
        all)
            railway up --service api
            railway up --service scraper
            ;;
    esac
    
    log_success "Deploy Railway concluído!"
}

deploy_digitalocean() {
    log_step "Deploy via DigitalOcean App Platform..."
    
    # Verificar doctl CLI
    if ! command -v doctl &> /dev/null; then
        log_error "doctl CLI não encontrado!"
        log_info "Instale: https://docs.digitalocean.com/reference/doctl/how-to/install/"
        exit 1
    fi
    
    # Verificar autenticação
    if ! doctl account get &> /dev/null 2>&1; then
        log_error "Não autenticado no DigitalOcean. Execute: doctl auth init"
        exit 1
    fi
    
    # Nome do app baseado no ambiente
    APP_NAME="tiktrend-finder"
    if [ "$ENVIRONMENT" = "staging" ]; then
        APP_NAME="tiktrend-finder-staging"
    fi
    
    if [ "$DRY_RUN" = true ]; then
        log_info "DRY RUN: doctl apps create-deployment $APP_NAME"
        return
    fi
    
    # Trigger deployment
    APP_ID=$(doctl apps list --format ID,Spec.Name --no-header | grep "$APP_NAME" | awk '{print $1}')
    
    if [ -z "$APP_ID" ]; then
        log_error "App '$APP_NAME' não encontrado no DigitalOcean!"
        log_info "Crie o app primeiro via console ou app spec"
        exit 1
    fi
    
    doctl apps create-deployment "$APP_ID"
    
    log_success "Deploy DigitalOcean iniciado!"
    log_info "Acompanhe em: https://cloud.digitalocean.com/apps/$APP_ID"
}

# ============================================================================
# Verificações Pré-Deploy
# ============================================================================

log_step "Verificações pré-deploy..."

# Verificar variáveis de ambiente necessárias
REQUIRED_VARS=()

case $ENVIRONMENT in
    production)
        REQUIRED_VARS+=("DATABASE_URL" "REDIS_URL" "JWT_SECRET_KEY")
        ;;
    staging)
        REQUIRED_VARS+=("DATABASE_URL")
        ;;
esac

MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    log_warning "Variáveis de ambiente não configuradas: ${MISSING_VARS[*]}"
    log_info "Configure via .env ou variáveis de ambiente do provider"
fi

# ============================================================================
# Executar Deploy
# ============================================================================

case $DEPLOY_TARGET in
    docker)
        deploy_docker
        ;;
    railway)
        deploy_railway
        ;;
    digitalocean)
        deploy_digitalocean
        ;;
    *)
        log_error "Target de deploy desconhecido: $DEPLOY_TARGET"
        log_info "Targets suportados: docker, railway, digitalocean"
        exit 1
        ;;
esac

# ============================================================================
# Pós-Deploy
# ============================================================================

echo ""
echo "=============================================="
echo "          Deploy Concluído!                  "
echo "=============================================="
echo ""

log_info "Próximos passos:"
echo "  1. Verificar logs: docker compose logs -f (se docker)"
echo "  2. Verificar health: curl https://api.tiktrend.com/health"
echo "  3. Executar migrations se necessário"
echo ""

if [ "$ENVIRONMENT" = "production" ]; then
    log_warning "Lembre-se de verificar:"
    echo "  - Migrations do banco de dados"
    echo "  - Redis cache limpo (se necessário)"
    echo "  - Notificar equipe sobre o deploy"
fi

log_success "Deploy finalizado com sucesso!"
