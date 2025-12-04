#!/usr/bin/env bash

# ============================================================================
# TikTrend Finder - Universal Installation Script
# ============================================================================
# Detecta automaticamente o sistema operacional e instala todas as dependências
# Suporta: Ubuntu, Debian, Fedora, Arch, openSUSE, macOS
# ============================================================================

set -e

# Versões mínimas
MIN_NODE_VERSION=20
MIN_PYTHON_VERSION="3.11"
MIN_RUST_VERSION="1.70"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step() { echo -e "${PURPLE}[STEP]${NC} ${BOLD}$1${NC}"; }

# Banner
show_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║   ████████╗██╗██╗  ██╗████████╗██████╗ ███████╗███╗   ██╗██████╗  ║"
    echo "║   ╚══██╔══╝██║██║ ██╔╝╚══██╔══╝██╔══██╗██╔════╝████╗  ██║██╔══██╗ ║"
    echo "║      ██║   ██║█████╔╝    ██║   ██████╔╝█████╗  ██╔██╗ ██║██║  ██║ ║"
    echo "║      ██║   ██║██╔═██╗    ██║   ██╔══██╗██╔══╝  ██║╚██╗██║██║  ██║ ║"
    echo "║      ██║   ██║██║  ██╗   ██║   ██║  ██║███████╗██║ ╚████║██████╔╝ ║"
    echo "║      ╚═╝   ╚═╝╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═════╝  ║"
    echo "║                                                               ║"
    echo "║               FINDER - Instalador Universal                   ║"
    echo "║                      Versão 1.0.0                             ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ============================================================================
# Detecção de Sistema Operacional
# ============================================================================

detect_os() {
    log_step "Detectando sistema operacional..."
    
    OS=""
    DISTRO=""
    PKG_MANAGER=""
    PKG_INSTALL=""
    PKG_UPDATE=""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        DISTRO="macOS"
        
        # Verificar se Homebrew está instalado
        if command -v brew &> /dev/null; then
            PKG_MANAGER="brew"
            PKG_INSTALL="brew install"
            PKG_UPDATE="brew update"
        else
            log_warning "Homebrew não encontrado. Será instalado automaticamente."
            PKG_MANAGER="brew"
        fi
        
        # Detectar versão do macOS
        MACOS_VERSION=$(sw_vers -productVersion)
        log_success "macOS $MACOS_VERSION detectado"
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        
        # Detectar distribuição Linux
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            DISTRO=$ID
            DISTRO_VERSION=$VERSION_ID
            DISTRO_NAME=$PRETTY_NAME
        elif [ -f /etc/lsb-release ]; then
            . /etc/lsb-release
            DISTRO=$DISTRIB_ID
            DISTRO_VERSION=$DISTRIB_RELEASE
        fi
        
        # Configurar gerenciador de pacotes
        case $DISTRO in
            ubuntu|debian|linuxmint|pop|elementary|zorin)
                PKG_MANAGER="apt"
                PKG_INSTALL="sudo apt-get install -y"
                PKG_UPDATE="sudo apt-get update"
                ;;
            fedora)
                PKG_MANAGER="dnf"
                PKG_INSTALL="sudo dnf install -y"
                PKG_UPDATE="sudo dnf check-update || true"
                ;;
            centos|rhel|rocky|almalinux)
                PKG_MANAGER="yum"
                PKG_INSTALL="sudo yum install -y"
                PKG_UPDATE="sudo yum check-update || true"
                ;;
            arch|manjaro|endeavouros)
                PKG_MANAGER="pacman"
                PKG_INSTALL="sudo pacman -S --noconfirm"
                PKG_UPDATE="sudo pacman -Sy"
                ;;
            opensuse*|sles)
                PKG_MANAGER="zypper"
                PKG_INSTALL="sudo zypper install -y"
                PKG_UPDATE="sudo zypper refresh"
                ;;
            *)
                log_error "Distribuição Linux não suportada: $DISTRO"
                log_info "Distros suportadas: Ubuntu, Debian, Fedora, Arch, openSUSE"
                exit 1
                ;;
        esac
        
        log_success "Linux detectado: $DISTRO_NAME"
        
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        log_error "Windows detectado. Use o script install.ps1 no PowerShell:"
        log_info "  PowerShell: .\\scripts\\install.ps1"
        exit 1
    else
        log_error "Sistema operacional não suportado: $OSTYPE"
        exit 1
    fi
    
    log_info "Gerenciador de pacotes: $PKG_MANAGER"
}

