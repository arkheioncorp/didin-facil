#!/usr/bin/env python3
"""
Live Test Script for Credits Purchase Flow
Tests the real API endpoints with MercadoPago sandbox

Usage:
    cd backend
    python scripts/test_live_purchase.py
"""

import asyncio
import httpx
import json
from datetime import datetime

API_BASE = "http://localhost:8001"


async def test_get_packages():
    """Test GET /credits/packages endpoint"""
    print("\n" + "="*60)
    print("📦 TEST 1: Obtendo pacotes de créditos disponíveis")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE}/credits/packages")
            
            if response.status_code == 200:
                packages = response.json()
                print(f"✅ Sucesso! {len(packages)} pacotes encontrados:\n")
                
                for pkg in packages:
                    badge = f" [{pkg.get('badge')}]" if pkg.get('badge') else ""
                    featured = " ⭐" if pkg.get('is_featured') else ""
                    print(f"  • {pkg['name']}{badge}{featured}")
                    print(f"    - Créditos: {pkg['credits']}")
                    print(f"    - Preço: R$ {pkg['price']:.2f}")
                    print(f"    - Preço/crédito: R$ {pkg['price_per_credit']:.2f}")
                    if pkg.get('discount_percent'):
                        print(f"    - Desconto: {pkg['discount_percent']}%")
                    print()
                
                return packages
            else:
                print(f"❌ Erro: {response.status_code}")
                print(response.text)
                return None
                
        except httpx.ConnectError:
            print("❌ API não está rodando. Inicie com: cd backend && uvicorn api.main:app --port 8001")
            return None


async def test_purchase_pix(package_slug: str = "pro"):
    """Test POST /credits/purchase with PIX"""
    print("\n" + "="*60)
    print(f"💳 TEST 2: Iniciando compra PIX do pacote '{package_slug}'")
    print("="*60)
    
    # Note: This requires authentication
    # For now, we'll just test if the endpoint exists
    
    payload = {
        "package_slug": package_slug,
        "payment_method": "pix",
        "cpf": "12345678900",
        "name": "Usuário Teste",
        "email": "teste@example.com"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE}/credits/purchase",
                json=payload
            )
            
            if response.status_code == 401:
                print("⚠️  Endpoint requer autenticação (esperado)")
                print("   Para testar com auth, use o frontend ou crie um token JWT")
                return None
            elif response.status_code == 200:
                data = response.json()
                print("✅ Pagamento PIX criado com sucesso!")
                print(f"\n  Order ID: {data.get('order_id')}")
                print(f"  Valor: R$ {data.get('amount'):.2f}")
                print(f"  Créditos: {data.get('credits')}")
                print(f"  Status: {data.get('status')}")
                
                if data.get('pix_copy_paste'):
                    print(f"\n  📱 Código PIX Copia e Cola:")
                    print(f"     {data['pix_copy_paste'][:50]}...")
                
                return data
            else:
                print(f"❌ Erro: {response.status_code}")
                print(response.text)
                return None
                
        except httpx.ConnectError:
            print("❌ API não está rodando")
            return None


async def test_mercadopago_connection():
    """Test MercadoPago API connection"""
    print("\n" + "="*60)
    print("🔗 TEST 3: Verificando conexão com MercadoPago")
    print("="*60)
    
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from shared.config import settings
        
        token = settings.MERCADO_PAGO_ACCESS_TOKEN or settings.MERCADOPAGO_ACCESS_TOKEN
        
        if not token:
            print("❌ Token MercadoPago não configurado")
            print("   Configure MERCADOPAGO_ACCESS_TOKEN no .env")
            return False
        
        print(f"✅ Token encontrado: {token[:20]}...")
        
        # Test API connection
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.mercadopago.com/users/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                user = response.json()
                print(f"✅ Conexão OK!")
                print(f"   Usuário: {user.get('first_name')} {user.get('last_name')}")
                print(f"   Email: {user.get('email')}")
                print(f"   País: {user.get('site_id')}")
                return True
            else:
                print(f"❌ Erro na API: {response.status_code}")
                print(response.text)
                return False
                
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


async def test_database_packages():
    """Check packages in database"""
    print("\n" + "="*60)
    print("🗄️  TEST 4: Verificando pacotes no banco de dados")
    print("="*60)
    
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from api.database.connection import database
        
        await database.connect()
        
        query = """
            SELECT name, slug, credits, price_brl, discount_percent, is_active, badge
            FROM credit_packages
            WHERE is_active = true
            ORDER BY sort_order
        """
        
        rows = await database.fetch_all(query)
        
        if rows:
            print(f"✅ {len(rows)} pacotes ativos encontrados:\n")
            for row in rows:
                print(f"  • {row['name']} ({row['slug']})")
                print(f"    - Créditos: {row['credits']}")
                print(f"    - Preço: R$ {float(row['price_brl']):.2f}")
                print(f"    - Desconto: {row['discount_percent']}%")
                print(f"    - Badge: {row['badge'] or 'N/A'}")
                print()
        else:
            print("⚠️  Nenhum pacote ativo encontrado")
            print("   Execute: python scripts/update_credit_packages.py")
        
        await database.disconnect()
        return bool(rows)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


async def test_operation_costs():
    """Check operation costs in database"""
    print("\n" + "="*60)
    print("💰 TEST 5: Verificando custos de operação")
    print("="*60)
    
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    try:
        from api.database.connection import database
        
        await database.connect()
        
        query = """
            SELECT operation_type, credits_charged, base_cost_brl
            FROM operation_costs
            ORDER BY credits_charged
        """
        
        rows = await database.fetch_all(query)
        
        if rows:
            print(f"✅ {len(rows)} operações configuradas:\n")
            for row in rows:
                op_name = row['operation_type'].replace('_', ' ').title()
                print(f"  • {op_name}")
                print(f"    - Créditos: {row['credits_charged']}")
                print(f"    - Custo base: R$ {float(row['base_cost_brl']):.4f}")
                print()
        else:
            print("⚠️  Nenhum custo configurado")
            print("   Execute: python scripts/init_operation_costs.py")
        
        await database.disconnect()
        return bool(rows)
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False


async def main():
    """Run all tests"""
    print("\n" + "🧪 "*20)
    print("\n  TESTE COMPLETO DO FLUXO DE CRÉDITOS - DIDIN FÁCIL")
    print(f"  {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print("\n" + "🧪 "*20)
    
    results = {}
    
    # Test 1: API Packages
    packages = await test_get_packages()
    results['packages_api'] = packages is not None
    
    # Test 2: Purchase (requires auth)
    await test_purchase_pix()
    
    # Test 3: MercadoPago Connection
    results['mercadopago'] = await test_mercadopago_connection()
    
    # Test 4: Database Packages
    results['db_packages'] = await test_database_packages()
    
    # Test 5: Operation Costs
    results['operation_costs'] = await test_operation_costs()
    
    # Summary
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    all_passed = True
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 Todos os testes passaram! O sistema está pronto.")
    else:
        print("⚠️  Alguns testes falharam. Verifique as configurações.")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
