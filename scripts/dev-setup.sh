#!/bin/bash

# ============================================================================
# TikTrend Finder - Development Environment Setup
# ============================================================================
# Este script configura o ambiente de desenvolvimento completo
# Requisitos: Node.js 20+, Rust 1.70+, Python 3.11+
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Header
echo ""
echo "=============================================="
echo "   TikTrend Finder - Dev Environment Setup   "
echo "=============================================="
echo ""

# Detectar diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

log_info "Diretório do projeto: $PROJECT_ROOT"

# ============================================================================
# 1. Verificar Dependências do Sistema
# ============================================================================
log_info "Verificando dependências do sistema..."

check_command() {
    if command -v "$1" &> /dev/null; then
        log_success "$1 encontrado: $($1 --version 2>&1 | head -n1)"
        return 0
    else
        log_error "$1 não encontrado!"
        return 1
    fi
}

MISSING_DEPS=()

if ! check_command "node"; then MISSING_DEPS+=("Node.js"); fi
if ! check_command "npm"; then MISSING_DEPS+=("npm"); fi
if ! check_command "rustc"; then MISSING_DEPS+=("Rust"); fi
if ! check_command "cargo"; then MISSING_DEPS+=("Cargo"); fi
if ! check_command "python3"; then MISSING_DEPS+=("Python3"); fi

if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
    log_error "Dependências faltando: ${MISSING_DEPS[*]}"
    echo ""
    echo "Instale as dependências necessárias:"
    echo "  - Node.js 20+: https://nodejs.org/"
    echo "  - Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    echo "  - Python 3.11+: https://www.python.org/"
    exit 1
fi

# Verificar versões mínimas
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    log_warning "Node.js versão $NODE_VERSION detectada. Recomendado: 20+"
fi

# ============================================================================
# 2. Instalar Dependências do Frontend
# ============================================================================
log_info "Instalando dependências do frontend (npm)..."

if [ -f "package.json" ]; then
    npm install
    log_success "Dependências do frontend instaladas!"
else
    log_error "package.json não encontrado!"
    exit 1
fi

# ============================================================================
# 3. Instalar Dependências do Tauri/Rust
# ============================================================================
log_info "Verificando dependências do Tauri..."

# Instalar Tauri CLI se necessário
if ! command -v tauri &> /dev/null; then
    log_info "Instalando Tauri CLI..."
    cargo install tauri-cli
fi

# Instalar dependências do sistema para Tauri (Linux)
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    log_info "Verificando dependências do sistema Linux para Tauri..."
    
    # Verificar se é Debian/Ubuntu
    if command -v apt-get &> /dev/null; then
        TAURI_DEPS="libwebkit2gtk-4.1-dev libappindicator3-dev librsvg2-dev patchelf"
        
        MISSING_PACKAGES=()
        for pkg in $TAURI_DEPS; do
            if ! dpkg -l | grep -q "^ii  $pkg"; then
                MISSING_PACKAGES+=("$pkg")
            fi
        done
        
        if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
            log_warning "Pacotes faltando para Tauri: ${MISSING_PACKAGES[*]}"
            log_info "Instalando com sudo apt-get..."
            sudo apt-get update
            sudo apt-get install -y ${MISSING_PACKAGES[*]}
        fi
    fi
fi

# Build dependências Rust
log_info "Compilando dependências Rust..."
cd src-tauri
cargo build
cd ..
log_success "Dependências Rust compiladas!"

# ============================================================================
# 4. Configurar Python Environment (Scraper)
# ============================================================================
log_info "Configurando ambiente Python para o scraper..."

cd scripts

# Criar virtual environment se não existir
if [ ! -d "venv" ]; then
    log_info "Criando virtual environment..."
    python3 -m venv venv
fi

# Ativar venv e instalar dependências
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Instalar Playwright browsers
log_info "Instalando navegadores Playwright..."
playwright install chromium

deactivate
cd ..
log_success "Ambiente Python configurado!"

# ============================================================================
# 5. Criar arquivo .env se não existir
# ============================================================================
if [ ! -f ".env" ]; then
    log_info "Criando arquivo .env..."
    cat > .env << 'EOF'
# TikTrend Finder - Environment Variables
# Copie este arquivo e preencha com suas credenciais

# API Backend (quando estiver pronto)
VITE_API_URL=http://localhost:8000

# Sentry Error Tracking (opcional)
VITE_SENTRY_DSN=

# Feature Flags
VITE_ENABLE_ANALYTICS=false
VITE_ENABLE_TELEMETRY=false

# Development
VITE_DEV_MODE=true
EOF
    log_success ".env criado! Edite conforme necessário."
else
    log_info ".env já existe, pulando..."
fi

# ============================================================================
# 6. Verificar Estrutura do Projeto
# ============================================================================
log_info "Verificando estrutura do projeto..."

REQUIRED_DIRS=("src" "src-tauri" "docs" "scripts")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log_success "Diretório $dir: OK"
    else
        log_error "Diretório $dir não encontrado!"
    fi
done

# ============================================================================
# 7. Resumo Final
# ============================================================================
echo ""
echo "=============================================="
echo "        Setup Concluído com Sucesso!         "
echo "=============================================="
echo ""
log_info "Próximos passos:"
echo ""
echo "  1. Iniciar desenvolvimento frontend:"
echo "     ${GREEN}npm run dev${NC}"
echo ""
echo "  2. Iniciar app Tauri (desktop):"
echo "     ${GREEN}npm run tauri dev${NC}"
echo ""
echo "  3. Executar scraper Python:"
echo "     ${GREEN}cd scripts && source venv/bin/activate && python scraper.py${NC}"
echo ""
echo "  4. Build para produção:"
echo "     ${GREEN}./scripts/build-desktop.sh${NC}"
echo ""
log_success "Ambiente de desenvolvimento pronto!"