# ============================================================================
# Verificação de Privilégios
# ============================================================================

check_privileges() {
    if [[ "$OS" == "linux" ]] && [[ $EUID -eq 0 ]]; then
        log_warning "Executando como root. Algumas operações serão feitas como usuário normal."
    fi
}

# ============================================================================
# Instalação do Homebrew (macOS)
# ============================================================================

install_homebrew() {
    if [[ "$OS" != "macos" ]]; then return; fi
    
    if ! command -v brew &> /dev/null; then
        log_step "Instalando Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # Adicionar ao PATH
        if [[ -f "/opt/homebrew/bin/brew" ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
            echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        fi
        
        log_success "Homebrew instalado!"
    else
        log_success "Homebrew já está instalado"
    fi
    
    PKG_INSTALL="brew install"
    PKG_UPDATE="brew update"
}

# ============================================================================
# Atualização do Sistema
# ============================================================================

update_system() {
    log_step "Atualizando lista de pacotes..."
    
    if [[ -n "$PKG_UPDATE" ]]; then
        eval "$PKG_UPDATE" 2>/dev/null || true
        log_success "Lista de pacotes atualizada"
    fi
}

# ============================================================================
# Instalação de Dependências do Sistema
# ============================================================================

install_system_deps() {
    log_step "Instalando dependências do sistema..."
    
    case $DISTRO in
        ubuntu|debian|linuxmint|pop)
            # Dependências para Tauri
            DEPS=(
                "build-essential"
                "curl"
                "wget"
                "file"
                "libssl-dev"
                "libgtk-3-dev"
                "libayatana-appindicator3-dev"
                "librsvg2-dev"
                "libwebkit2gtk-4.1-dev"
                "libjavascriptcoregtk-4.1-dev"
                "libsoup-3.0-dev"
                "patchelf"
                "git"
            )
            ;;
        fedora)
            DEPS=(
                "gcc"
                "gcc-c++"
                "curl"
                "wget"
                "file"
                "openssl-devel"
                "gtk3-devel"
                "webkit2gtk4.1-devel"
                "javascriptcoregtk4.1-devel"
                "libsoup3-devel"
                "librsvg2-devel"
                "patchelf"
                "git"
            )
            ;;
        arch|manjaro)
            DEPS=(
                "base-devel"
                "curl"
                "wget"
                "file"
                "openssl"
                "gtk3"
                "webkit2gtk-4.1"
                "librsvg"
                "patchelf"
                "git"
            )
            ;;
        opensuse*)
            DEPS=(
                "patterns-devel-base-devel_basis"
                "curl"
                "wget"
                "libopenssl-devel"
                "gtk3-devel"
                "webkit2gtk3-devel"
                "librsvg-devel"
                "patchelf"
                "git"
            )
            ;;
        macOS)
            DEPS=(
                "curl"
                "wget"
                "git"
            )
            ;;
    esac
    
    for dep in "${DEPS[@]}"; do
        log_info "Instalando $dep..."
        eval "$PKG_INSTALL $dep" 2>/dev/null || log_warning "Falha ao instalar $dep (pode já estar instalado)"
    done
    
    log_success "Dependências do sistema instaladas!"
}

# ============================================================================
# Instalação do Node.js
# ============================================================================

