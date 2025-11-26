#!/bin/bash
# TikTrend Finder - Complete Test Suite with Coverage Report
# Runs all tests (unit, integration, E2E) and generates coverage reports

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}TikTrend Finder - Complete Test Suite${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# Directory setup
ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR"
BACKEND_DIR="$ROOT_DIR/backend"
REPORTS_DIR="$ROOT_DIR/test-reports"

# Create reports directory
mkdir -p "$REPORTS_DIR"
mkdir -p "$REPORTS_DIR/frontend"
mkdir -p "$REPORTS_DIR/backend"
mkdir -p "$REPORTS_DIR/e2e"

# ============================================
# FRONTEND TESTS
# ============================================
echo -e "${YELLOW}[1/3] Running Frontend Tests...${NC}"
cd "$FRONTEND_DIR"

echo "Installing dependencies..."
npm install --silent

echo "Running Vitest with coverage..."
npx vitest run --coverage --reporter=verbose --outputFile="$REPORTS_DIR/frontend/test-results.json" 2>&1 | tee "$REPORTS_DIR/frontend/test-output.log"

# Copy coverage report
if [ -d "coverage" ]; then
    cp -r coverage/* "$REPORTS_DIR/frontend/"
    echo -e "${GREEN}✓ Frontend coverage report generated${NC}"
fi

# ============================================
# BACKEND TESTS
# ============================================
echo ""
echo -e "${YELLOW}[2/3] Running Backend Tests...${NC}"
cd "$BACKEND_DIR"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -q -r ../scripts/requirements.txt
pip install -q pytest pytest-asyncio pytest-cov httpx

echo "Running pytest with coverage..."
python -m pytest --cov=api --cov=shared --cov-report=html:"$REPORTS_DIR/backend/htmlcov" --cov-report=xml:"$REPORTS_DIR/backend/coverage.xml" --cov-report=json:"$REPORTS_DIR/backend/coverage.json" 2>&1 | tee "$REPORTS_DIR/backend/test-output.log"

echo -e "${GREEN}✓ Backend coverage report generated${NC}"

deactivate

# ============================================
# E2E TESTS
# ============================================
echo ""
echo -e "${YELLOW}[3/3] Running E2E Tests...${NC}"
cd "$FRONTEND_DIR"

echo "Installing Playwright browsers..."
npx playwright install chromium --with-deps

echo "Running Playwright tests..."
npx playwright test --reporter=html --output="$REPORTS_DIR/e2e" 2>&1 | tee "$REPORTS_DIR/e2e/test-output.log"

# Copy Playwright report
if [ -d "playwright-report" ]; then
    cp -r playwright-report/* "$REPORTS_DIR/e2e/"
    echo -e "${GREEN}✓ E2E test report generated${NC}"
fi

# ============================================
# GENERATE SUMMARY REPORT
# ============================================
echo ""
echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}Generating Summary Report...${NC}"
echo -e "${BLUE}======================================${NC}"

SUMMARY_FILE="$REPORTS_DIR/SUMMARY.md"

cat > "$SUMMARY_FILE" << EOF
# TikTrend Finder - Test Coverage Summary

**Generated:** $(date)

## Overview

| Suite | Status | Coverage |
|-------|--------|----------|
| Frontend (Vitest) | $(grep -q "FAIL" "$REPORTS_DIR/frontend/test-output.log" 2>/dev/null && echo "❌ Failed" || echo "✅ Passed") | See frontend/index.html |
| Backend (pytest) | $(grep -q "FAILED" "$REPORTS_DIR/backend/test-output.log" 2>/dev/null && echo "❌ Failed" || echo "✅ Passed") | See backend/htmlcov/index.html |
| E2E (Playwright) | $(grep -q "failed" "$REPORTS_DIR/e2e/test-output.log" 2>/dev/null && echo "❌ Failed" || echo "✅ Passed") | See e2e/index.html |

## Reports Location

- **Frontend Coverage:** \`test-reports/frontend/index.html\`
- **Backend Coverage:** \`test-reports/backend/htmlcov/index.html\`
- **E2E Report:** \`test-reports/e2e/index.html\`

## Test Categories

### Frontend Unit Tests
- Stores: userStore, productsStore, searchStore, favoritesStore
- Components: Layout, Header, Sidebar, ThemeProvider, ProductCard
- Hooks: useToast
- Utils: cn, formatCurrency, formatNumber, debounce, etc.

### Backend Unit Tests
- Services: auth, cache, license, mercadopago, openai, scraper
- Middleware: auth, quota, ratelimit
- Routes: auth, copy, license, products, webhooks

### E2E Tests
- Authentication Flow
- Search and Filtering
- Favorites Management
- Copy Generation
- Subscription Management
- Dashboard Navigation
- Settings Configuration
- Profile Management
- Accessibility (WCAG)
- Performance (Core Web Vitals)

## Target Coverage: 90%+

EOF

echo -e "${GREEN}✓ Summary report generated: $SUMMARY_FILE${NC}"

# ============================================
# FINAL OUTPUT
# ============================================
echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo -e "Reports available at: ${BLUE}$REPORTS_DIR${NC}"
echo ""
echo "Open reports:"
echo "  - Frontend: $REPORTS_DIR/frontend/index.html"
echo "  - Backend:  $REPORTS_DIR/backend/htmlcov/index.html"  
echo "  - E2E:      $REPORTS_DIR/e2e/index.html"
echo "  - Summary:  $REPORTS_DIR/SUMMARY.md"
echo ""
