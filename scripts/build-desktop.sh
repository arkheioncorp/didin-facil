#!/bin/bash

# ============================================================================
# TikTrend Finder - Desktop Build Script
# ============================================================================
# Compila o aplicativo desktop para a plataforma atual ou múltiplas plataformas
# Uso: ./build-desktop.sh [--target <target>] [--release] [--debug]
# ============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Funções de log
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${CYAN}[STEP]${NC} $1"; }

# Valores padrão
BUILD_MODE="release"
TARGET=""
SKIP_FRONTEND=false
VERBOSE=false

# Parse argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --target)
            TARGET="$2"
            shift 2
            ;;
        --release)
            BUILD_MODE="release"
            shift
            ;;
        --debug)
            BUILD_MODE="debug"
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Uso: $0 [opções]"
            echo ""
            echo "Opções:"
            echo "  --target <target>   Target de compilação Rust (ex: x86_64-unknown-linux-gnu)"
            echo "  --release           Build de release (padrão)"
            echo "  --debug             Build de debug"
            echo "  --skip-frontend     Pular build do frontend"
            echo "  --verbose, -v       Output verbose"
            echo "  --help, -h          Mostrar esta ajuda"
            echo ""
            echo "Targets suportados:"
            echo "  Linux:   x86_64-unknown-linux-gnu"
            echo "  Windows: x86_64-pc-windows-msvc"
            echo "  macOS:   x86_64-apple-darwin, aarch64-apple-darwin"
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
echo "    TikTrend Finder - Desktop Build          "
echo "=============================================="
echo ""

# Detectar diretório do projeto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

log_info "Diretório do projeto: $PROJECT_ROOT"
log_info "Modo de build: $BUILD_MODE"

# ============================================================================
# 1. Verificar Dependências
# ============================================================================
log_step "Verificando dependências..."

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "$1 não encontrado! Execute ./scripts/dev-setup.sh primeiro."
        exit 1
    fi
}

check_command "node"
check_command "npm"
check_command "cargo"

# Verificar Tauri CLI
if ! command -v tauri &> /dev/null; then
    if ! cargo tauri --version &> /dev/null; then
        log_info "Instalando Tauri CLI..."
        cargo install tauri-cli
    fi
fi

log_success "Todas as dependências verificadas!"

# ============================================================================
# 2. Limpar builds anteriores (opcional)
# ============================================================================
log_step "Preparando ambiente de build..."

# Limpar cache do Vite se existir problemas
if [ -d "node_modules/.vite" ]; then
    rm -rf node_modules/.vite
fi

# ============================================================================
# 3. Build do Frontend
# ============================================================================
if [ "$SKIP_FRONTEND" = false ]; then
    log_step "Compilando frontend React..."
    
    # Instalar dependências se necessário
    if [ ! -d "node_modules" ]; then
        log_info "Instalando dependências npm..."
        npm ci
    fi
    
    # Build frontend
    npm run build
    log_success "Frontend compilado!"
else
    log_info "Pulando build do frontend (--skip-frontend)"
fi

# ============================================================================
# 4. Build do Tauri App
# ============================================================================
log_step "Compilando aplicativo Tauri..."

BUILD_ARGS=""

if [ "$BUILD_MODE" = "debug" ]; then
    BUILD_ARGS="--debug"
fi

if [ -n "$TARGET" ]; then
    BUILD_ARGS="$BUILD_ARGS --target $TARGET"
    log_info "Target de compilação: $TARGET"
fi

if [ "$VERBOSE" = true ]; then
    BUILD_ARGS="$BUILD_ARGS --verbose"
fi

# Executar build
npm run tauri build -- $BUILD_ARGS

log_success "Build do Tauri concluído!"

# ============================================================================
# 5. Localizar artefatos
# ============================================================================
log_step "Localizando artefatos de build..."

BUNDLE_DIR="src-tauri/target"

if [ -n "$TARGET" ]; then
    BUNDLE_DIR="$BUNDLE_DIR/$TARGET"
fi

if [ "$BUILD_MODE" = "release" ]; then
    BUNDLE_DIR="$BUNDLE_DIR/release/bundle"
else
    BUNDLE_DIR="$BUNDLE_DIR/debug/bundle"
fi

echo ""
log_info "Artefatos gerados em: $BUNDLE_DIR"

# Listar artefatos
if [ -d "$BUNDLE_DIR" ]; then
    echo ""
    log_info "Artefatos disponíveis:"
    
    # Linux
    if [ -d "$BUNDLE_DIR/deb" ]; then
        echo "  📦 DEB: $(ls $BUNDLE_DIR/deb/*.deb 2>/dev/null | head -1)"
    fi
    if [ -d "$BUNDLE_DIR/appimage" ]; then
        echo "  📦 AppImage: $(ls $BUNDLE_DIR/appimage/*.AppImage 2>/dev/null | head -1)"
    fi
    if [ -d "$BUNDLE_DIR/rpm" ]; then
        echo "  📦 RPM: $(ls $BUNDLE_DIR/rpm/*.rpm 2>/dev/null | head -1)"
    fi
    
    # Windows
    if [ -d "$BUNDLE_DIR/msi" ]; then
        echo "  📦 MSI: $(ls $BUNDLE_DIR/msi/*.msi 2>/dev/null | head -1)"
    fi
    if [ -d "$BUNDLE_DIR/nsis" ]; then
        echo "  📦 NSIS: $(ls $BUNDLE_DIR/nsis/*.exe 2>/dev/null | head -1)"
    fi
    
    # macOS
    if [ -d "$BUNDLE_DIR/macos" ]; then
        echo "  📦 macOS App: $(ls $BUNDLE_DIR/macos/*.app 2>/dev/null | head -1)"
    fi
    if [ -d "$BUNDLE_DIR/dmg" ]; then
        echo "  📦 DMG: $(ls $BUNDLE_DIR/dmg/*.dmg 2>/dev/null | head -1)"
    fi
fi

# ============================================================================
# 6. Resumo Final
# ============================================================================
echo ""
echo "=============================================="
echo "          Build Concluído com Sucesso!       "
echo "=============================================="
echo ""

# Calcular tamanho do bundle
if [ -d "$BUNDLE_DIR" ]; then
    BUNDLE_SIZE=$(du -sh "$BUNDLE_DIR" 2>/dev/null | cut -f1)
    log_info "Tamanho total do bundle: $BUNDLE_SIZE"
fi

log_success "O aplicativo está pronto para distribuição!"
echo ""
echo "Para testar localmente:"
echo "  ${GREEN}npm run tauri dev${NC}"
echo ""