install_nodejs() {
    log_step "Verificando Node.js..."
    
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge "$MIN_NODE_VERSION" ]; then
            log_success "Node.js v$(node -v | cut -d'v' -f2) já instalado"
            return
        else
            log_warning "Node.js v$NODE_VERSION encontrado, mas v$MIN_NODE_VERSION+ é necessário"
        fi
    fi
    
    log_info "Instalando Node.js $MIN_NODE_VERSION..."
    
    if [[ "$OS" == "macos" ]]; then
        brew install node@$MIN_NODE_VERSION
        brew link --overwrite node@$MIN_NODE_VERSION
    else
        # Usar NodeSource para versão específica
        curl -fsSL https://deb.nodesource.com/setup_$MIN_NODE_VERSION.x | sudo -E bash -
        $PKG_INSTALL nodejs
    fi
    
    log_success "Node.js $(node -v) instalado!"
}

# ============================================================================
# Instalação do Rust
# ============================================================================

install_rust() {
    log_step "Verificando Rust..."
    
    if command -v rustc &> /dev/null; then
        RUST_VERSION=$(rustc --version | cut -d' ' -f2)
        log_success "Rust $RUST_VERSION já instalado"
        return
    fi
    
    log_info "Instalando Rust via rustup..."
    
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    
    # Adicionar ao PATH
    source "$HOME/.cargo/env"
    
    log_success "Rust $(rustc --version | cut -d' ' -f2) instalado!"
}

# ============================================================================
# Instalação do Python
# ============================================================================

install_python() {
    log_step "Verificando Python..."
    
    PYTHON_CMD=""
    
    # Verificar python3.11 ou superior
    for cmd in python3.12 python3.11 python3; do
        if command -v $cmd &> /dev/null; then
            PY_VERSION=$($cmd --version 2>&1 | cut -d' ' -f2)
            PY_MAJOR=$(echo $PY_VERSION | cut -d'.' -f1)
            PY_MINOR=$(echo $PY_VERSION | cut -d'.' -f2)
            
            if [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -ge 11 ]; then
                PYTHON_CMD=$cmd
                log_success "Python $PY_VERSION já instalado ($cmd)"
                break
            fi
        fi
    done
    
    if [ -z "$PYTHON_CMD" ]; then
        log_info "Instalando Python 3.11+..."
        
        case $DISTRO in
            ubuntu|debian|linuxmint|pop)
                sudo add-apt-repository -y ppa:deadsnakes/ppa 2>/dev/null || true
                sudo apt-get update
                $PKG_INSTALL python3.11 python3.11-venv python3.11-dev python3-pip
                PYTHON_CMD="python3.11"
                ;;
            fedora)
                $PKG_INSTALL python3.11 python3.11-devel python3-pip
                PYTHON_CMD="python3.11"
                ;;
            arch|manjaro)
                $PKG_INSTALL python python-pip
                PYTHON_CMD="python3"
                ;;
            macOS)
                brew install python@3.11
                PYTHON_CMD="python3.11"
                ;;
        esac
        
        log_success "Python instalado!"
    fi
    
    # Verificar pip
    if ! $PYTHON_CMD -m pip --version &> /dev/null; then
        log_info "Instalando pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
    fi
    
    echo "PYTHON_CMD=$PYTHON_CMD" >> "$PROJECT_ROOT/.env.local"
}

# ============================================================================
# Instalação do Tauri CLI
# ============================================================================

install_tauri_cli() {
    log_step "Verificando Tauri CLI..."
    
    if command -v cargo-tauri &> /dev/null || cargo tauri --version &> /dev/null 2>&1; then
        log_success "Tauri CLI já instalado"
        return
    fi
    
    log_info "Instalando Tauri CLI..."
    cargo install tauri-cli
    
    log_success "Tauri CLI instalado!"
}

# ============================================================================
# Configuração do Ambiente Python (Scraper)
# ============================================================================

