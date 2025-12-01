#!/usr/bin/env bash
# =============================================================================
# Script: check-tauri-invoke.sh
# Description: Verifica se chamadas a invoke() do Tauri estão protegidas com isTauri()
# Usage: ./scripts/check-tauri-invoke.sh
# Exit codes:
#   0 - Todos os arquivos estão corretos
#   1 - Encontrados arquivos com invoke() sem isTauri() check
# =============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Verificando uso seguro de invoke() do Tauri..."
echo ""

# Diretório dos serviços
SERVICES_DIR="src/services"

# Arquivos com problemas
declare -a PROBLEM_FILES=()

# Verificar cada arquivo .ts nos serviços
for file in "$SERVICES_DIR"/*.ts; do
    if [[ ! -f "$file" ]]; then
        continue
    fi
    
    # Verificar se o arquivo importa invoke
    if grep -q "import { invoke }" "$file" 2>/dev/null; then
        # Verificar se também define ou usa isTauri
        if ! grep -qE "isTauri|__TAURI_INTERNALS__|__TAURI__" "$file" 2>/dev/null; then
            PROBLEM_FILES+=("$file")
        fi
    fi
done

# Reportar resultados
if [[ ${#PROBLEM_FILES[@]} -eq 0 ]]; then
    echo -e "${GREEN}✅ Todos os serviços estão usando invoke() de forma segura!${NC}"
    echo ""
    echo "Arquivos verificados em $SERVICES_DIR:"
    for file in "$SERVICES_DIR"/*.ts; do
        if [[ -f "$file" ]]; then
            echo "  ✓ $(basename "$file")"
        fi
    done
    exit 0
else
    echo -e "${RED}❌ Encontrados arquivos com invoke() sem verificação isTauri():${NC}"
    echo ""
    for file in "${PROBLEM_FILES[@]}"; do
        echo -e "${YELLOW}  ⚠️  $file${NC}"
        echo "     Linha(s) com invoke:"
        grep -n "invoke" "$file" | head -5 | while read -r line; do
            echo "       $line"
        done
        echo ""
    done
    
    echo -e "${RED}📖 Como corrigir:${NC}"
    echo ""
    echo "1. Adicione a verificação isTauri() no arquivo:"
    echo ""
    echo "   const isTauri = (): boolean => {"
    echo "     return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;"
    echo "   };"
    echo ""
    echo "2. Proteja cada chamada invoke():"
    echo ""
    echo "   if (isTauri()) {"
    echo "     return await invoke<T>('command_name');"
    echo "   }"
    echo "   // Fallback para browser"
    echo "   return defaultValue;"
    echo ""
    echo "📚 Veja: CONTRIBUTING.md - Seção 'Padrão isTauri()'"
    echo ""
    exit 1
fi
