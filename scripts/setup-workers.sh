#!/bin/bash
# ==============================================================================
# Worker Supervisor Setup Script
# ==============================================================================
# Configura PM2 ou systemd para gerenciar os workers do TikTrend Finder
#
# Uso:
#   ./scripts/setup-workers.sh pm2      # Configura PM2 (desenvolvimento)
#   ./scripts/setup-workers.sh systemd  # Configura systemd (produção)
#   ./scripts/setup-workers.sh docker   # Usa Docker Compose
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ==============================================================================
# PM2 Setup
# ==============================================================================
setup_pm2() {
    log_info "Configurando PM2..."
    
    # Verifica se PM2 está instalado
    if ! command -v pm2 &> /dev/null; then
        log_warn "PM2 não encontrado. Instalando..."
        npm install -g pm2
    fi
    
    # Cria diretório de logs
    mkdir -p "$PROJECT_ROOT/logs"
    
    # Para processos existentes
    pm2 delete ecosystem.config.js 2>/dev/null || true
    
    # Inicia os workers
    cd "$PROJECT_ROOT"
    pm2 start ecosystem.config.js
    
    # Configura startup automático
    pm2 save
    log_info "Para configurar inicialização automática, execute:"
    echo "  pm2 startup"
    
    log_success "PM2 configurado com sucesso!"
    log_info "Comandos úteis:"
    echo "  pm2 status           # Ver status dos workers"
    echo "  pm2 logs             # Ver logs em tempo real"
    echo "  pm2 logs scheduler   # Logs do scheduler"
    echo "  pm2 restart all      # Reiniciar todos"
    echo "  pm2 monit            # Dashboard interativo"
}

# ==============================================================================
# Systemd Setup
# ==============================================================================
setup_systemd() {
    log_info "Configurando systemd..."
    
    # Verifica se está rodando como root
    if [[ $EUID -ne 0 ]]; then
        log_error "Este script precisa ser executado como root para systemd"
        exit 1
    fi
    
    # Cria usuário tiktrend se não existir
    if ! id "tiktrend" &>/dev/null; then
        log_info "Criando usuário 'tiktrend'..."
        useradd -r -m -s /bin/bash tiktrend
    fi
    
    # Cria diretórios necessários
    mkdir -p /etc/tiktrend-facil
    mkdir -p /var/www/tiktrend-facil/logs
    chown -R didin:didin /var/www/tiktrend-facil
    
    # Copia arquivos de serviço
    log_info "Instalando arquivos de serviço..."
    cp "$PROJECT_ROOT/docker/systemd/tiktrend-scheduler.service" /etc/systemd/system/
    cp "$PROJECT_ROOT/docker/systemd/tiktrend-whatsapp-reconnect.service" /etc/systemd/system/
    
    # Cria arquivo de ambiente template
    if [[ ! -f /etc/tiktrend-facil/scheduler.env ]]; then
        cat > /etc/tiktrend-facil/scheduler.env << 'EOF'
# Scheduler Worker Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/tiktrend
REDIS_URL=redis://localhost:6379/0
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=your-key-here
EOF
        chmod 600 /etc/tiktrend-facil/scheduler.env
        log_warn "Edite /etc/tiktrend-facil/scheduler.env com suas credenciais"
    fi
    
    # Recarrega systemd
    systemctl daemon-reload
    
    # Habilita serviços
    systemctl enable tiktrend-scheduler.service
    systemctl enable tiktrend-whatsapp-reconnect.service
    
    log_success "Systemd configurado com sucesso!"
    log_info "Comandos úteis:"
    echo "  systemctl start tiktrend-scheduler        # Iniciar scheduler"
    echo "  systemctl stop tiktrend-scheduler         # Parar scheduler"
    echo "  systemctl restart tiktrend-scheduler      # Reiniciar"
    echo "  systemctl status tiktrend-scheduler       # Ver status"
    echo "  journalctl -u tiktrend-scheduler -f       # Ver logs"
    echo ""
    echo "  # Para iniciar agora:"
    echo "  systemctl start tiktrend-scheduler tiktrend-whatsapp-reconnect"
}

# ==============================================================================
# Docker Setup
# ==============================================================================
setup_docker() {
    log_info "Configurando Docker Compose workers..."
    
    # Verifica se Docker está instalado
    if ! command -v docker &> /dev/null; then
        log_error "Docker não encontrado"
        exit 1
    fi
    
    cd "$PROJECT_ROOT/docker"
    
    # Cria network se não existir
    docker network create tiktrend-network 2>/dev/null || true
    
    # Inicia os workers
    docker-compose -f docker-compose.yml -f docker-compose.workers.yml up -d scheduler whatsapp-reconnect
    
    log_success "Docker workers iniciados!"
    log_info "Comandos úteis:"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.workers.yml ps"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.workers.yml logs -f scheduler"
    echo "  docker-compose -f docker-compose.yml -f docker-compose.workers.yml restart scheduler"
}

# ==============================================================================
# Status Check
# ==============================================================================
check_status() {
    log_info "Verificando status dos workers..."
    
    echo ""
    echo "=== PM2 ===" 
    if command -v pm2 &> /dev/null; then
        pm2 jlist 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for app in data:
        status = '✅' if app['pm2_env']['status'] == 'online' else '❌'
        print(f\"  {status} {app['name']}: {app['pm2_env']['status']}\")
except:
    print('  Nenhum processo PM2 rodando')
" || echo "  PM2 não configurado"
    else
        echo "  PM2 não instalado"
    fi
    
    echo ""
    echo "=== Systemd ==="
    for service in tiktrend-scheduler tiktrend-whatsapp-reconnect; do
        if systemctl is-active --quiet "$service" 2>/dev/null; then
            echo "  ✅ $service: active"
        elif systemctl is-enabled --quiet "$service" 2>/dev/null; then
            echo "  ⚠️ $service: enabled but not running"
        else
            echo "  ⬜ $service: not configured"
        fi
    done
    
    echo ""
    echo "=== Docker ==="
    if command -v docker &> /dev/null; then
        for container in tiktrend-scheduler tiktrend-whatsapp-reconnect; do
            status=$(docker inspect -f '{{.State.Status}}' "$container" 2>/dev/null || echo "not found")
            if [[ "$status" == "running" ]]; then
                echo "  ✅ $container: running"
            else
                echo "  ⬜ $container: $status"
            fi
        done
    else
        echo "  Docker não instalado"
    fi
}

# ==============================================================================
# Main
# ==============================================================================
case "${1:-status}" in
    pm2)
        setup_pm2
        ;;
    systemd)
        setup_systemd
        ;;
    docker)
        setup_docker
        ;;
    status)
        check_status
        ;;
    *)
        echo "Uso: $0 {pm2|systemd|docker|status}"
        echo ""
        echo "  pm2      - Configura PM2 (desenvolvimento)"
        echo "  systemd  - Configura systemd (produção Linux)"
        echo "  docker   - Usa Docker Compose"
        echo "  status   - Verifica status de todos os métodos"
        exit 1
        ;;
esac