setup_python_env() {
    log_step "Configurando ambiente Python para o scraper..."
    
    SCRIPTS_DIR="$PROJECT_ROOT/scripts"
    VENV_DIR="$SCRIPTS_DIR/venv"
    
    # Criar virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        log_info "Criando virtual environment..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi
    
    # Ativar venv e instalar dependências
    source "$VENV_DIR/bin/activate"
    
    log_info "Atualizando pip..."
    pip install --upgrade pip
    
    log_info "Instalando dependências Python..."
    pip install -r "$SCRIPTS_DIR/requirements.txt"
    
    # Instalar Playwright e navegadores
    log_info "Instalando Playwright e Chromium..."
    pip install playwright
    playwright install chromium
    playwright install-deps 2>/dev/null || true
    
    deactivate
    
    log_success "Ambiente Python configurado!"
}

# ============================================================================
# Instalação de Dependências do Frontend
# ============================================================================

install_frontend_deps() {
    log_step "Instalando dependências do frontend..."
    
    cd "$PROJECT_ROOT"
    
    if [ -f "package.json" ]; then
        npm install
        log_success "Dependências do frontend instaladas!"
    else
        log_error "package.json não encontrado!"
        exit 1
    fi
}

# ============================================================================
# Compilar Backend Rust
# ============================================================================

build_rust_backend() {
    log_step "Compilando backend Rust..."
    
    cd "$PROJECT_ROOT/src-tauri"
    cargo build --release
    
    log_success "Backend Rust compilado!"
}

# ============================================================================
# Criar Estrutura de Diretórios
# ============================================================================

create_directories() {
    log_step "Criando estrutura de diretórios..."
    
    DIRS=(
        "$HOME/.tiktrend"
        "$HOME/.tiktrend/data"
        "$HOME/.tiktrend/cache"
        "$HOME/.tiktrend/logs"
        "$HOME/.tiktrend/exports"
        "$HOME/.tiktrend/images"
        "$PROJECT_ROOT/src-tauri/binaries"
        "$PROJECT_ROOT/src-tauri/resources"
    )
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        log_info "Criado: $dir"
    done
    
    log_success "Estrutura de diretórios criada!"
}

# ============================================================================
# Criar arquivo de configuração inicial
# ============================================================================

create_initial_config() {
    log_step "Criando configuração inicial..."
    
    CONFIG_FILE="$HOME/.tiktrend/config.json"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        cat > "$CONFIG_FILE" << 'EOF'
{
  "version": "1.0.0",
  "firstRun": true,
  "installedAt": "",
  "settings": {
    "theme": "dark",
    "language": "pt-BR",
    "notifications": true,
    "autoUpdate": true
  },
  "scraper": {
    "maxProducts": 50,
    "intervalMinutes": 60,
    "categories": [],
    "useProxy": false
  },
  "license": {
    "key": null,
    "plan": "trial",
    "expiresAt": null,
    "trialStarted": null
  },
  "credentials": {
    "openaiKey": null,
    "proxies": []
  }
}
EOF
        # Adicionar data de instalação
        sed -i "s/\"installedAt\": \"\"/\"installedAt\": \"$(date -Iseconds)\"/" "$CONFIG_FILE"
        
        log_success "Configuração inicial criada!"
    else
        log_info "Configuração já existe, mantendo..."
    fi
}

# ============================================================================
# Criar arquivo .env
# ============================================================================

create_env_file() {
    log_step "Criando arquivo .env..."
    
    ENV_FILE="$PROJECT_ROOT/.env"
    
    if [ ! -f "$ENV_FILE" ]; then
        cat > "$ENV_FILE" << 'EOF'
# TikTrend Finder - Environment Variables
# Gerado automaticamente pelo instalador

# Modo de desenvolvimento
VITE_DEV_MODE=false

# Diretório de dados do usuário
VITE_DATA_DIR=~/.tiktrend

# API URL (para funcionalidades cloud opcionais)
VITE_API_URL=

# Telemetria (anônima, para melhorias)
VITE_ENABLE_TELEMETRY=false

# Sentry DSN (error tracking - opcional)
VITE_SENTRY_DSN=
EOF
        log_success "Arquivo .env criado!"
    else
        log_info ".env já existe, mantendo..."
    fi
}

