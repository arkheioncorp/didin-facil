#!/bin/bash

# ============================================================================
# TikTrend Finder - Service Health Check Script
# ============================================================================
# Verifica saúde de todos os serviços após deploy
# ============================================================================

set -e

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuração
API_URL="${API_URL:-http://localhost:8000}"
MAX_RETRIES=30
RETRY_INTERVAL=5

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[!]${NC} $1"; }

check_endpoint() {
    local name="$1"
    local url="$2"
    local expected_status="${3:-200}"
    
    echo -n "  Checking $name... "
    
    local response
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}FAILED${NC} (HTTP $response)"
        return 1
    fi
}

wait_for_service() {
    local name="$1"
    local url="$2"
    local retries=0
    
    log_info "Waiting for $name to be ready..."
    
    while [ $retries -lt $MAX_RETRIES ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_success "$name is ready"
            return 0
        fi
        
        retries=$((retries + 1))
        echo "  Attempt $retries/$MAX_RETRIES..."
        sleep $RETRY_INTERVAL
    done
    
    log_error "$name failed to start after $MAX_RETRIES attempts"
    return 1
}

# Banner
echo "=============================================="
echo "  TikTrend Finder - Health Check"
echo "=============================================="
echo ""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --api-url)
            API_URL="$2"
            shift 2
            ;;
        --wait)
            WAIT_FOR_READY=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

log_info "API URL: $API_URL"
echo ""

# Wait for service if requested
if [ "$WAIT_FOR_READY" = true ]; then
    wait_for_service "API" "$API_URL/health"
fi

# Health Checks
echo "Running health checks..."
echo ""

FAILED=0

# API Health
check_endpoint "API Health" "$API_URL/health" || FAILED=1

# API Root
check_endpoint "API Root" "$API_URL/" || FAILED=1

# Auth endpoints (should return 401 without token)
check_endpoint "Auth (requires auth)" "$API_URL/auth/me" "401" || FAILED=1

# Products endpoint (should return 401 without token)
check_endpoint "Products (requires auth)" "$API_URL/products" "401" || FAILED=1

# Social Auth platforms (public endpoint)
check_endpoint "Social Platforms" "$API_URL/social-auth/platforms" || FAILED=1

# Integrations config (requires auth)
check_endpoint "Integrations (requires auth)" "$API_URL/integrations/config" "401" || FAILED=1

echo ""

# Summary
if [ $FAILED -eq 0 ]; then
    log_success "All health checks passed!"
    echo ""
    echo "API Status:"
    curl -s "$API_URL/health" | python3 -m json.tool 2>/dev/null || cat
    echo ""
    exit 0
else
    log_error "Some health checks failed!"
    exit 1
fi
