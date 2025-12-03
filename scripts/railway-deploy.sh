#!/bin/bash
# ============================================================================
# Railway Deployment Helper - Didin Fácil / TikTrend
# ============================================================================
# Usage: ./scripts/railway-deploy.sh
# ============================================================================

set -e

echo "🚀 Didin Fácil - Railway Deployment Helper"
echo "==========================================="

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

echo ""
echo "📋 Deployment Checklist:"
echo "========================"
echo ""
echo "1. Create a new project in Railway Dashboard"
echo "   https://railway.app/dashboard"
echo ""
echo "2. Add PostgreSQL plugin:"
echo "   - Click '+ New' → 'Database' → 'Add PostgreSQL'"
echo ""
echo "3. Add Redis plugin:"
echo "   - Click '+ New' → 'Database' → 'Add Redis'"
echo ""
echo "4. Link this repository:"
echo "   - Click '+ New' → 'GitHub Repo' → Select 'didin-facil'"
echo ""
echo "5. Configure environment variables:"
echo "   - Go to your service → 'Variables'"
echo "   - Add these required variables:"
echo "     • JWT_SECRET_KEY (generate secure key)"
echo "     • ENVIRONMENT=production"
echo "     • CORS_ORIGINS=https://your-frontend-url"
echo "     • OPENAI_API_KEY (if using AI features)"
echo "     • MERCADOPAGO_ACCESS_TOKEN (if using payments)"
echo ""
echo "6. DATABASE_URL and REDIS_URL are auto-configured!"
echo ""

read -p "Have you completed steps 1-5? (y/n): " CONFIRM

if [ "$CONFIRM" = "y" ]; then
    echo ""
    echo "🔗 Linking to Railway project..."
    railway link
    
    echo ""
    echo "🚀 Deploying to Railway..."
    railway up
    
    echo ""
    echo "✅ Deployment initiated!"
    echo ""
    echo "📊 Check status at: https://railway.app/dashboard"
    echo "📝 View logs with: railway logs"
else
    echo ""
    echo "Please complete the setup steps first."
    echo "Documentation: https://docs.railway.app"
fi