# ============================================================================
# Verificação Final
# ============================================================================

verify_installation() {
    log_step "Verificando instalação..."
    
    ERRORS=0
    
    # Node.js
    if command -v node &> /dev/null; then
        log_success "Node.js: $(node -v)"
    else
        log_error "Node.js não encontrado!"
        ((ERRORS++))
    fi
    
    # npm
    if command -v npm &> /dev/null; then
        log_success "npm: $(npm -v)"
    else
        log_error "npm não encontrado!"
        ((ERRORS++))
    fi
    
    # Rust
    if command -v rustc &> /dev/null; then
        log_success "Rust: $(rustc --version | cut -d' ' -f2)"
    else
        log_error "Rust não encontrado!"
        ((ERRORS++))
    fi
    
    # Cargo
    if command -v cargo &> /dev/null; then
        log_success "Cargo: $(cargo --version | cut -d' ' -f2)"
    else
        log_error "Cargo não encontrado!"
        ((ERRORS++))
    fi
    
    # Python
    if [ -n "$PYTHON_CMD" ] && command -v $PYTHON_CMD &> /dev/null; then
        log_success "Python: $($PYTHON_CMD --version | cut -d' ' -f2)"
    else
        log_error "Python não encontrado!"
        ((ERRORS++))
    fi
    
    # Playwright
    if [ -d "$PROJECT_ROOT/scripts/venv" ]; then
        source "$PROJECT_ROOT/scripts/venv/bin/activate"
        if python -c "import playwright" 2>/dev/null; then
            log_success "Playwright: instalado"
        else
            log_warning "Playwright não encontrado no venv"
        fi
        deactivate
    fi
    
    return $ERRORS
}

# ============================================================================
# Resumo Final
# ============================================================================

show_summary() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║          INSTALAÇÃO CONCLUÍDA COM SUCESSO! 🎉                 ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Sistema:${NC} $DISTRO_NAME"
    echo -e "${CYAN}Diretório:${NC} $PROJECT_ROOT"
    echo -e "${CYAN}Dados:${NC} $HOME/.tiktrend"
    echo ""
    echo -e "${YELLOW}Próximos passos:${NC}"
    echo ""
    echo -e "  1. ${BOLD}Iniciar em modo desenvolvimento:${NC}"
    echo -e "     ${GREEN}cd $PROJECT_ROOT${NC}"
    echo -e "     ${GREEN}npm run tauri dev${NC}"
    echo ""
    echo -e "  2. ${BOLD}Build para produção:${NC}"
    echo -e "     ${GREEN}npm run tauri build${NC}"
    echo ""
    echo -e "  3. ${BOLD}Executar scraper manualmente:${NC}"
    echo -e "     ${GREEN}cd scripts && source venv/bin/activate${NC}"
    echo -e "     ${GREEN}python scraper.py${NC}"
    echo ""
    echo -e "${PURPLE}Documentação:${NC} $PROJECT_ROOT/docs/"
    echo ""
}

# ============================================================================
# Main
# ============================================================================

main() {
    show_banner
    
    # Detectar diretório do projeto
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    
    log_info "Diretório do projeto: $PROJECT_ROOT"
    cd "$PROJECT_ROOT"
    
    # Etapas de instalação
    detect_os
    check_privileges
    
    if [[ "$OS" == "macos" ]]; then
        install_homebrew
    fi
    
    update_system
    install_system_deps
    install_nodejs
    install_rust
    install_python
    install_tauri_cli
    create_directories
    install_frontend_deps
    setup_python_env
    create_initial_config
    create_env_file
    
    # Compilar em background (opcional)
    log_info "Compilação do backend será feita na primeira execução..."
    
    # Verificar
    if verify_installation; then
        show_summary
    else
        log_error "Instalação completada com erros. Verifique as mensagens acima."
        exit 1
    fi
}

# Executar
main "$@"
